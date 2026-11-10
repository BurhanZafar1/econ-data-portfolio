# Runs check_crosswalk() on every crosswalk table in output/ (called by build/run_all.sh when Rscript is present).
# Run from the project root: Rscript code/run_checks.R
source("code/apply_crosswalk.R")
files <- c("crosswalk_tehsil_2017_to_2023.csv", "crosswalk_tehsil_1998_to_2017.csv", "crosswalk_tehsil_1998_to_2023.csv",
           "crosswalk_district_2017_to_2023.csv", "crosswalk_district_1998_to_2017.csv", "crosswalk_district_1998_to_2023.csv",
           "crosswalk_tehsil_1998census_to_pcoframe.csv", "crosswalk_tehsil_1998census_to_2023.csv",
           "crosswalk_district_1998census_to_pcoframe.csv", "crosswalk_district_1998census_to_2023.csv")
for (f in files) { cat("==", f, "\n"); check_crosswalk(read_crosswalk(file.path("output", f))) }
