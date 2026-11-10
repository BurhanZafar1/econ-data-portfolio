"""Generic resolver: move units of an old census frame onto a new frame using the new frame's
restated old-year populations (PBS prints the earlier census count on the newer units).

For each district group (a connected set of old and new districts whose populations balance),
find integer flows F[i,j] >= 0 with row sums = old-unit populations and column sums = new-unit
restated populations, opening as few "unexpected" cells as possible:

    minimise  sum_ij w_ij * y_ij  (+ a tiny term on the flows to break ties)
    subject to  sum_j F_ij = P_i,  sum_i F_ij = Q_j,  F_ij <= min(P_i,Q_j) * y_ij,  y binary

with w_ij small for same-name pairs, and otherwise rising with distance between the new unit and
the polygon of the old unit's namesake (adjacency prior). This is a fixed-charge transportation
problem, solved exactly with scipy's MILP (HiGHS). Uniqueness of the support is then checked by
forbidding each opened non-name cell in turn and re-solving: if an equally cheap alternative
exists, the rows in that cell are marked medium confidence.
"""
import pandas as pd, numpy as np, re, difflib
from scipy.optimize import milp, LinearConstraint, Bounds
import time
TIME_LIMIT=60
TIER=['SUB-DIVISION','SUB DIVISION','SUB-TEHSIL','SUB TEHSIL','SUBTEHSIL','TEHSIL','TALUKA','F.R.','F.R','SUB-','DISTRICT','AGENCY','TOWN','CANTT.','CANTT','TRIBAL AREA ADJOINING','TRIBAL AREA ADJ.','TRIBAL AREA ADJ']
def base(n):
    n=str(n).upper()
    for w in TIER: n=n.replace(w,' ')
    n=re.sub(r'\(.*?\)',' ',n); n=re.sub(r'[^A-Z0-9]+',' ',n).strip()
    return n
def namematch(a,b):
    A,B=base(a),base(b)
    if not A or not B: return False
    sa,sb=set(A.split()),set(B.split())
    if sa<=sb or sb<=sa: return True
    ca,cb=A.replace(' ',''),B.replace(' ','')
    if len(ca)>=4 and len(cb)>=4 and (ca in cb or cb in ca): return True
    r=difflib.SequenceMatcher(None,ca,cb).ratio()
    if r>=0.85: return True
    # spelling variants with a shared stem (BULEDA/BULAIDA, SOBHODHERO/SOBHO DERO)
    k=0
    while k<min(len(ca),len(cb)) and ca[k]==cb[k]: k+=1
    return k>=3 and r>=0.7

def _solve(P,Q,W,forbid=None,fixed=None,block_eq=None,allowed=None):
    """Fixed-charge transportation MILP on the allowed cells only.
    fixed: {(i,j): value} cells pinned to a flow (removed from the problem);
    block_eq: list of (cells, total) equality constraints; allowed: boolean mask of candidate cells."""
    m,n=W.shape
    fixed=fixed or {}
    Pr=P.astype(float).copy(); Qr=Q.astype(float).copy()
    for (i,j),v in fixed.items(): Pr[i]-=v; Qr[j]-=v
    cand=np.ones((m,n),bool) if allowed is None else allowed.copy()
    for (i,j) in fixed: cand[i,j]=False
    if forbid is not None:
        for (i,j) in forbid: cand[i,j]=False
    # rows/cols already satisfied by pins need no cells
    for i in range(m):
        if Pr[i]==0: cand[i,:]=False
    for j in range(n):
        if Qr[j]==0: cand[:,j]=False
    cells=[(i,j) for i in range(m) for j in range(n) if cand[i,j]]
    K=len(cells); F=np.zeros((m,n),np.int64)
    for (i,j),v in fixed.items(): F[i,j]=v
    if K==0:
        if (Pr==0).all() and (Qr==0).all(): return F,float(np.sum(W*(F>0)))
        return None,None
    U=np.array([min(Pr[i],Qr[j]) for i,j in cells])
    if (U<=0).any(): return None,None
    idx={c:k for k,c in enumerate(cells)}
    from scipy.sparse import lil_matrix
    rows=[];lo=[];hi=[]
    def addrow(coefs,l,h): rows.append(coefs); lo.append(l); hi.append(h)
    for i in range(m):
        ks=[idx[(i,j)] for j in range(n) if (i,j) in idx]
        if ks: addrow({k:1.0 for k in ks},Pr[i],Pr[i])
        elif Pr[i]!=0: return None,None
    for j in range(n):
        ks=[idx[(i,j)] for i in range(m) if (i,j) in idx]
        if ks: addrow({k:1.0 for k in ks},Qr[j],Qr[j])
        elif Qr[j]!=0: return None,None
    for k in range(K): addrow({k:1.0,K+k:-U[k]},-np.inf,0.0)
    for cs,total in (block_eq or []):
        pinned=sum(fixed.get(c,0) for c in cs)
        ks=[idx[c] for c in cs if c in idx]
        if ks: addrow({k:1.0 for k in ks},total-pinned,total-pinned)
        elif total-pinned!=0: return None,None
    A=lil_matrix((len(rows),2*K))
    for r,coefs in enumerate(rows):
        for k,v in coefs.items(): A[r,k]=v
    w=np.array([W[c] for c in cells])
    c=np.concatenate([w*1e-9/max(P.sum(),1),w])
    res=milp(c,constraints=LinearConstraint(A.tocsr(),lo,hi),integrality=np.concatenate([np.zeros(K),np.ones(K)]),
             bounds=Bounds(np.zeros(2*K),np.concatenate([U,np.ones(K)])),options={'time_limit':TIME_LIMIT,'disp':False})
    if res.x is None: return None,None
    if not res.success: print(f'   (MILP stopped at time limit, status {res.status}; best feasible solution kept)',flush=True)
    for k,(i,j) in enumerate(cells): F[i,j]=int(round(res.x[k]))
    return F,float(np.sum(W*(F>0)))

