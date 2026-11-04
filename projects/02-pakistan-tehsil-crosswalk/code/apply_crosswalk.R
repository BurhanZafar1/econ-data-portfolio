# apply_crosswalk.R  --  move tehsil- or district-level data from the 2017 census frame
# to the 2023 census frame using the PBS-based crosswalk. Base R only.
#
# Usage:
#   source("apply_crosswalk.R")
#   cw  <- read_crosswalk("crosswalk_tehsil_2017_to_2023.csv")
#   out <- apply_crosswalk(mydata, cw, id = "unit_id_2017",
#                          counts = c("schools","votes"), rates = c("literacy"),
#                          weight = "pop")
#
# Arguments
#   data    data.frame with one row per 2017 unit (tehsil or district) and the 2017 id column
#   cw      crosswalk data.frame (tehsil or district file)
#   id      name of the column in `data` holding the 2017 id. For the tehsil file use
#           unit_id_2017 (T17-nnnn) or the pair district_2017 + unit_2017; for the district
#           file use district_2017.
#   counts  columns that are counts (people, votes, schools): allocated by the weight and summed
#   rates   columns that are rates or means (literacy rate, turnout): averaged over source
#           units with weights = flow of people (pop weight x 2017 population). Rates of a
#           variable whose denominator is not population should instead be rebuilt from
#           numerator and denominator counts.
#   weight  "pop" (default) or "area"
#
# Returns one row per 2023 unit with the crosswalked columns, the number of source units,
# and the lowest confidence among the rows used.

read_crosswalk <- function(path) {
  cw <- read.csv(path, stringsAsFactors = FALSE, check.names = FALSE)
  stopifnot(all(c("pop_weight", "area_weight") %in% names(cw)))
  cw
}

apply_crosswalk <- function(data, cw, id = "unit_id_2017", counts = character(0),
                            rates = character(0), weight = c("pop", "area")) {
  weight <- match.arg(weight)
  wcol <- if (weight == "pop") "pop_weight" else "area_weight"
  to_id <- if ("unit_id_2023" %in% names(cw)) "unit_id_2023" else "district_2023"
  from_id <- if (id %in% names(cw)) id else stop("id column not in crosswalk: ", id)
  if (anyDuplicated(data[[id]])) stop("data must have one row per 2017 unit")
  missing_units <- setdiff(data[[id]], cw[[from_id]])
  if (length(missing_units)) warning(length(missing_units), " ids in data not in crosswalk, e.g. ",
                                     paste(head(missing_units, 5), collapse = ", "))
  m <- merge(cw, data, by.x = from_id, by.y = id, all.x = FALSE, all.y = FALSE)
  m$w <- m[[wcol]]
  # people moved along each row: the weight for averaging rates
  m$flow <- m$pop_weight * m$pop_2017
  conf_rank <- c(high = 2, medium = 1, low = 0)
  out <- do.call(rbind, lapply(split(m, m[[to_id]]), function(g) {
    r <- data.frame(id23 = g[[to_id]][1], n_sources = nrow(g),
                    min_confidence = names(conf_rank)[which(conf_rank == min(conf_rank[g$confidence]))][1],
                    stringsAsFactors = FALSE)
    for (v in counts) r[[v]] <- sum(g$w * g[[v]], na.rm = TRUE)
    for (v in rates)  r[[v]] <- if (sum(g$flow) > 0) sum(g$flow * g[[v]], na.rm = TRUE) / sum(g$flow[!is.na(g[[v]])]) else NA_real_
    r
  }))
  names(out)[names(out) == "id23"] <- to_id
  rownames(out) <- NULL
  # attach 2023 names
  lab <- unique(cw[, intersect(c(to_id, "province_2023", "district_2023", "unit_2023"), names(cw))])
  merge(lab, out, by = to_id)
}

# Minimal self-check: crosswalking PBS's own 2017 populations must reproduce the 2023 table's
# "POPULATION 2017" column exactly, and provincial totals must be unchanged.
check_crosswalk <- function(cw) {
  u <- unique(cw[, c("unit_id_2017", "pop_2017")])
  out <- apply_crosswalk(u, cw, id = "unit_id_2017", counts = "pop_2017")
  tgt <- unique(cw[, c("unit_id_2023", "pop_2017_restated_2023")])
  chk <- merge(out, tgt, by = "unit_id_2023")
  dev <- max(abs(chk$pop_2017 - chk$pop_2017_restated_2023))
  cat("max deviation from PBS restated 2017 population:", dev, "\n")
  cat("weights sum to 1 for every 2017 unit:",
      all(abs(tapply(cw$pop_weight, cw$unit_id_2017, sum) - 1) < 1e-9), "\n")
  invisible(dev)
}
