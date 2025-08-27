import re
from collections import Counter
from functools import partial
import pandas as pd
from sklearn.metrics import f1_score
from sklearn.tree import DecisionTreeClassifier, export_text
from tools.definitions import partial_metrics, soundscape_sites, benthic_site_map
from tools.ml import pca_nd
from matplotlib.cm import tab20
from tools.plots import Plots

def set_x_markers(scale, fig, ax, lgd=None):
    ticks = [0, 5, 10, 15, 20]
    tick_labs = ["Solar midnight", "Sunrise", "Solar midday", "Sunset", "Solar midnight"]
    ax.set_xticks(ticks, labels=tick_labs)
    if scale is not None:
        ax.set_ylim(scale[0], scale[1])

    return fig, ax, lgd

def plot_day_percentiles(site_data, metrics, fltr, site, xcallback, scale):
    grouping_var = 'scaled_group'
    site_data = site_data.sort_values(grouping_var)
    group = site_data.groupby(grouping_var)
    for metric in metrics:
        callback = partial(xcallback, scale[metric])
        metric_results = {0.05: None, 0.1: None, 0.25: None, 0.5: None, 0.75: None, 0.9: None, 0.95: None, "Mean": None}
        for quant in [x for x in metric_results if isinstance(x, float)]:
            q = group[metric].quantile(quant)
            vals = q.values.tolist()
            metric_results[quant] = vals

        mn = group[metric].mean().values.tolist()
        metric_results["Mean"] = mn

        x = sorted(site_data[grouping_var].unique())
        percentiles = []
        for key in metric_results.keys():
            try:
                ans = f"{100 * float(key)}%"
                percentiles.append(ans)
            except ValueError:
                percentiles.append("Mean")


        Plots.multiline_scatter_plot(x, list(metric_results.values()), ("Hours from closest transition", metric),
            percentiles, f"{fltr}_{metric}_{site}", "", callback=callback, legend_title="Percentiles")

def get_habitat_cover():
    col = "point_human_group_code"
    raw_benthic = pd.read_excel('data/benthic_wcp.xlsx')
    groups = raw_benthic.groupby(['site_name', 'survey_title'])
    df = groups[col].value_counts(normalize=True).reset_index()
    date_map = {"Feb": "02", "Nov": "11", "Oct": "10", "Tiles": '02', 'Hydrophone': '10', 'February': "02", "October": "10", "November": "11"}
    df["month"] = df["survey_title"].apply(lambda x: date_map[x.split(' ')[0]])
    df = df.pivot_table('proportion', ['site_name', 'month'], col).reset_index().fillna(0)
    df = df[df["month"] == "02"]
    habitat_pca, _, _ = pca_nd(df.drop(['site_name', 'month'], axis=1), 1)
    habitat = pd.Series(habitat_pca.squeeze())
    habitat.index = df["site_name"].apply(lambda x: benthic_site_map[x])
    habitat.name = "algae_cover"

    return habitat

def get_daily_metrics(data, metrics):
    daily_metrics = {metric: [] for metric in metrics}
    labels = {metric: [] for metric in metrics}
    data["day"] = data["datetime"].dt.floor('d')
    days = data.groupby(['day', 'soundtrap'])
    for day, day_data in days:
        group = day_data.groupby('scaled_group')
        for metric in metrics:
            med = group[metric].quantile(0.5)
            if len(med) != 20:
                continue
            day_results = med.sort_index().values.tolist()
            daily_metrics[metric].append(day_results)
            labels[metric].append(day_data['soundtrap'].unique()[0])

    cols = {metric: [f"{metric}_{x}" for x in range(20)] for metric in daily_metrics}
    daily_metrics = {k: pd.DataFrame(v, columns=cols[k]) for k, v in daily_metrics.items()}
    labels = {k: pd.Series(v) for k, v in labels.items()}

    return daily_metrics, labels

