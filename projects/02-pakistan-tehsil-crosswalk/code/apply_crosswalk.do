* apply_crosswalk.do  --  move tehsil- or district-level data from one census frame to another
* (1998 -> 2017, 2017 -> 2023, or 1998 -> 2023) using the PBS-based crosswalk. Stata 14+.
*
* Expects:  a dataset in memory with one row per source unit, holding the source id
*           (unit_id_1998 / unit_id_2017 for the tehsil files, district_1998 / district_2017
*           for the district files) and the variables to crosswalk.
* Produces: one row per target unit.
*
* Example:
*   use mydata_1998, clear
*   apply_crosswalk, cw("crosswalk_tehsil_1998_to_2023.csv") id(unit_id_1998) ///
*       counts(schools votes) rates(literacy) weight(pop)
*
* counts: allocated along each crosswalk row by the chosen weight and summed.
* rates : averaged over source units with weights = people moved (pop_weight x source population).
*         Rates whose denominator is not population should be rebuilt from counts instead.
* weight: pop (default) or area.
* The source and target years are read from the crosswalk's column names. Frames: 1998, 2017, 2023 and
* 1998census (the census-day 1998 units, id unit_id_1998census / district_1998census). The two census-day ->
* report-frame tables (…_1998census_to_pcoframe.csv) carry population weights only and are not handled by this
* program; use the R function or the chained …_1998census_to_2023.csv tables.

capture program drop _cw_frames
program define _cw_frames, rclass
    * finds the two census years in the crosswalk variable names
    local yrs
    foreach v of varlist _all {
        if regexm("`v'", "^(unit_id|district)_([0-9][0-9][0-9][0-9](census)?)$") {
            local y = regexs(2)
            if !strpos(" `yrs' ", " `y' ") local yrs `yrs' `y'
        }
    }
    local yrs : list sort yrs
    local n : word count `yrs'
    if `n' != 2 {
        di as err "could not read the two census years from the crosswalk columns"
        exit 459
    }
    return local from : word 1 of `yrs'
    return local to   : word 2 of `yrs'
end

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
    isid `id'
    save `src'
    import delimited using "`cw'", clear varnames(1) case(preserve) encoding(utf8) stringcols(_all)
    _cw_frames
    local from `r(from)'
    local to   `r(to)'
    destring pop_weight area_weight pop_`from', replace
    capture confirm variable unit_id_`to'
    if _rc == 0 local tovar unit_id_`to'
    else local tovar district_`to'
    capture confirm variable `id'
    if _rc {
        di as err "id `id' is not a column of the crosswalk"
        exit 111
    }
    rename `id' `id'_cw
    gen double w = `weight'_weight
    gen double flow = pop_weight * pop_`from'
    gen byte confrank = cond(confidence=="high",2,cond(confidence=="medium",1,0))
    capture confirm variable unit_`to'
    if _rc == 0 local uvar unit_`to'
    keep `id'_cw `tovar' province_`to' district_`to' `uvar' w flow confrank
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
    local keep province_`to' district_`to' `uvar'
    local rsum
    foreach v of local rates {
        local rsum `rsum' `v'_num `v'_den
    }
    collapse (sum) `counts' `rsum' (count) n_sources=w (min) min_confrank=confrank ///
        (first) `keep', by(`tovar')
    foreach v of local rates {
        gen double `v' = `v'_num / `v'_den
        drop `v'_num `v'_den
    }
    gen str6 min_confidence = cond(min_confrank==2,"high",cond(min_confrank==1,"medium","low"))
    drop min_confrank
    order `tovar' `keep' n_sources min_confidence
end

* Self-check: pushing the source census populations through the crosswalk must conserve the
* total and, where PBS printed the source-year population on the target frame
* (pop_1998_restated_2017, pop_2017_restated_2023), reproduce that column exactly.
capture program drop check_crosswalk
program define check_crosswalk
    syntax , CW(string)
    import delimited using "`cw'", clear varnames(1) case(preserve) encoding(utf8) stringcols(_all)
    _cw_frames
    local from `r(from)'
    local to   `r(to)'
    capture confirm variable unit_id_`to'
    if _rc == 0 local lvl unit_id
    else local lvl district
    destring pop_weight area_weight pop_`from', replace
    bysort `lvl'_`from': egen double wsum = total(pop_weight)
    assert abs(wsum-1) < 1e-9
    bysort `lvl'_`from': egen double asum = total(area_weight)
    assert abs(asum-1) < 1e-9
    di as txt "weights sum to 1 for every source unit: yes"
    capture confirm variable pop_`from'_restated_`to'
    local has_rest = (_rc == 0)
    if `has_rest' {
        destring pop_`from'_restated_`to', replace
        preserve
        keep `lvl'_`to' pop_`from'_restated_`to'
        duplicates drop
        tempfile tgt
        save `tgt'
        restore
    }
    keep `lvl'_`from' pop_`from'
    duplicates drop
    summarize pop_`from', meanonly
    local total = r(sum)
    apply_crosswalk, cw("`cw'") id(`lvl'_`from') counts(pop_`from')
    summarize pop_`from', meanonly
    di as txt "total source population: " %15.2f `total' "   after crosswalk: " %15.2f r(sum)
    if `has_rest' {
        merge 1:1 `lvl'_`to' using `tgt', nogenerate
        gen double dev = abs(pop_`from' - pop_`from'_restated_`to')
        summarize dev
        di as txt "max deviation from PBS restated `from' population on `to' units: " r(max)
    }
    else di as txt "no PBS restatement exists for `from' on `to' units (chained table); total conservation only"
end

* Historical district maps (1951, 1961, 1972, 1981) -> 1998 or 2023 districts, using
* crosswalk_district_historical_to_1998.csv or _to_2023.csv. The dataset in memory must have one row
* per historical district (variable historical_district, names as in district_frames_by_census.csv)
* for one census year.
capture program drop apply_historical
program define apply_historical
    version 14
    syntax , CW(string) YEAR(integer) [COUNTS(varlist) RATES(varlist)]
    tempfile src cwf
    isid historical_district
    save `src'
    import delimited using "`cw'", clear varnames(1) case(preserve) encoding(utf8) stringcols(_all)
    destring census_year weight pop_historical_district, replace
    keep if census_year == `year'
    capture confirm variable district_2023
    if _rc == 0 local tovar district_2023
    else local tovar district_1998
    gen double flow = weight * pop_historical_district
    gen byte proxy = strpos(weight_basis, "proxy") > 0
    keep historical_district `tovar' weight flow proxy lineage_confidence
    save `cwf'
    use `src', clear
    merge 1:m historical_district using `cwf', keep(match) nogenerate
    foreach v of local counts {
        replace `v' = `v' * weight
    }
    local rsum
    foreach v of local rates {
        gen double `v'_num = `v' * flow
        gen double `v'_den = cond(missing(`v'), 0, flow)
        local rsum `rsum' `v'_num `v'_den
    }
    collapse (sum) `counts' `rsum' (count) n_sources=weight (max) any_proxy_weight=proxy, by(`tovar')
    foreach v of local rates {
        gen double `v' = `v'_num / `v'_den
        drop `v'_num `v'_den
    }
end
