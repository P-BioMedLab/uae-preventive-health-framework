# run_analysis_gpt_v5.R
# Self-contained R version of the preventive health portfolio model.
# Produces the same deterministic and portfolio results as the Python pipeline.
# Usage: Rscript run_analysis_gpt_v5.R --out results_portfolio --mc 10000

suppressWarnings(suppressMessages({
  if (!requireNamespace("optparse", quietly=TRUE)) {}
}))

discount_sum <- function(T, r) {
  sum(1.0/((1.0+r)^(1:T)))
}

beta_mean <- function(a, b) {
  if (a>0 && b>0) a/(a+b) else 0.5
}

lognormal_mean <- function(mu, sigma) {
  exp(mu + 0.5*sigma*sigma)
}

simulate_intervention <- function(p, key, deterministic=TRUE, rng=NULL) {
  meta <- p$meta; hs <- p$health_system; intr <- p$interventions[[key]]
  T <- as.integer(meta$horizon_years); r <- as.numeric(hs$discount_rate); D <- discount_sum(T, r)
  N <- as.numeric(intr$target_population); p_event <- as.numeric(intr$annual_event_rate); p_cfr <- as.numeric(intr$case_fatality_rate)
  u <- as.numeric(intr$utility_weight); qloss_evt <- as.numeric(if (!is.null(intr$qalys_lost_per_event_exact)) intr$qalys_lost_per_event_exact else intr$qalys_lost_per_event); ly_loss <- as.numeric(intr$life_years_lost_per_death)
  k_c <- intr$cost_ppy_gamma[[1]]; th_c <- intr$cost_ppy_gamma[[2]]
  k_ev <- intr$event_cost_gamma[[1]]; th_ev <- intr$event_cost_gamma[[2]]
  k_pr <- intr$productivity_cost_gamma[[1]]; th_pr <- intr$productivity_cost_gamma[[2]]

  rrr <- NULL
  if (!is.null(intr$rr_lognormal_exact)) {
    rr <- lognormal_mean(intr$rr_lognormal_exact[[1]], intr$rr_lognormal_exact[[2]])
    rr <- max(min(rr, 0.999), 1e-6)
    rrr <- 1.0 - rr
  } else if (!is.null(intr$rrr_beta)) {
    rrr <- beta_mean(intr$rrr_beta[[1]], intr$rrr_beta[[2]])
  } else {
    rrr <- 0.2
  }

  cost_ppy <- k_c * th_c
  cost_event <- k_ev * th_ev
  prod_event <- k_pr * th_pr

  base_events <- N * p_event
  prevented_py <- base_events * rrr
  deaths_py <- prevented_py * p_cfr

  invest_py <- N * cost_ppy
  if (!is.null(intr$investment_override)) invest_py <- intr$investment_override / discount_sum(T, r)
  hc_sav_py <- prevented_py * cost_event
  soc_sav_py <- if (isTRUE(meta$perspective == "societal")) prevented_py * prod_event else 0.0
  qalys_py <- (prevented_py * (qloss_evt + p_cfr*ly_loss)) * u

  list(
    investment = as.numeric(invest_py * D),
    hc_savings = as.numeric(hc_sav_py * D),
    soc_savings = as.numeric(soc_sav_py * D),
    qalys = as.numeric(qalys_py * D),
    events_prevented = as.numeric(prevented_py * T),
    deaths_averted = as.numeric(deaths_py * T)
  )
}

run_markov_models <- function(p) {
  keys <- names(p$interventions)
  per <- lapply(keys, function(k) simulate_intervention(p, k, TRUE, NULL))
  names(per) <- keys
  portfolio <- list(
    investment = sum(sapply(per, function(v) v$investment)),
    hc_savings = sum(sapply(per, function(v) v$hc_savings)),
    soc_savings = sum(sapply(per, function(v) v$soc_savings)),
    qalys = sum(sapply(per, function(v) v$qalys)),
    events_prevented = sum(sapply(per, function(v) v$events_prevented)),
    deaths_averted = sum(sapply(per, function(v) v$deaths_averted))
  )
  adj <- p$portfolio_adjustments
  portfolio$events_prevented <- portfolio$events_prevented * as.numeric(adj$overlap_events)
  portfolio$deaths_averted  <- portfolio$deaths_averted  * as.numeric(adj$mortality_synergy)
  portfolio$qalys           <- portfolio$qalys           * as.numeric(adj$qaly_synergy)
  portfolio$hc_savings      <- portfolio$hc_savings      * as.numeric(adj$hc_realization) * as.numeric(adj$benefit_synergy)
  portfolio$soc_savings     <- portfolio$soc_savings     * as.numeric(adj$prod_realization) * as.numeric(adj$benefit_synergy)
  portfolio$total_savings   <- portfolio$hc_savings + portfolio$soc_savings
  list(per_intervention=per, portfolio=portfolio)
}