def assess_df(df, labels, splitter, name):
    split = splitter.split(df, labels)
    for train_inds, test_inds in split:
        tree = DecisionTreeClassifier()
        tree.fit(df.iloc[train_inds], labels.iloc[train_inds])
        preds = tree.predict(df.iloc[test_inds])
        results = pd.DataFrame([labels.iloc[test_inds].values, preds]).transpose()
        results.columns = ["actual", "predicted"]
        f1s = [f1_score(results['actual'], results['predicted'], average=metric) for metric in ['micro', 'macro', 'weighted']]
        truth = results.apply(lambda x: x["actual"] == x["predicted"], axis=1)
        acc = truth.sum() / len(truth)
        f1s.append(acc)

        rules = export_text(tree, feature_names=df.columns)
        formatted_rules = rules.split('\n')
        n_rules = len(formatted_rules)
        rules_export = re.findall(r"---\s(.+)\s[><=].*\n", rules)
        rule_locations = set(rules_export)
        n_rule_locations = len(rule_locations)
        index_use = [x.split('_')[0] for x in rules_export]
        index_counts = Counter(index_use)
        time_use = [x.split('_')[1] for x in rules_export]
        time_counts = Counter(time_use)
        write_rules(rules, name)

        return f1s, (name, n_rules, n_rule_locations), index_counts, time_counts

def write_rules(rules, name):
    path = f"output/rules_{name}.txt"
    with open(path, 'w') as f:
        f.write(rules)

def pca_plot(data, labels, name, color_by_site=True):
    normalized_df=(data - data.min()) / (data.max() - data.min()).astype(float)
    pca, weights, variance = pca_nd(normalized_df, 2)
    print(f"Variance for {name}: {variance}")
    pca = pd.DataFrame(pca)
    weights = pd.DataFrame(weights)
    weights.to_csv(f"output/pca_weights_{name}.csv")
    group_vals = labels.astype("category")
    cat_codes = group_vals.cat.codes
    nunique = group_vals.nunique()
    if color_by_site:
        colors = pd.Series([tab20(float(x)/nunique) for x in cat_codes])
        cbars = None
    else:
        habitat = get_habitat_cover()
        assert min(habitat) >= -1 and min(habitat) < 0 and max(habitat) > 0 and max(habitat) <= 1
        colors = labels.apply(lambda x: Plots.blue_fader(habitat[soundscape_sites[x]]))
        col_example_mixes = [0.05 * x for x in range(-20, 21)]
        index_vals = [x / 2 + 0.5 for x in col_example_mixes]
        cbars = []
        examples = [(index_vals[i], Plots.blue_fader(x)) for i, x in enumerate(col_example_mixes)]
        cbars.append(tuple([habitat, examples, "Habitat PCA value"]))

    full_labels = [soundscape_sites[x] for x in labels]
    fig = Plots.scatter_plot(pca[0], pca[1], ("PCA Dim 0", "PCA Dim 1"), f"pca_{name}", legend=full_labels, color=colors, colbar=cbars)

    return fig

def write_rule_counts(rules):
    fname = f"output/n_rules.csv"
    with open(fname, 'w+') as f:
        cols = 'Dataset,Band,Metric,Rules,Locations\n'
        f.write(cols)
        for name, n_rules, n_locations in rules:
            formatted_name = name.replace('_', ',')
            ln = f"{formatted_name},{n_rules},{n_locations}\n"
            f.write(ln)

def write_metric_rule_counts(typ, counts):
    fname = f"data/{typ}_counts.csv"
    usable = [x for x in counts if "combined" in x[0]]
    columns = sorted(partial_metrics + ['D']) if typ == "index" else [str(x) for x in range(20)]
    with open(fname, 'w+') as f:
        column_ln = ','.join(columns)
        f.write(f",{column_ln}\n")
        for model, vals in usable:
            formatted_vals = ','.join([str(vals[x]) for x in columns])
            ln = f"{model},{formatted_vals}\n"
            f.write(ln)

def get_site_metrics(data, fltr, x_callback, axis_ranges):
    for site, site_data in data.groupby('soundtrap'):
        plot_day_percentiles(site_data, partial_metrics, fltr, site, x_callback, axis_ranges)
        par_data = site_data.dropna()
        plot_day_percentiles(par_data, ['D'], fltr, site, x_callback, axis_ranges)

def get_dailies_for_all_metrics(data):
    daily_metrics, labels = get_daily_metrics(data, partial_metrics)
    partial_data = data[~data['D'].isna()]
    d_metrics, d_labels = get_daily_metrics(partial_data, ['D'])
    daily_metrics['D'] = d_metrics['D']
    labels['D'] = d_labels['D']

    return daily_metrics, labels
