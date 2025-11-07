get_family <- function(family, link = "logit") {
  if (family == "gaussian") return(stats::gaussian())
  if (family == "bernoulli") return(brms::bernoulli(link = link))
  if (family == "binomial") return(stats::binomial())
  if (family == "gamma") return(stats::Gamma(link = log))
  if (family == "beta") return(brms::Beta())
  if (family == "logit_normal") return(brms::logistic_normal())
  if (family == "zero_beta") return(brms::zero_inflated_beta())
}

generate_brms_model <- function(data, formula, family, file_path, iter = 3000,
                                warmup = 2000, cores = 5, chains = 5, prior=NULL) {
  save(data, file=file_path)
  family_inst <- get_family(family)
  # formula <- as.formula(formula)
  model <- brms::brm(formula,
    data = data,
    prior=prior,
    family = family_inst,
    iter = iter,
    warmup = warmup,
    cores = cores,
    chains = chains,
    init = 0,
  )

  save(model, file=file_path)
  return(model)
}

between_within_effects <- function(data, name, formula) {
  path <- paste("output/brms_", name, "_model.RData")
  brms_model <- generate_brms_model(data, formula, "gaussian", path)
  post <- brms::posterior_summary(brms_model)

  between_sd <- post["sd_id__Intercept", c("Estimate", "Q2.5", "Q97.5")]^2
  within_sd <- post["sigma", c("Estimate", "Q2.5", "Q97.5")]^2

  ret <- c(within_sd, between_sd)

  return(ret)
}

conditional_effects <- function(model, resp=NULL) {
  effects <- brms::conditional_effects(model, resp=resp)
  return(effects)
}


pp_check <- function(model, resp, type="dens_overlay") {
  return(brms::pp_check(model, type=type, resp=resp))
}

check_hypothesis <- function(model, hypothesis, class = "b") {
  hyp <- brms::hypothesis(model, hypothesis, class = class)
  starred <- hyp$hypothesis$Star
  return(starred)
}