def solve_group(old,new,adjacency=None,label='',district_flows=None,pin_equal=True):
    """old: DataFrame[id,name,n(,district)]; new: DataFrame[id,name,n(,district)] (restated); sums must agree.
    district_flows: {(old_district,new_district): persons} imposed as equality constraints on the
    tehsil flows between those districts. pin_equal: a uniquely same-named pair with identical
    population is treated as unchanged (flow pinned to the full population).
    Returns (rows, group_confidence); rows are (old_id,new_id,flow,method,confidence,note)."""
    P=old['n'].values.astype(np.int64); Q=new['n'].values.astype(np.int64); m,n=len(old),len(new)
    assert P.sum()==Q.sum(), (label,P.sum(),Q.sum())
    NM=np.array([[namematch(old.name.iloc[i],new.name.iloc[j]) for j in range(n)] for i in range(m)])
    W=np.full((m,n),2.0)
    for i in range(m):
        anchors=[j for j in range(n) if NM[i,j]]
        for j in range(n):
            if NM[i,j]: W[i,j]=0.1
            elif adjacency is not None and anchors:
                a=max(adjacency(new.id.iloc[k],new.id.iloc[j]) for k in anchors)
                W[i,j]=1+2*(1-a) if a>0 else 4
    block=[]; allowed=W<4
    if district_flows:
        for (do,dn),tot in district_flows.items():
            cells=[(i,j) for i in range(m) for j in range(n) if old.district.iloc[i]==do and new.district.iloc[j]==dn]
            if cells: block.append((cells,tot))
        for i in range(m):
            for j in range(n):
                if (old.district.iloc[i],new.district.iloc[j]) not in district_flows: allowed[i,j]=False
    fixed={}
    if pin_equal:
        for i in range(m):
            for j in range(n):
                if NM[i,j] and P[i]==Q[j] and NM[i].sum()==1 and NM[:,j].sum()==1: fixed[(i,j)]=int(P[i])
        # a name printed more than once (e.g. "Quetta Tehsil (Part)" under two sub-divisions): pin the pair whose
        # populations are identical when that equality singles out one partner on each side
        for i in range(m):
            for j in range(n):
                if NM[i,j] and P[i]==Q[j] and (i,j) not in fixed:
                    if sum(1 for k in range(n) if NM[i,k] and Q[k]==P[i])==1 and sum(1 for k in range(m) if NM[k,j] and P[k]==Q[j])==1: fixed[(i,j)]=int(P[i])
    t0=time.time(); print(f'solving {label}: {m} old x {n} new, {len(fixed)} pinned, {len(block)} district constraints',flush=True)
    F,obj=_solve(P,Q,W,fixed=fixed,block_eq=block,allowed=allowed)
    if F is None:
        allowed=np.ones((m,n),bool); F,obj=_solve(P,Q,W,fixed=fixed,block_eq=block,allowed=allowed); print('   (non-adjacent cells re-admitted)',flush=True)
    if F is None and fixed:
        F,obj=_solve(P,Q,W,block_eq=block,allowed=allowed); fixed={}; print('   (pins dropped)',flush=True)
    if F is None and block:
        F,obj=_solve(P,Q,W,allowed=allowed); block=[]; print('WARNING: district flow constraints infeasible, dropped for',label)
    assert F is not None, label
    assert (F.sum(1)==P).all() and (F.sum(0)==Q).all(), label
    opened=[(i,j) for i in range(m) for j in range(n) if F[i,j]>0]
    # grade every opened cell that is not a same-name pair:
    #   forced     - the group cannot balance without it (re-solve with the cell forbidden is infeasible)   -> high
    #   inferred   - a balancing alternative exists but costs more under the adjacency prior              -> medium
    #   ambiguous  - an equally cheap alternative exists                                                   -> low
    grade={}
    for (i,j) in opened:
        if NM[i,j]: grade[(i,j)]='same_name'; continue
        F2,obj2=_solve(P,Q,W,forbid=[(i,j)],fixed=fixed,block_eq=block,allowed=allowed)
        if F2 is None: grade[(i,j)]='forced'
        elif obj2<=obj+1e-6: grade[(i,j)]='ambiguous'
        else: grade[(i,j)]='inferred'
    ambiguous={c for c,g in grade.items() if g=='ambiguous'}; inferred={c for c,g in grade.items() if g=='inferred'}
    print(f'   done in {time.time()-t0:.1f}s, {len(opened)} cells, {len(inferred)} inferred, {len(ambiguous)} ambiguous',flush=True)
    rows=[]
    outdeg=(F>0).sum(1); indeg=(F>0).sum(0)
    for (i,j) in opened:
        if outdeg[i]==1 and indeg[j]==1: method='one_to_one' if NM[i,j] else 'one_to_one_renamed'
        elif outdeg[i]>1 and indeg[j]==1: method='split'
        elif outdeg[i]==1 and indeg[j]>1: method='merge'
        else: method='split_and_merge'
        g=grade[(i,j)]
        if g=='same_name': note='same name'; conf='high'
        else:
            note=f'{F[i,j]:,} persons (source-year count) of {old.name.iloc[i]} fall in {new.name.iloc[j]} (cell cost {W[i,j]:.2f}); '
            if g=='forced': note+='forced: the group cannot balance without this cell'; conf='high'
            elif g=='inferred': note+='inferred: another balancing allocation exists but is less parsimonious under the adjacency prior'; conf='medium'
            else: note+='ambiguous: an equally parsimonious alternative allocation exists'; conf='low'
        rows.append((old.id.iloc[i],new.id.iloc[j],int(F[i,j]),method,conf,note))
    return rows,('low' if ambiguous else 'medium' if inferred else 'high')

