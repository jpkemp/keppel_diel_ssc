import pandas as pd
from numpy import NaN, log
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

    return habitat_cols.drop(merge, axis=1).map(lambda x: 1e5 if not x else x)

def get_habitat_log_ratios(): # this is not generalisable because dataset knowledge is used
    habitat_data = get_proportional_habitat_cover()
    baseline_col = 'O'
    hab_cols = habitat_data.columns.drop(baseline_col)
    ratios = habitat_data[hab_cols].div(habitat_data[baseline_col], axis=0)
    log_ratios = ratios.map(lambda x: log(x))

    return log_ratios

def construct_df(r_link:GamLink, pcas, habitat_data):

    rdf = r_link.convert_to_rdf(data)

    return rdf


def create_settlement_data(add_to_zero=True):
    settlement = [21.75, 49.41667, 14.83333, 20.08333, 31.25, 3.583333, 90.91667, 12.72727, 7.5, 25.25, NaN] # %s?
    settlement_order = ["Mazie site 2", "Mazie Taylors", "Shelving site 1", "Middle Taylor", "Monkey Taylor", "Halfway", "Miall Taylor", "Clam Bay", "Humpy", "Home Cathie", "Home Taylor"]
    settlement = pd.Series(settlement) / 100
    settlement.index = settlement_order

    return settlement.sort_index()

def load_pca_points(band):
    return pd.read_csv(f"output/pca_points_{band}_combined.csv").drop("Unnamed: 0", axis=1)

def get_measurement_error(pcas:pd.DataFrame):
    groups = pcas.groupby('Site')
    ses =  groups.sem()
    stds = groups.std()
    means = groups.mean()
    dfs = []
    for dim in ["PCA1","PCA2"]:
        # ses_dim = ses[dim]
        ses_dim = stds[dim]
        means_dim = means[dim]
        std = pcas[dim].std()
        obs = (means_dim - pcas[dim].mean()) / std
        sd = ses_dim / std
        out = pd.concat([obs, sd], axis=1).reset_index()
        out.columns = ["site", f"obs{dim}", f"sd{dim}"]
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

if __name__ == "__main__":
    r_link = GamLink()
    glms = r_link.load_src("tools/gams/brms_models.R")
    settlement_data = create_settlement_data()
    lrs = get_habitat_log_ratios()
    for band in ["broad", "fish", "invertebrate"]:
        pca_points = load_pca_points(band)
        me = get_measurement_error(pca_points)
        data = lrs.join(me)
        rdf = r_link.convert_to_rdf(data)
        formula_str = f"brms::bf(brms::mvbind({','.join(lrs.columns)}) ~ 0 + Intercept + mi(obsPCA1) + mi(obsPCA2))"
        formula_str += f"+ brms::bf(obsPCA1 | mi(sdPCA1) ~ 0 + Intercept)"
        formula_str += f"+ brms::bf(obsPCA2 | mi(sdPCA2) ~ 0 + Intercept)"
        formula_str += "+ brms::set_rescor(FALSE)"
        formula = rcode(formula_str)
        family = "gaussian"
        model = glms.generate_brms_model(rdf, formula, family, f"output/{band}_mi_model.RData")
        effects = glms.conditional_effects(model)
        generate_effects_plot(r_link, model, effects, f"{band}_mv")