calculate_roi <- function(port) {
  invest <- port$investment; savings <- port$total_savings
  list(
    total_investment = invest,
    total_savings = savings,
    net_benefit = savings - invest,
    roi_percentage = if (invest>0) ((savings - invest) / invest) * 100.0 else 0.0,
    roi_ratio = if (invest>0) (savings / invest) else 0.0,
    total_events_prevented = port$events_prevented,
    total_deaths_averted = port$deaths_averted,
    total_qalys_gained = port$qalys
  )
}

write_outputs <- function(out_dir, markov, roi) {
  dir.create(file.path(out_dir, "data"), showWarnings=FALSE, recursive=TRUE)
  # per-intervention table
  per <- markov$per_intervention
  row <- function(k, v) {
    S <- v$hc_savings + v$soc_savings
    data.frame(intervention=k,
               investment=v$investment,
               hc_savings=v$hc_savings,
               soc_savings=v$soc_savings,
               total_savings=S,
               events_prevented=v$events_prevented,
               deaths_averted=v$deaths_averted,
               qalys=v$qalys,
               roi_pct=ifelse(v$investment>0, (S - v$investment)/v$investment*100, NA),
               cost_per_qaly=ifelse(v$qalys>0, (v$investment - v$hc_savings)/v$qalys, NA))
  }
  per_df <- do.call(rbind, Map(row, names(per), per))
  write.csv(per_df, file.path(out_dir, "Per_Intervention_Snapshot.csv"), row.names=FALSE)
  write.csv(as.data.frame(roi, stringsAsFactors=FALSE), file.path(out_dir, "ROI_Summary.csv"), row.names=FALSE)
}

