# apply_crosswalk.R  --  move tehsil- or district-level data from one census frame to another
# (1998 -> 2017, 2017 -> 2023, 1998 -> 2023, or the census-day 1998 layers) using the PBS-based crosswalk. Base R only.
#
# Usage:
#   source("apply_crosswalk.R")
#   cw  <- read_crosswalk("crosswalk_tehsil_1998_to_2023.csv")
#   out <- apply_crosswalk(mydata, cw, id = "unit_id_1998",
#                          counts = c("schools","votes"), rates = c("literacy"),
#                          weight = "pop")
#
# Arguments
#   data    data.frame with one row per source unit (tehsil or district) and its id column
#   cw      crosswalk data.frame (any of the tehsil or district files). The source and target
#           years are read from its column names (unit_id_1998 / unit_id_2017 / unit_id_2023,
#           or district_1998 / district_2017 / district_2023).
#   id      name of the column in `data` holding the source id. For a tehsil file use the
#           unit id (T98-nnnn, T17-nnnn); for a district file use district_1998 or district_2017.
#   counts  columns that are counts (people, votes, schools): allocated by the weight and summed
#   rates   columns that are rates or means (literacy rate, turnout): averaged over source
#           units with weights = people moved along the row (pop weight x source population).
#           Rates whose denominator is not population should instead be rebuilt from
#           numerator and denominator counts.
#   weight  "pop" (default) or "area"
#
# Returns one row per target unit with the crosswalked columns, the number of source units,
# and the lowest confidence among the rows used.

read_crosswalk <- function(path) {
  cw <- read.csv(path, stringsAsFactors = FALSE, check.names = FALSE)
  stopifnot(all(c("pop_weight", "confidence") %in% names(cw)))
  if (!"area_weight" %in% names(cw)) cw$area_weight <- NA_real_   # the census-day -> report-frame tables carry population weights only
  cw
}

.frames <- function(cw) {
  # frame labels are the suffixes of the id columns: 1998, 2017, 2023, or 1998census (census-day 1998 units)
  # and 1998_pcoframe (the report frame as target of the census-day layer); sorted so that 1998 < 1998census < 2017 < 2023
  yrs <- sub("_pcoframe$", "", sub(".*_(\\d{4}[a-z_]*)$", "\\1", grep("^(unit_id|district)_\\d{4}(census|_pcoframe)?$", names(cw), value = TRUE)))
  yrs <- sort(unique(yrs))
  yrs <- yrs[order(substr(yrs, 1, 4), yrs)]
  if (identical(sort(yrs), c("1998", "1998census"))) yrs <- c("1998census", "1998")   # census-day units -> report frame
  if (length(yrs) != 2) stop("could not read the two census frames from the crosswalk columns")
  list(from = yrs[1], to = yrs[2])
}

.idcol <- function(cw, level, fr) {   # the id column of a frame; the report-frame side of the census-day district table is district_1998_pcoframe
  for (v in c(paste0(level, "_", fr), paste0(level, "_", fr, "_pcoframe"))) if (v %in% names(cw)) return(v)
  paste0(level, "_", fr)
}

apply_crosswalk <- function(data, cw, id = NULL, counts = character(0),
                            rates = character(0), weight = c("pop", "area")) {
  weight <- match.arg(weight)
  fr <- .frames(cw)
  wcol <- if (weight == "pop") "pop_weight" else "area_weight"
  level <- if (paste0("unit_id_", fr$to) %in% names(cw)) "unit_id" else "district"
  to_id <- .idcol(cw, level, fr$to)
  if (is.null(id)) id <- .idcol(cw, level, fr$from)
  if (!id %in% names(cw)) stop("id column not in crosswalk: ", id)
  if (!id %in% names(data)) stop("id column not in data: ", id)
  if (anyDuplicated(data[[id]])) stop("data must have one row per source unit")
  missing_units <- setdiff(data[[id]], cw[[id]])
  if (length(missing_units)) warning(length(missing_units), " ids in data not in crosswalk, e.g. ",
                                     paste(head(missing_units, 5), collapse = ", "))
  # data columns that share a name with a crosswalk column get the suffix .data
  m <- merge(cw, data, by = id, suffixes = c("", ".data"))
  dcol <- function(v) if (v %in% names(cw)) paste0(v, ".data") else v
  m$w <- m[[wcol]]
  m$flow <- m$pop_weight * m[[paste0("pop_", fr$from)]]   # people moved along the row
  conf_rank <- c(high = 2, medium = 1, low = 0)
  out <- do.call(rbind, lapply(split(m, m[[to_id]]), function(g) {
    r <- data.frame(tid = g[[to_id]][1], n_sources = nrow(g),
                    min_confidence = names(conf_rank)[conf_rank == min(conf_rank[g$confidence])][1],
                    stringsAsFactors = FALSE)
    for (v in counts) r[[v]] <- sum(g$w * g[[dcol(v)]], na.rm = TRUE)
    for (v in rates)  r[[v]] <- if (sum(g$flow[!is.na(g[[dcol(v)]])]) > 0)
      sum(g$flow * g[[dcol(v)]], na.rm = TRUE) / sum(g$flow[!is.na(g[[dcol(v)]])]) else NA_real_
    r
  }))
  names(out)[names(out) == "tid"] <- to_id
  rownames(out) <- NULL
  lab <- unique(cw[, intersect(c(to_id, paste0(c("province_", "district_", "unit_"), fr$to), paste0(c("district_", "unit_"), fr$to, "_pcoframe")), names(cw)), drop = FALSE])
  merge(lab, out, by = to_id)
}