def components(edges):
    """edges: iterable of (old_key,new_key) -> list of (set(old), set(new))"""
    parent={}
    def find(x):
        parent.setdefault(x,x)
        while parent[x]!=x: parent[x]=parent[parent[x]]; x=parent[x]
        return x
    for a,b in edges: parent[find(('o',a))]=find(('n',b))
    comp={}
    for x in list(parent): comp.setdefault(find(x),[]).append(x)
    return [({k for t,k in v if t=='o'},{k for t,k in v if t=='n'}) for v in comp.values()]

RANK={'high':2,'medium':1,'low':0}; INV={2:'high',1:'medium',0:'low'}
def district_confidence(T,a_col,b_col,conf_col='confidence'):
    """Grade of a district-to-district flow, from the tehsil rows that make it up.
    For a pair of different districts: the weakest tehsil row in that pair. For the within-district pair
    (a == b): the weakest tehsil row that leaves district a for another district (what stays is what did not
    leave), high if nothing leaves. Inferred rows between tehsils of the same district do not change any
    district total, so they do not lower the district grade. Returns a function for DataFrame.apply(axis=1)."""
    cross=T[T[a_col]!=T[b_col]]
    def f(r):
        if r[a_col]!=r[b_col]: s=cross[(cross[a_col]==r[a_col])&(cross[b_col]==r[b_col])][conf_col]
        else: s=cross[cross[a_col]==r[a_col]][conf_col]
        return INV[min(RANK[x] for x in s)] if len(s) else 'high'
    return f
