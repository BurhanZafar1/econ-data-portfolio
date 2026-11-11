# Independent re-estimation in R of the exposure means and central PAFs.
#
#   Rscript validation/crosscheck.R      (run from the project folder, after python run.py)
#
# Uses only base R and the survey package (tested with R 4.3.3, survey 4.2.1).
# Writes output/r_crosscheck.csv and stops if R and Python disagree.

suppressPackageStartupMessages(library(survey))

nh <- read.csv(gzfile("data/nhanes_sbp_2017_2018.csv.gz"))
nh$age_group <- cut(nh$age, breaks = c(40, 50, 60, 70, 80, 200), right = FALSE,
                    labels = c("40-49", "50-59", "60-69", "70-79", "80+"))

# PSC 2002 hazard ratios per 20 mmHg lower usual SBP; 80+ uses the 80-89 band.
psc <- read.csv("data/psc2002_ihd_hazard_ratios.csv")
psc <- psc[psc$sex != "Both", ]
psc$age_group <- ifelse(psc$age_band == "80-89", "80+", psc$age_band)
psc$beta <- -log(psc$hr_per_20) / 20
nh <- merge(nh, psc[, c("sex", "age_group", "beta")], by = c("sex", "age_group"))

tmrel <- (110 + 115) / 2
nh$rr <- exp(nh$beta * pmax(nh$sbp - tmrel, 0))

des <- svydesign(ids = ~psu, strata = ~stratum, weights = ~wt_mec, nest = TRUE, data = nh)
sbp <- svyby(~sbp, ~sex + age_group, des, svymean)
rr <- svyby(~rr, ~sex + age_group, des, svymean)

r_out <- data.frame(sex = sbp$sex, age_group = as.character(sbp$age_group),
                    r_mean_sbp = sbp$sbp, r_se = SE(sbp),
                    r_paf_central = (rr$rr - 1) / rr$rr)

py_exp <- read.csv("output/exposure_sbp_age_sex.csv")
py_paf <- read.csv("output/paf_ihd_age_sex.csv")
cmp <- merge(merge(r_out, py_exp[, c("sex", "age_group", "mean_sbp", "se")]),
             py_paf[, c("sex", "age_group", "paf_central")])
cmp$diff_mean <- cmp$r_mean_sbp - cmp$mean_sbp
cmp$diff_se <- cmp$r_se - cmp$se
cmp$diff_paf <- cmp$r_paf_central - cmp$paf_central
write.csv(cmp, "output/r_crosscheck.csv", row.names = FALSE)

worst <- max(abs(cmp$diff_mean), abs(cmp$diff_se), abs(cmp$diff_paf))
cat(sprintf("Cells compared: %d. Largest absolute difference: %.2e\n", nrow(cmp), worst))
if (nrow(cmp) != 10 || worst > 1e-3) stop("R and Python estimates disagree")
cat("R cross-check passed.\n")
