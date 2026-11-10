"""District rankings by night-time light, 1992-2025, and how much districts move.

Professor Khan's question: have Pakistan's districts been stuck in one ranking, or have some improved
their economies? Three rankings are built for every year:
  (i)   all districts of the four provinces plus Islamabad (Karachi's seven districts as one unit)
  (ii)  excluding Islamabad, Lahore, Peshawar, Quetta and Karachi
  (iii) excluding those five and every district whose polygon touches one of them
Each ranking is computed for three measures of light and both source series:
  size      sum of lights (radiance x km2; series B rad_sum_km2, series A dn_sum_km2)
  density   light per km2 of the district (rad_per_km2 / dn_per_km2)
  percap    light per 1,000 people, in census years only (1998, 2017, 2023)
Rank 1 = brightest. Mobility is summarised by Spearman rank correlations with the 1992 ranking,
quintile transition matrices, and lists of climbers and fallers, within sensor eras as well as
end to end (both series break at the DMSP to VIIRS change; see docs/VALIDATION.md).
Outputs: output/rankings/*.csv, output/figures/*.png, and the numbers quoted in docs/RANKINGS.md.
"""
import os, json, numpy as np, pandas as pd, geopandas as gpd
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
HERE=os.path.dirname(os.path.abspath(__file__)); OUT=os.path.join(HERE,'..','output'); RK=os.path.join(OUT,'rankings'); FG=os.path.join(OUT,'figures')
os.makedirs(RK,exist_ok=True); os.makedirs(FG,exist_ok=True)
P=pd.read_csv(os.path.join(OUT,'panel_ntl_census_district_2023frame.csv'))
G=gpd.read_file(os.path.join(OUT,'boundaries_district_2023.gpkg'))
KEEP_PROV={'PUNJAB','SINDH','KHYBER PAKHTUNKHWA','BALOCHISTAN','ISLAMABAD CAPITAL TERRITORY'}
KARACHI={'KARACHI EAST DISTRICT','KARACHI WEST DISTRICT','KARACHI CENTRAL DISTRICT','KARACHI SOUTH DISTRICT','MALIR DISTRICT','KORANGI DISTRICT','KEAMARI DISTRICT'}
BIG={'ISLAMABAD DISTRICT','LAHORE DISTRICT','PESHAWAR DISTRICT','QUETTA DISTRICT','KARACHI'}
ISB_POP={1998:805235,2017:2003368,2023:2363863}   # PBS Table 1 district rows for Islamabad (2017 table: 2017 count and restated 1998; 2023 table: 2023 count), as in project 02 output/unit_master_2017_all.csv and unit_master_2023_all.csv; Islamabad is outside the crosswalk so it is added here
# ---- unit frame: merge Karachi, add Islamabad populations
P=P[P.province_2023.isin(KEEP_PROV)].copy()
P['unit']=np.where(P.district_2023.isin(KARACHI),'KARACHI',P.district_2023)
agg={c:'sum' for c in ['area_km2','pixel_area_km2','rad_sum','rad_sum_km2','dn_sum','dn_sum_km2','rad_sum_gt1_km2','dn_sum_gt7_km2','pop_1998','pop_2017','pop_2023']}
U=P.groupby(['unit','province_2023','year'],as_index=False).agg(agg)
U['rad_per_km2']=U.rad_sum_km2/U.pixel_area_km2; U['dn_per_km2']=U.dn_sum_km2/U.pixel_area_km2
for y,v in ISB_POP.items(): U.loc[(U.unit=='ISLAMABAD DISTRICT'),f'pop_{y}']=v
U['pop_census']=np.nan
for y in (1998,2017,2023): U.loc[U.year==y,'pop_census']=U.loc[U.year==y,f'pop_{y}']
U['rad_percap']=U.rad_sum_km2/(U.pop_census/1000); U['dn_percap']=U.dn_sum_km2/(U.pop_census/1000)
# ---- adjacency to the five big cities from the polygons
G=G[G.province.isin(KEEP_PROV)].to_crs(32642); G['unit']=np.where(G.name.isin(KARACHI),'KARACHI',G.name)
GU=G.dissolve(by='unit').reset_index()
GU['geometry']=GU.geometry.buffer(0)
adj=set()
for _,b in GU[GU.unit.isin(BIG)].iterrows():
    for _,o in GU.iterrows():
        if o.unit not in BIG and b.geometry.buffer(50).intersects(o.geometry): adj.add(o.unit)
