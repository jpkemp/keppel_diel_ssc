import pandas as pd
from numpy import NaN, log
from scipy.stats import anderson
from rpy2.robjects import r as rcode
from tools.gams.gam_link import GamLink
from backend.diel_vector import benthic_site_map, soundscape_sites

def get_proportional_habitat_cover() -> pd.DataFrame:
    '''loads the habitat data from file

    returns: dataframe with habitat information
    '''
    merge = ["A", "AB", "OT", "SC", "SP"]
    col = "point_human_group_code"
    raw_benthic = pd.read_excel('data/benthic_wcp.xlsx')
    groups = raw_benthic.groupby(['site_name', 'survey_title'])
    df = groups[col].value_counts(normalize=True).reset_index()
    date_map = {"Feb": "02", "Nov": "11", "Oct": "10", "Tiles": '02', 'Hydrophone': '10', 'February': "02", "October": "10", "November": "11"}
    df["month"] = df["survey_title"].apply(lambda x: date_map[x.split(' ')[0]])
    feb = df[df["month"] == "02"]
    pivoted = feb.pivot_table('proportion', ['site_name', 'month'], col).reset_index().fillna(0)
    habitat_cols = pivoted.drop(['site_name', 'month'], axis=1)
    habitat_cols.index = pivoted["site_name"].apply(lambda x: benthic_site_map[x])
    habitat_cols["O"] = habitat_cols[merge].sum(axis=1)

    return habitat_cols.drop(merge, axis=1).map(lambda x: 1e-5 if not x else x)

def get_habitat_log_ratios(): # this is not generalisable because dataset knowledge is used
    habitat_data = get_proportional_habitat_cover()
    baseline_col = 'O'
    hab_cols = habitat_data.columns.drop(baseline_col)
    ratios = habitat_data[hab_cols].div(habitat_data[baseline_col], axis=0)
    log_ratios = ratios.map(lambda x: log(x))

    return log_ratios

def create_settlement_data():
    settlement = [21.75, 49.41667, 14.83333, 20.08333, 31.25, 3.583333, 90.91667, 12.72727, 7.5, 25.25, NaN] # %s?
    settlement_order = ["Mazie site 2", "Mazie Taylors", "Shelving site 1", "Middle Taylor", "Monkey Taylor", "Halfway", "Miall Taylor", "Clam Bay", "Humpy", "Home Cathie", "Home Taylor"]
    settlement = pd.Series(settlement) / 100
    settlement.index = settlement_order

    return settlement.sort_index()

def load_pca_points(band):
    return pd.read_csv(f"output/pca_points_{band}_combined.csv").drop("Unnamed: 0", axis=1)

def get_measurement_error(pcas:pd.DataFrame):
    groups = pcas.groupby('Site')
    stds = groups.std()
    means = groups.mean()
    dfs = []
    for dim in ["PCA1","PCA2"]:
        # ses_dim = ses[dim]
        out = pd.concat([means[dim], stds[dim]], axis=1).reset_index()
        out.columns = ["site", dim, f"sd{dim}"]
        dfs.append(out)

    ret = pd.merge(*dfs, on='site')
    ret.index = ret['site'].apply(lambda x: soundscape_sites[x])
    ret.index.name = 'site_name'

    return ret.drop('site', axis=1)

def generate_effects_plot(r_link:GamLink, model, effects, title, plot_points=True):
    filename = f"output/{title}"
    theme = r_link.gg.theme_minimal(base_size=36, base_line_size=0.5, base_rect_size=0.5)
    plt = r_link.base.plot(model, ask=False, plot=False, theme=theme)
    for i in range(len(plt)):
        r_link.gr_plot(f"{filename}_base_{i}.png", plt[i])

    obj = r_link.base.plot(effects, ask=False, plot=False, points=plot_points, theme=theme)
    for i in range(len(obj)):
        r_link.gr_plot(f"{filename}_cond_effects_{i}.png", obj[i])

def generate_pp_checks(r_link:GamLink, model, title, resps):
    filename = f"output/{title}"
    for resp in resps:
        dens = glms.pp_check(model, resp) # should potentially use full pca dataset instead of mean points
        r_link.gr_plot(f"{filename}_density_overlay_{resp}.png", dens)

        scat = glms.pp_check(model, resp, "scatter_avg")
        r_link.gr_plot(f"{filename}_scatter_avg_{resp}.png", scat)

def hypothesis_checks(glms, model, responses, effects, clas="bsp"):
    passing = []
    for resp in responses:
        for eff in effects:
            formatted_hyp = f"{resp}_mi{eff} = 0"
            starred = glms.check_hypothesis(model, formatted_hyp, clas)
            if starred[0]:
                passing.append((resp, eff))

    return passing

def check_normality(data, effects):
    for effect in effects:
        assert anderson(data[effect]).fit_result.success

if __name__ == "__main__":
    r_link = GamLink()
    glms = r_link.load_src("tools/gams/brms_models.R")
    settlement_data = create_settlement_data()
    lrs = get_habitat_log_ratios()
    priors = rcode("c(brms::set_prior('normal(0,10)', class='b', resp = c('HC', 'MA')))")
    effects = ["PCA1", "PCA2"]
    responses = ["HC", "MA"]
    for band in ["broad", "fish", "invertebrate"]:
        pca_points = load_pca_points(band)
        check_normality(pca_points, effects)
        me = get_measurement_error(pca_points)
        data = lrs.join(me)
        rdf = r_link.convert_to_rdf(data)
        formula_str = f"brms::bf(brms::mvbind({','.join(lrs.columns)}) ~ 0 + Intercept + mi(PCA1) + mi(PCA2))"
        formula_str += f"+ brms::bf(PCA1 | mi(sdPCA1) ~ 0 + Intercept)"
        formula_str += f"+ brms::bf(PCA2 | mi(sdPCA2) ~ 0 + Intercept)"
        formula_str += "+ brms::set_rescor(FALSE)"
        formula = rcode(formula_str)
        family = "gaussian"
        model = glms.generate_brms_model(rdf, formula, family, f"output/{band}_mi_model.RData", prior=priors)
        for response in responses:
            effects = glms.conditional_effects(model, response)
            generate_effects_plot(r_link, model, effects, f"{band}_{response}_mv")
            generate_pp_checks(r_link, model, f"{band}_{response}_mv", responses)

        usable_predictors = hypothesis_checks(glms, model, responses, effects)
        tbl = pd.DataFrame(usable_predictors)
        tbl.to_csv(f"output/{band}_mi_starred.csv")
