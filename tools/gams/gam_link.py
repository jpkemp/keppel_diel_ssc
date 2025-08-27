from pathlib import Path
from rpy2.robjects import r as rcode
from .r_plotter import rPlotter

class GamLink(rPlotter):
    def __init__(self):
        super().__init__()
        path = Path(__file__).parent / "gam_models.R"
        self.gam = self.load_src(path)
        self.output_path = "output"
        self.log = print

    def _process_var_list(self, vars, r_str):
        if not vars:
            return ""

        joined_vars = ','.join(f'"{x}"' for x in vars)

        return f"{r_str}=c({joined_vars}),"

    def generate_gam_model_code(self, output_var, predictors, factor_vars, cyclic_vars, random_effects):
        form_re = " + " + " + ".join([f"s({x}, bs='re', k=5)" for x in random_effects]) if random_effects else ""
        formula_string = f"{output_var} ~ s({predictors[0]}, bs='cr', k=5)" + form_re
        n_predictors = min(len(predictors) + len(factor_vars), 5)
        predictors = self._process_var_list(predictors, "pred.vars.cont")
        factor_vars = self._process_var_list(factor_vars, "pred.vars.fact")
        cyclic_vars = self._process_var_list(cyclic_vars, "cyclic.vars")
        random_effects = self._process_var_list(random_effects, "null.terms")
        return(f"Model1 <- mgcv::gam({formula_string}, family=mgcv::tw(), data=use.dat)\n"
                "model.set <- FSSgam::generate.model.set(use.dat=use.dat,"
                "test.fit=Model1,"
                f"{predictors}"
                f"max.predictors={n_predictors},"
                f"{factor_vars}"
                f"{cyclic_vars}"
                f"{random_effects}"
                "k=5,"
                "factor.smooth.interactions=T,"
                "smooth.smooth.interactions=T)"
        )

    def fss_gam(self, data, output_var, continuous_vars, factor_vars, cyclic_vars, random_effects, name):
        self.gam.assign_data_to_parent_env(data)
        gam_code = self.generate_gam_model_code(output_var, continuous_vars, factor_vars, cyclic_vars, random_effects)
        self.log(gam_code)
        rcode(gam_code)
        for factor in factor_vars:
            self.change_col_to_factor(data, factor)

        self.gam.soundtrap_model_set(self.output_path, name)