pd.DataFrame(sorted(adj),columns=['district_adjacent_to_big_five']).to_csv(os.path.join(RK,'adjacent_to_big_cities.csv'),index=False)
VARIANTS={'i_all':set(),'ii_no_big5':BIG,'iii_no_big5_or_adjacent':BIG|adj}
MEASURES={'B':{'size':'rad_sum_km2','density':'rad_per_km2','percap':'rad_percap'},'A':{'size':'dn_sum_km2','density':'dn_per_km2','percap':'dn_percap'}}
# ---- rankings
rows=[]
for ser,ms in MEASURES.items():
    for mname,col in ms.items():
        for vname,excl in VARIANTS.items():
            S=U[~U.unit.isin(excl)&U[col].notna()]
            if ser=='A': S=S[S.year<=2024]
            for y,g in S.groupby('year'):
                g=g.copy(); g['rank']=g[col].rank(ascending=False,method='min').astype(int); g['n']=len(g); g['percentile']=1-(g['rank']-1)/(len(g)-1)
                for _,r in g.iterrows(): rows.append(dict(series=ser,measure=mname,variant=vname,year=y,unit=r.unit,province=r.province_2023,value=r[col],rank=r['rank'],n_units=r.n,percentile=round(r.percentile,4)))
R=pd.DataFrame(rows); R.to_csv(os.path.join(RK,'rankings_district_long.csv'),index=False)
for ser in MEASURES:
    for mname in MEASURES[ser]:
        w=R[(R.series==ser)&(R.measure==mname)].pivot_table(index=['variant','unit','province'],columns='year',values='rank').reset_index()
        w.to_csv(os.path.join(RK,f'ranks_wide_{ser}_{mname}.csv'),index=False)
# ---- mobility summaries
def spearman(a,b):
    m=pd.concat([a,b],axis=1).dropna(); return float(m.corr(method='spearman').iloc[0,1]) if len(m)>2 else np.nan
summ=[]; climb=[]
# era end points are kept away from the DMSP to VIIRS transition (2011-2016 are the noisiest years in both series)
ERAS={'B':[(1992,2010,'DMSP era'),(2017,2025,'VIIRS era'),(1992,2025,'end to end')],'A':[(1992,2010,'DMSP era'),(2017,2024,'VIIRS era'),(1992,2024,'end to end')]}
for ser in MEASURES:
    for mname in MEASURES[ser]:
        for vname in VARIANTS:
            S=R[(R.series==ser)&(R.measure==mname)&(R.variant==vname)]
            if S.empty: continue
            W=S.pivot(index='unit',columns='year',values='rank')
            yrs=sorted(W.columns); base=yrs[0]
            for y in yrs: summ.append(dict(series=ser,measure=mname,variant=vname,year=y,n_units=int(W[y].notna().sum()),spearman_vs_first_year=round(spearman(W[base],W[y]),3),spearman_vs_previous=round(spearman(W[yrs[yrs.index(y)-1]],W[y]),3) if y!=base else np.nan))
            for (y0,y1,label) in ERAS[ser]:
                if y0 not in W.columns or y1 not in W.columns: continue
                n=W[y1].notna().sum(); ch=(W[y0]-W[y1]).dropna()   # positive = climbed
                q0=pd.qcut(W[y0].rank(method='first'),5,labels=[1,2,3,4,5]); q1=pd.qcut(W[y1].rank(method='first'),5,labels=[1,2,3,4,5])
                T=pd.crosstab(q0,q1); T.to_csv(os.path.join(RK,f'transition_quintiles_{ser}_{mname}_{vname}_{y0}_{y1}.csv'))
                stay=float(np.trace(T.values)/T.values.sum())
                for u,c in ch.sort_values(ascending=False).items():
                    climb.append(dict(series=ser,measure=mname,variant=vname,period=label,year_from=y0,year_to=y1,unit=u,province=S[S.unit==u].province.iloc[0],rank_from=int(W.loc[u,y0]),rank_to=int(W.loc[u,y1]),places_climbed=int(c),n_units=int(n),quintile_from=int(q0[u]),quintile_to=int(q1[u])))
                summ.append(dict(series=ser,measure=mname,variant=vname,year=f'{y0}-{y1} ({label})',n_units=int(n),spearman_vs_first_year=round(spearman(W[y0],W[y1]),3),share_same_quintile=round(stay,3),mean_abs_rank_change=round(float(ch.abs().mean()),2),share_moved_10_or_more=round(float((ch.abs()>=10).mean()),3),climbers_20_or_more=int((ch>=20).sum()),fallers_20_or_more=int((ch<=-20).sum())))
