from tools.definitions import full_metrics
from rpy2.rinterface_lib.embedded import RRuntimeError

single_soundtrap:int = 0


def normalise(vector):
    high = vector.max()
    low = vector.min()
    def n(x):
        return (x - low) / (high - low)

    return vector.apply(n)

continuous = ['tide_height', 'temperature']
factors = []
circular = ["scaled_day", "phase"]
re = ['soundtrap']
required_cols = full_metrics + continuous + factors + circular + re
data_types = {x: float for x in full_metrics + continuous + circular}
predictors = continuous + circular

def create_gams(r_link, name, sscodes):
    data = sscodes[name]
    for col, typ in data_types.items():
        data[col] = data[col].astype(typ)

    for col in ["lprms", "lppk"]: # can't GAM with negative values in tweedie family.
        data[col] = normalise(data[col])

    data = data[required_cols].dropna()
    rdf = r_link.convert_to_rdf(data)
    r_link.change_col_to_factor(rdf, 'soundtrap')

    path = f"output/rdf_{name}.rda"
    r_link.r_src.save_object(rdf, str(path))
    for metric in full_metrics:
        extra_preds = predictors
        try:
            r_link.fss_gam(rdf, metric, extra_preds, factors, circular, re, f"{name}_{metric}")
        except RRuntimeError as e:
            print("Runtime error")
            print(e)
            continue