# Self-check. Pushing the source census populations through the crosswalk must (a) conserve the
# total and (b) where PBS printed the source-year population on the target frame
# (pop_1998_restated_2017, pop_2017_restated_2023), reproduce that column exactly.
check_crosswalk <- function(cw) {
  fr <- .frames(cw)
  level <- if (paste0("unit_id_", fr$to) %in% names(cw)) "unit_id" else "district"
  from_id <- .idcol(cw, level, fr$from); to_id <- .idcol(cw, level, fr$to)
  popcol <- paste0("pop_", fr$from)
  u <- unique(cw[, c(from_id, popcol)])
  out <- apply_crosswalk(u, cw, id = from_id, counts = popcol)
  cat("weights sum to 1 for every source unit:",
      all(abs(tapply(cw$pop_weight, cw[[from_id]], sum) - 1) < 1e-9),
      "(pop) ", if (all(is.na(cw$area_weight))) "no area weight in this table" else all(abs(tapply(cw$area_weight, cw[[from_id]], sum) - 1) < 1e-9), "(area)\n")
  cat("total source population conserved:", isTRUE(all.equal(sum(out[[popcol]]), sum(u[[popcol]]))), "\n")
  rest <- paste0("pop_", fr$from, "_restated_", fr$to)
  if (fr$from == "1998census" && fr$to == "1998") rest <- "pop_1998_pcoframe"   # the report frame's own 1998 count
  if (rest %in% names(cw)) {
    tgt <- unique(cw[, c(to_id, rest)])
    chk <- merge(out, tgt, by = to_id)
    dev <- max(abs(chk[[popcol]] - chk[[rest]]))
    cat("max deviation from PBS restated", fr$from, "population on", fr$to, "units:", dev, "\n")
    invisible(dev)
  } else {
    cat("no PBS restatement exists for", fr$from, "on", fr$to, "units (chained table); total conservation only\n")
    invisible(NA)
  }
}

# Historical district maps (1951, 1961, 1972, 1981) -> 1998 or 2023 districts.
# These tables (crosswalk_district_historical_to_1998.csv / _to_2023.csv) carry one population weight
# per row and are keyed by census_year and historical_district. `data` must have one row per
# historical district for one census year, named as in district_frames_by_census.csv.
apply_historical <- function(data, cw, census_year, id = "historical_district",
                             counts = character(0), rates = character(0)) {
  cw <- cw[cw$census_year == census_year, ]
  if (!nrow(cw)) stop("no rows for census_year ", census_year)
  to_id <- if ("district_2023" %in% names(cw)) "district_2023" else "district_1998"
  if (anyDuplicated(data[[id]])) stop("data must have one row per historical district")
  missing_units <- setdiff(data[[id]], cw$historical_district)
  if (length(missing_units)) warning(length(missing_units), " historical districts not in crosswalk, e.g. ",
                                     paste(head(missing_units, 5), collapse = ", "))
  m <- merge(cw, data, by.x = "historical_district", by.y = id, suffixes = c("", ".data"))
  dcol <- function(v) if (v %in% names(cw)) paste0(v, ".data") else v
  m$flow <- m$weight * m$pop_historical_district
  out <- do.call(rbind, lapply(split(m, m[[to_id]]), function(g) {
    r <- data.frame(tid = g[[to_id]][1], n_sources = length(unique(g$historical_district)),
                    min_lineage_confidence = if (any(g$lineage_confidence == "unverified")) "unverified"
                                             else if (any(g$lineage_confidence == "reported")) "reported" else "verified",
                    any_proxy_weight = any(grepl("^proxy", g$weight_basis)), stringsAsFactors = FALSE)
    for (v in counts) r[[v]] <- sum(g$weight * g[[dcol(v)]], na.rm = TRUE)
    for (v in rates)  r[[v]] <- if (sum(g$flow[!is.na(g[[dcol(v)]])]) > 0)
      sum(g$flow * g[[dcol(v)]], na.rm = TRUE) / sum(g$flow[!is.na(g[[dcol(v)]])]) else NA_real_
    r
  }))
  names(out)[names(out) == "tid"] <- to_id
  rownames(out) <- NULL
  out
}

check_historical <- function(cw) {
  for (y in sort(unique(cw$census_year))) {
    s <- cw[cw$census_year == y, ]
    w <- tapply(s$weight, s$historical_district, sum)
    cat(y, ": ", length(w), " historical districts; weights sum to 1: ", all(abs(w - 1) < 1e-6),
        "; proxy rows: ", sum(grepl("^proxy", s$weight_basis)), "\n", sep = "")
  }
}