pd.DataFrame(summ).to_csv(os.path.join(RK,'mobility_summary.csv'),index=False)
CL=pd.DataFrame(climb); CL.to_csv(os.path.join(RK,'rank_changes_by_period.csv'),index=False)
# ---- robustness: ranks on three-year window means (1992-94 vs 2023-25 in B; 1992-94 vs 2022-24 in A) to damp single-year noise
win=[]
for ser,ms in MEASURES.items():
    y_end=2025 if ser=='B' else 2024
    for mname,col in ms.items():
        if mname=='percap': continue
        for vname,excl in VARIANTS.items():
            S=U[~U.unit.isin(excl)]
            a=S[S.year.between(1992,1994)].groupby('unit')[col].mean(); b=S[S.year.between(y_end-2,y_end)].groupby('unit')[col].mean()
            ra=a.rank(ascending=False,method='min'); rb=b.rank(ascending=False,method='min')
            for u in ra.index: win.append(dict(series=ser,measure=mname,variant=vname,unit=u,rank_1992_94=int(ra[u]),rank_end_window=int(rb[u]),places_climbed=int(ra[u]-rb[u]),n_units=len(ra),spearman=round(spearman(ra,rb),3)))
WIN=pd.DataFrame(win); WIN.to_csv(os.path.join(RK,'rank_changes_three_year_windows.csv'),index=False)
# ---- figures (series B size and density, variant i and iii) ------------------------------------
BLUE='#2a78d6'; ORANGE='#eb6834'; AQUA='#1baf7a'; GREY='#8a8a86'; INK='#1a1a19'
plt.rcParams.update({'font.size':9,'axes.spines.top':False,'axes.spines.right':False,'axes.edgecolor':'#c8c8c4','axes.labelcolor':INK,'xtick.color':'#555','ytick.color':'#555','axes.grid':True,'grid.color':'#eeeeec','grid.linewidth':0.6})
def nice(u): return u.replace(' DISTRICT','').title()
def spread(ys,gap):
    """push label y positions apart so none are closer than gap (keeps order)"""
    order=np.argsort(ys); out=np.array(ys,dtype=float)
    for k in range(1,len(order)):
        a,b=order[k-1],order[k]
        if out[b]-out[a]<gap: out[b]=out[a]+gap
    return out
def label_lines(ax,W,units,colors,xlast,gap=2.4):
    ys=[W.loc[u,xlast] for u in units]; ys2=spread(ys,gap)
    for u,col,y0,y1 in zip(units,colors,ys,ys2):
        ax.plot([xlast,xlast+0.6],[y0,y1],color='#c8c8c4',lw=0.6,zorder=2)
        ax.text(xlast+0.8,y1,f'{nice(u)}  ({int(W.loc[u,W.columns.min()])}\u2192{int(W.loc[u,xlast])})',color=col if col!=GREY else GREY,fontsize=7.5,va='center')
# Figure 1: stability of the ranking over time, Spearman vs 1992, by variant (series B, size)
fig,ax=plt.subplots(figsize=(8,4.2),dpi=200)
for (vname,label,color) in [('i_all','(i) all districts',BLUE),('ii_no_big5','(ii) without the five big cities',ORANGE),('iii_no_big5_or_adjacent','(iii) also without their neighbours',AQUA)]:
    s=pd.DataFrame(summ); s=s[(s.series=='B')&(s.measure=='size')&(s.variant==vname)&s.year.apply(lambda x:isinstance(x,(int,np.integer)))]
    ax.plot(s.year.astype(int),s.spearman_vs_first_year,color=color,lw=2,label=label); ax.text(s.year.astype(int).iloc[-1]+0.3,s.spearman_vs_first_year.iloc[-1],label,color=INK,va='center',fontsize=8)
