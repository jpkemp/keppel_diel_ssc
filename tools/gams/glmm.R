between_within_effects <- function(data, name, formula){
  output_path <- paste("output/glm_data_", name, ".RData", sep='')
  save(data, file = output_path)
  model <- glmmTMB::glmmTMB(
    as.formula(formula),
    data = data,
    family = gaussian(),
    dispformula = ~1,
    control = glmmTMB::glmmTMBControl(optCtrl = list(iter.max = 1e3))
  )

  vc <- glmmTMB::VarCorr(model)
  between_sd <- as.numeric(vc$cond$soundtrap[1])
  within_sd <- glmmTMB::sigma(model)
  output_path <- paste("output/glm_", name, ".RData", sep='')
  save(model, file = output_path)

  return(c(within_sd, between_sd))
}
