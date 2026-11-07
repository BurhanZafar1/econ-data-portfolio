# Independent check of the Python estimates with the R survey package.
#
#   Rscript validation/crosscheck.R      (run from the project folder, after python run.py)
#
# Rebuilds the analysis sample and indicators from data/nhanes_bp_extract.csv.gz,
# estimates crude and WHO age standardized values with survey::svymean and
# survey::svystandardize, and compares them with output/estimates_who_standard.csv.
# Tested with R 4.3.3 and survey 4.2.1.

suppressPackageStartupMessages(library(survey))

extract <- read.csv(gzfile("data/nhanes_bp_extract.csv.gz"))
python <- read.csv("output/estimates_who_standard.csv")

extract$in_sample <- extract$pregnant == 0 & !is.na(extract$sbp) & !is.na(extract$dbp) &
  !is.na(extract$bp_med) & extract$age >= 20
on_med <- extract$bp_med %in% 1
extract$htn140 <- as.numeric(extract$sbp >= 140 | extract$dbp >= 90 | on_med)
extract$htn130 <- as.numeric(extract$sbp >= 130 | extract$dbp >= 80 | on_med)
# Ages 18-19 fall outside the breaks (NA) and are already out of the sample.
extract$agegrp <- cut(extract$age, breaks = c(19, 29, 39, 49, 59, 69, 79, Inf),
                      labels = c("20-29", "30-39", "40-49", "50-59", "60-69", "70-79", "80+"))

# WHO World Standard 2000-2025 percents (Ahmad et al. 2001, Table 4), ages 20+.
who_pct <- c("20-29" = 8.22 + 7.93, "30-39" = 7.61 + 7.15, "40-49" = 6.59 + 6.04,
             "50-59" = 5.37 + 4.55, "60-69" = 3.72 + 2.96, "70-79" = 2.21 + 1.52,
             "80+" = 0.91 + 0.44 + 0.15 + 0.04 + 0.005)
who_w <- who_pct / sum(who_pct)

rows <- list()
for (cyc in sort(unique(extract$cycle))) {
  d <- extract[extract$cycle == cyc, ]
  des <- svydesign(ids = ~psu, strata = ~stratum, weights = ~wt_mec, nest = TRUE, data = d)
  sub <- subset(des, in_sample)
  sub_std <- svystandardize(sub, by = ~agegrp, over = ~1,
                            population = data.frame(agegrp = names(who_w), Freq = as.numeric(who_w)))
  for (m in c("htn140", "htn130", "sbp")) {
    scale <- if (m == "sbp") 1 else 100
    f <- as.formula(paste0("~", m))
    crude <- svymean(f, sub)
    std <- svymean(f, sub_std)
    rows[[length(rows) + 1]] <- data.frame(
      cycle = cyc, measure = m, type = c("crude", "age_standardized"),
      r_estimate = scale * c(coef(crude), coef(std)),
      r_se = scale * c(SE(crude), SE(std))
    )
  }
}
r_out <- do.call(rbind, rows)
py <- python[python$sex == "Both", c("cycle", "measure", "type", "estimate", "se")]
cmp <- merge(r_out, py, by = c("cycle", "measure", "type"))
cmp$diff_estimate <- cmp$r_estimate - cmp$estimate
cmp$diff_se <- cmp$r_se - cmp$se
write.csv(cmp, "output/r_crosscheck.csv", row.names = FALSE)
cat(sprintf("Compared %d estimates. Max |difference|: estimate %.2e, standard error %.2e\n",
            nrow(cmp), max(abs(cmp$diff_estimate)), max(abs(cmp$diff_se))))
