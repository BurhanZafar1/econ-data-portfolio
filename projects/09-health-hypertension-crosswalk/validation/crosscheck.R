# Independent re-estimation in R of the two building blocks of the crosswalk.
#
#   Rscript validation/crosscheck.R      (run from the project folder, after python run.py)
#
# 1. Paired survey estimates (R survey): for every cycle and crosswalk cell, the
#    self reported and measured prevalence and the logit difference d with its
#    design based standard error (svycontrast on the joint covariance).
# 2. The meta-regression (R metafor): rma(method = "DL") on the 2013-2018 cells,
#    the window the final crosswalk uses.
# Writes output/r_crosscheck.csv and stops if any difference exceeds 1e-6.
#
# Tested with R 4.3.3, survey 4.5, metafor 5.2-1.

suppressPackageStartupMessages({
  library(survey)
  library(metafor)
})

extract <- read.csv(gzfile("data/nhanes_htn_extract.csv.gz"))
extract$age_group <- cut(extract$age, c(18, 25, 35, 45, 55, 65, 200), right = FALSE,
                         labels = c("18-24", "25-34", "35-44", "45-54", "55-64", "65+"))
extract$xw_group <- ifelse(extract$age_group %in% c("18-24", "25-34"), "18-34",
                           as.character(extract$age_group))
extract$self_htn[is.na(extract$self_htn)] <- 0
extract$measured_htn[is.na(extract$measured_htn)] <- 0

python <- read.csv("output/paired_estimates_age_sex.csv")
rows <- list()
for (cyc in sort(unique(extract$cycle))) {
  d <- extract[extract$cycle == cyc, ]
  des <- svydesign(ids = ~psu, strata = ~stratum, weights = ~wt_mec, nest = TRUE, data = d)
  sub <- subset(des, analysis == 1)
  est <- svyby(~self_htn + measured_htn, ~xw_group + sex, sub, svymean, covmat = TRUE)
  for (i in seq_len(nrow(est))) {
    cell <- paste(est$xw_group[i], est$sex[i], sep = ".")
    expr <- substitute(log(m / (1 - m)) - log(s / (1 - s)),
                       list(m = as.name(paste0(cell, ":measured_htn")),
                            s = as.name(paste0(cell, ":self_htn"))))
    contrast <- svycontrast(est, list(d = expr))
    rows[[length(rows) + 1]] <- data.frame(
      cycle = cyc, xw_group = est$xw_group[i], sex = est$sex[i],
      r_p_self = est$self_htn[i], r_p_meas = est$measured_htn[i],
      r_d = as.numeric(coef(contrast)), r_se_d = as.numeric(SE(contrast)))
  }
}
r_paired <- do.call(rbind, rows)
both <- merge(python, r_paired, by = c("cycle", "xw_group", "sex"))
stopifnot(nrow(both) == nrow(python), nrow(both) == 100)

window <- both[both$cycle %in% c("2013-2014", "2015-2016", "2017-2018"), ]
window$cell <- factor(paste(window$xw_group, window$sex))
fit <- rma(yi = d, vi = se_d^2, mods = ~ 0 + cell, data = window, method = "DL")
python_xw <- read.csv("output/crosswalk_age_sex.csv")
python_xw$cell <- paste(python_xw$xw_group, python_xw$sex)
r_coef <- setNames(as.numeric(coef(fit)), sub("^cell", "", names(coef(fit))))

checks <- data.frame(
  quantity = c("p_self (100 cells)", "p_meas (100 cells)", "d (100 cells)", "se_d (100 cells)",
               "crosswalk d (10 cells)", "tau^2"),
  max_abs_difference = c(
    max(abs(both$p_self - both$r_p_self)),
    max(abs(both$p_meas - both$r_p_meas)),
    max(abs(both$d - both$r_d)),
    max(abs(both$se_d - both$r_se_d)),
    max(abs(python_xw$d - r_coef[python_xw$cell])),
    abs(python_xw$tau[1]^2 - fit$tau2)))
print(checks, digits = 3)
write.csv(checks, "output/r_crosscheck.csv", row.names = FALSE)
stopifnot(all(checks$max_abs_difference < 1e-6))
cat("R cross-check passed\n")