ax.axvspan(2012.5,2016.5,color='#f3f3f0',zorder=0); ax.text(2014.5,ax.get_ylim()[0]+0.01,'sensor\nchange',ha='center',fontsize=7,color=GREY)
ax.set_xlim(1992,2033); ax.set_ylim(0.5,1.0); ax.set_xticks(range(1992,2026,3)); ax.set_ylabel('Spearman rank correlation with 1992'); ax.set_title('How much the district ranking by sum of lights has changed since 1992 (series B)',loc='left',fontsize=10)
ax.grid(axis='x',visible=False); fig.tight_layout(); fig.savefig(os.path.join(FG,'fig1_rank_stability_spearman.png')); plt.close(fig)
# Figure 2: quintile transition heatmap 1992 -> 2025, variant iii, series B size
T=pd.read_csv(os.path.join(RK,'transition_quintiles_B_size_iii_no_big5_or_adjacent_1992_2025.csv'),index_col=0)
Tn=T.div(T.sum(axis=1),axis=0)
fig,ax=plt.subplots(figsize=(5.2,4.6),dpi=200)
im=ax.imshow(Tn.values,cmap=matplotlib.colors.LinearSegmentedColormap.from_list('b',['#ffffff','#cde2fb','#5598e7','#1c5cab','#0d366b']),vmin=0,vmax=1)
for i in range(5):
    for j in range(5): ax.text(j,i,f'{T.values[i,j]}',ha='center',va='center',color='white' if Tn.values[i,j]>0.55 else INK,fontsize=9)
ax.set_xticks(range(5)); ax.set_yticks(range(5)); ax.set_xticklabels(['Q1\nbrightest','Q2','Q3','Q4','Q5\ndarkest']); ax.set_yticklabels(['Q1','Q2','Q3','Q4','Q5'])
ax.set_xlabel('Quintile in 2025'); ax.set_ylabel('Quintile in 1992'); ax.grid(False); ax.set_title('Where districts of each 1992 quintile ended up in 2025\n(sum of lights, series B, ranking iii; cell = number of districts)',loc='left',fontsize=9)
fig.tight_layout(); fig.savefig(os.path.join(FG,'fig2_quintile_transitions_1992_2025.png')); plt.close(fig)
# Figure 3: rank paths of the biggest climbers (variant iii, series B size, end to end), with the big fallers greyed
S=R[(R.series=='B')&(R.measure=='size')&(R.variant=='iii_no_big5_or_adjacent')]; W=S.pivot(index='unit',columns='year',values='rank')
c=CL[(CL.series=='B')&(CL.measure=='size')&(CL.variant=='iii_no_big5_or_adjacent')&(CL.period=='end to end')].sort_values('places_climbed',ascending=False)
top=c.head(8).unit.tolist(); bottom=c.tail(4).unit.tolist()
fig,ax=plt.subplots(figsize=(9,5.2),dpi=200)
for u in W.index: ax.plot(W.columns,W.loc[u],color='#e4e4e0',lw=0.6,zorder=1)
cols=[BLUE,ORANGE,AQUA,'#eda100','#e87ba4','#008300','#7c4dff','#8d6e63']
for u,col in zip(top,cols): ax.plot(W.columns,W.loc[u],color=col,lw=2,zorder=3)
for u in bottom: ax.plot(W.columns,W.loc[u],color=GREY,lw=1.4,ls='--',zorder=2)
label_lines(ax,W,top+bottom,[INK]*len(top)+[GREY]*len(bottom),2025)
ax.invert_yaxis(); ax.set_xlim(1992,2034); ax.set_xticks(range(1992,2026,3)); ax.set_ylabel('rank (1 = brightest)'); ax.set_title(f'The eight biggest climbers 1992 to 2025 and the four biggest fallers (dashed), among {int(W[2025].notna().sum())} districts\nsum of lights, series B, ranking iii (five big cities and their neighbours excluded)',loc='left',fontsize=9)
ax.axvspan(2012.5,2016.5,color='#f3f3f0',zorder=0); ax.text(2014.5,ax.get_ylim()[0]-1,'sensor change',ha='center',fontsize=7,color=GREY); ax.grid(axis='x',visible=False); fig.tight_layout(); fig.savefig(os.path.join(FG,'fig3_biggest_climbers_rank_paths.png')); plt.close(fig)
# Figure 4: rank 1992 vs 2025 scatter, variant iii, series B size, labelled movers
fig,ax=plt.subplots(figsize=(6.4,6.2),dpi=200)
x=W[1992]; y=W[2025]; n=len(W)
ax.plot([1,n],[1,n],color='#c8c8c4',lw=1,zorder=1)
ax.scatter(x,y,s=18,color=BLUE,alpha=0.85,edgecolor='white',linewidth=0.5,zorder=3)
for u in top+bottom: ax.annotate(nice(u),(x[u],y[u]),xytext=(4,-3),textcoords='offset points',fontsize=7,color=INK)
ax.set_xlabel('rank in 1992 (1 = brightest)'); ax.set_ylabel('rank in 2025'); ax.set_title('Rank in 2025 against rank in 1992, sum of lights, series B, ranking iii\n(below the line = climbed)',loc='left',fontsize=9)
ax.invert_xaxis(); ax.invert_yaxis(); fig.tight_layout(); fig.savefig(os.path.join(FG,'fig4_rank_1992_vs_2025_scatter.png')); plt.close(fig)
# Figure 5: same as fig 3 for light density (per km2), variant iii
S=R[(R.series=='B')&(R.measure=='density')&(R.variant=='iii_no_big5_or_adjacent')]; W2=S.pivot(index='unit',columns='year',values='rank')
c2=CL[(CL.series=='B')&(CL.measure=='density')&(CL.variant=='iii_no_big5_or_adjacent')&(CL.period=='end to end')].sort_values('places_climbed',ascending=False)
top2=c2.head(8).unit.tolist()
fig,ax=plt.subplots(figsize=(9,5.2),dpi=200)
for u in W2.index: ax.plot(W2.columns,W2.loc[u],color='#e4e4e0',lw=0.6,zorder=1)
for u,col in zip(top2,cols): ax.plot(W2.columns,W2.loc[u],color=col,lw=2,zorder=3)
label_lines(ax,W2,top2,[INK]*len(top2),2025)
ax.invert_yaxis(); ax.set_xlim(1992,2034); ax.set_xticks(range(1992,2026,3)); ax.set_ylabel('rank (1 = brightest per km2)'); ax.set_title('The eight biggest climbers 1992 to 2025 by light per km2, series B, ranking iii',loc='left',fontsize=9)
ax.axvspan(2012.5,2016.5,color='#f3f3f0',zorder=0); ax.grid(axis='x',visible=False); fig.tight_layout(); fig.savefig(os.path.join(FG,'fig5_biggest_climbers_density.png')); plt.close(fig)
# ---- headline numbers for the write-up
summdf=pd.DataFrame(summ); key={}
for ser in ['B','A']:
    for mname in ['size','density']:
        for vname in VARIANTS:
            s=summdf[(summdf.series==ser)&(summdf.measure==mname)&(summdf.variant==vname)&summdf.year.astype(str).str.contains('end to end')]
            if len(s): key[f'{ser}_{mname}_{vname}']=s.iloc[0].to_dict()
