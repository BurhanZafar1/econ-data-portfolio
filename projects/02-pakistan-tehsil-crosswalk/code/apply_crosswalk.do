* apply_crosswalk.do  --  move 2017-frame data to the 2023 census frame (Stata 14+)
*
* Expects:  a dataset with one row per 2017 unit, holding `id2017` (unit_id_2017 for
*           tehsils, district_2017 for districts) and the variables to crosswalk.
* Produces: one row per 2023 unit.
*
* Example:
*   use mydata_2017, clear
*   apply_crosswalk, cw("crosswalk_tehsil_2017_to_2023.csv") id(unit_id_2017) ///
*       counts(schools votes) rates(literacy) weight(pop)
*
* counts: allocated along each crosswalk row by the chosen weight and summed.
* rates : averaged over source units with weights = people moved (pop_weight x pop_2017).
*         Rates whose denominator is not population should be rebuilt from counts instead.
* weight: pop (default) or area.

capture program drop apply_crosswalk
program define apply_crosswalk
    version 14
    syntax , CW(string) ID(string) [COUNTS(varlist) RATES(varlist) WEIGHT(string)]
    if "`weight'" == "" local weight pop
    if !inlist("`weight'", "pop", "area") {
        di as err "weight() must be pop or area"
        exit 198
    }
    tempfile src cwf
    * one row per 2017 unit
    isid `id'
    save `src'
    import delimited using "`cw'", clear varnames(1) case(preserve) encoding(utf8) stringcols(_all)
    destring pop_weight area_weight pop_2017 pop_2017_restated_2023 pop_2023, replace
    capture confirm variable unit_id_2023
    if _rc == 0 local to unit_id_2023
    else local to district_2023
    rename `id' `id'_cw
    gen double w = `weight'_weight
    gen double flow = pop_weight * pop_2017
    gen byte confrank = cond(confidence=="high",2,cond(confidence=="medium",1,0))
    save `cwf'
    use `src', clear
    rename `id' `id'_cw
    merge 1:m `id'_cw using `cwf', keep(match) nogenerate
    foreach v of local counts {
        replace `v' = `v' * w
    }
    foreach v of local rates {
        gen double `v'_num = `v' * flow
        gen double `v'_den = cond(missing(`v'), 0, flow)
    }
    local keep province_2023 district_2023
    capture confirm variable unit_2023
    if _rc == 0 local keep `keep' unit_2023
    local rsum
    foreach v of local rates {
        local rsum `rsum' `v'_num `v'_den
    }
    collapse (sum) `counts' `rsum' (count) n_sources=w (min) min_confrank=confrank ///
        (first) `keep', by(`to')
    foreach v of local rates {
        gen double `v' = `v'_num / `v'_den
        drop `v'_num `v'_den
    }
    gen str6 min_confidence = cond(min_confrank==2,"high",cond(min_confrank==1,"medium","low"))
    drop min_confrank
    order `to' `keep' n_sources min_confidence
end

* Self-check: crosswalking PBS's own 2017 populations must reproduce the 2023 table's
* POPULATION 2017 column exactly.
capture program drop check_crosswalk
program define check_crosswalk
    syntax , CW(string)
    import delimited using "`cw'", clear varnames(1) case(preserve) encoding(utf8) stringcols(_all)
    destring pop_weight pop_2017 pop_2017_restated_2023, replace
    bysort unit_id_2017: gen double wsum = sum(pop_weight)
    bysort unit_id_2017: assert abs(wsum[_N]-1) < 1e-9
    preserve
    keep unit_id_2023 pop_2017_restated_2023
    duplicates drop
    tempfile tgt
    save `tgt'
    restore
    keep unit_id_2017 pop_2017
    duplicates drop
    apply_crosswalk, cw("`cw'") id(unit_id_2017) counts(pop_2017)
    merge 1:1 unit_id_2023 using `tgt', nogenerate
    gen double dev = abs(pop_2017 - pop_2017_restated_2023)
    summarize dev
    di as txt "max deviation from PBS restated 2017 population: " r(max)
end