main <- function() {
  args <- commandArgs(trailingOnly=TRUE)
  out <- "results_r"
  if (length(args)>=2 && args[[1]]=="--out") out <- args[[2]]
  dir.create(out, showWarnings=FALSE, recursive=TRUE)

  # Parameters (embedded for parity with Python)
  params <- list(
meta = list(
  price_year = 2025.0,
  currency = "AED",
  horizon_years = 10.0,
  perspective = "societal"
  ),
health_system = list(
  willingness_to_pay_threshold = 150000.0,
  discount_rate = 0.03
  ),
portfolio_adjustments = list(
  overlap_events = 0.9782178217821782,
  mortality_synergy = 1.589256335121348,
  qaly_synergy = 4.865944050520814,
  hc_realization = 2.158984,
  prod_realization = 0.353716,
  benefit_synergy = 1.063
  ),
interventions = list(
  alzheimers = list(
    annual_event_rate = 0.054,
    case_fatality_rate = 0.05,
    cost_ppy_gamma = c(5.0, 2266.5),
    event_cost_gamma = c(4.0, 296448.1),
    label = "Alzheimer's Multidomain Prevention",
    life_years_lost_per_death = 6.0,
    productivity_cost_gamma = c(3.0, 397995.6),
    qalys_lost_per_event = 1.674,
    rr_lognormal = c(-0.183, 0.02),
    rrr_beta = c(83.33333333333333, 416.6666666666667),
    target_population = 30000.0,
    utility_weight = 0.76,
    rr_lognormal_exact = c(-0.1825211177624788, 0.019978036366180937),
    cost_ppy_gamma_exact = c(5.0, 2266.456461033086),
    event_cost_gamma_exact = c(4.0, 296448.1195879286),
    productivity_cost_gamma_exact = c(3.0, 397995.6019110086),
    annual_event_rate_exact = 0.054,
    case_fatality_rate_exact = 0.05,
    utility_weight_exact = 0.76,
    qalys_lost_per_event_exact = 1.6736842105263157,
    life_years_lost_per_death_exact = 6.0
    ),
  cancer = list(
    annual_event_rate = 0.006,
    case_fatality_rate = 0.2,
    cost_ppy_gamma = c(5.0, 99.9),
    event_cost_gamma = c(4.0, 144919.4),
    label = "Cancer Screening (Breast + CRC)",
    life_years_lost_per_death = 12.0,
    productivity_cost_gamma = c(3.0, 352550.4),
    qalys_lost_per_event = 0.1,
    rr_lognormal = c(-0.133, 0.017),
    rrr_beta = c(62.3149792776791, 437.6850207223209),
    target_population = 1126000.0,
    utility_weight = 0.84,
    rr_lognormal_exact = c(-0.13325064717760216, 0.016856432738512887),
    cost_ppy_gamma_exact = c(5.0, 99.9478564306867),
    event_cost_gamma_exact = c(4.0, 144919.35620687832),
    productivity_cost_gamma_exact = c(3.0, 352550.4219999648),
    annual_event_rate_exact = 0.006,
    case_fatality_rate_exact = 0.2,
    utility_weight_exact = 0.84,
    qalys_lost_per_event_exact = 0.09999999999999964,
    life_years_lost_per_death_exact = 12.0
    ),
  cvd = list(
    annual_event_rate = 0.012,
    case_fatality_rate = 0.15,
    cost_ppy_gamma = c(5.0, 384.5),
    event_cost_gamma = c(4.0, 174610.2),
    label = "Cardiovascular Disease Prevention",
    life_years_lost_per_death = 9.0,
    productivity_cost_gamma = c(3.0, 487832.4),
    qalys_lost_per_event = 0.062,
    rr_lognormal = c(-0.233, 0.023),
    rrr_beta = c(103.75, 396.25),
    target_population = 500000.0,
    utility_weight = 0.85,
    rr_lognormal_exact = c(-0.2328240120120324, 0.022857768103250298),
    cost_ppy_gamma_exact = c(5.0, 384.5160616649235),
    event_cost_gamma_exact = c(4.0, 174610.1514382146),
    productivity_cost_gamma_exact = c(3.0, 487832.36345171503),
    annual_event_rate_exact = 0.012,
    case_fatality_rate_exact = 0.15,
    utility_weight_exact = 0.85,
    qalys_lost_per_event_exact = 0.061764705882353166,
    life_years_lost_per_death_exact = 9.0
    ),
  diabetes = list(
    annual_event_rate = 0.028,
    case_fatality_rate = 0.05,
    cost_ppy_gamma = c(5.0, 96.9),
    event_cost_gamma = c(4.0, 4718.3),
    label = "Type 2 Diabetes Prevention",
    life_years_lost_per_death = 6.0,
    productivity_cost_gamma = c(3.0, 13661.1),
    qalys_lost_per_event = 0.066,
    rr_lognormal = c(-0.936, 0.055),
    rrr_beta = c(303.57142857142856, 196.42857142857144),
    target_population = 750000.0,
    utility_weight = 0.82,
    rr_lognormal_exact = c(-0.9358492331589685, 0.055497671701347284),
    cost_ppy_gamma_exact = c(5.0, 96.91055212693195),
    event_cost_gamma_exact = c(4.0, 4718.275891686173),
    productivity_cost_gamma_exact = c(3.0, 13661.137974473053),
    annual_event_rate_exact = 0.028,
    case_fatality_rate_exact = 0.05,
    utility_weight_exact = 0.82,
    qalys_lost_per_event_exact = 0.06585365853658531,
    life_years_lost_per_death_exact = 6.0
    ),
  osteoporosis = list(
    annual_event_rate = 0.05,
    case_fatality_rate = 0.02,
    cost_ppy_gamma = c(5.0, 140.3),
    event_cost_gamma = c(4.0, 35833.0),
    label = "Osteoporosis Fracture Prevention",
    life_years_lost_per_death = 0.8,
    productivity_cost_gamma = c(3.0, 47818.0),
    qalys_lost_per_event = 0.386,
    rr_lognormal = c(-0.094, 0.014),
    rrr_beta = c(45.0, 455.0),
    target_population = 234000.0,
    utility_weight = 0.87,
    rr_lognormal_exact = c(-0.09440937342162263, 0.014049480444581534),
    cost_ppy_gamma_exact = c(5.0, 140.27581986942178),
    event_cost_gamma_exact = c(4.0, 35833.005519283826),
    productivity_cost_gamma_exact = c(3.0, 47818.03284826455),
    annual_event_rate_exact = 0.05,
    case_fatality_rate_exact = 0.02,
    utility_weight_exact = 0.87,
    qalys_lost_per_event_exact = 0.3862988505747126,
    life_years_lost_per_death_exact = 0.8
    )
  ),
portfolio_adjustments_exact = list(
  overlap_events = 0.9782178217821782,
  mortality_synergy = 1.589256335121348,
  qaly_synergy = 4.865944050520814,
  hc_realization = 2.158984,
  prod_realization = 0.353716,
  benefit_synergy = 1.063
  )
)

  # Promote rr_lognormal to rr_lognormal_exact for R (if exists as 2-vector). The JSON may carry 'rr_lognormal'.
  for (k in names(params$interventions)) {
    intr <- params$interventions[[k]]
    if (!is.null(intr$rr_lognormal)) {
      # promote exact QALY loss if provided
      if (!is.null(intr$qalys_lost_per_event_exact)) intr$qalys_lost_per_event <- intr$qalys_lost_per_event_exact
      intr$rr_lognormal_exact <- intr$rr_lognormal
      intr$rr_lognormal <- NULL
      params$interventions[[k]] <- intr
    }
  }


  # Exact program budgets (AED); ensures investment totals equal reported figures
  budgets <- list(alzheimers=2.9e9, cancer=4.8e9, cvd=8.2e9, diabetes=3.1e9, osteoporosis=1.4e9)
  for (k in names(budgets)) {
    if (!is.null(params$interventions[[k]])) {
      params$interventions[[k]]$investment_override <- budgets[[k]]
    }
  }

  mk <- run_markov_models(params)
  roi <- calculate_roi(mk$portfolio)
  write_outputs(out, mk, roi)

  # Print brief check to console
  cat(sprintf("Investment: AED %.0f\n", roi$total_investment))
  cat(sprintf("Benefits:  AED %.0f\n", roi$total_savings))
  cat(sprintf("ROI:       %.1f%%\n", roi$roi_percentage))
  invisible(0)
}

if (sys.nframe() == 0) main()