agree=spearman(R[(R.series=='B')&(R.measure=='size')&(R.variant=='i_all')&(R.year==2023)].set_index('unit')['rank'],R[(R.series=='A')&(R.measure=='size')&(R.variant=='i_all')&(R.year==2023)].set_index('unit')['rank'])
key['series_agreement_2023_size_all']=round(agree,3); key['window_spearman']={f'{r.series}_{r.measure}_{r.variant}':r.spearman for _,r in WIN.drop_duplicates(['series','measure','variant']).iterrows()}; key['window_top_climbers_B_size_iii']=WIN[(WIN.series=='B')&(WIN.measure=='size')&(WIN.variant=='iii_no_big5_or_adjacent')].sort_values('places_climbed',ascending=False).head(10)[['unit','rank_1992_94','rank_end_window','places_climbed']].values.tolist(); key['adjacent_to_big_five']=sorted(adj); key['n_units']={v:int(R[(R.series=='B')&(R.measure=='size')&(R.variant==v)&(R.year==2025)].n_units.iloc[0]) for v in VARIANTS}
json.dump(key,open(os.path.join(RK,'headline_numbers.json'),'w'),indent=1,default=str)
print(json.dumps({k:v for k,v in key.items() if not k.startswith('A_')},indent=1,default=str)[:4000])
print(c.head(12)[['unit','province','rank_from','rank_to','places_climbed']].to_string(index=False)); print(c.tail(6)[['unit','province','rank_from','rank_to','places_climbed']].to_string(index=False))
