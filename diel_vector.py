import re
from collections import Counter
from dataclasses import dataclass
from functools import partial
from itertools import permutations
from overrides import overrides
import matplotlib.pyplot as plt
import pandas as pd
import pygraphviz as pgv
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay, f1_score
from sklearn.model_selection import StratifiedShuffleSplit
from sklearn.tree import DecisionTreeClassifier, export_text
from tools.process_dataframe import partial_metrics, soundscape_sites, benthic_site_map, blue_fader
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

def get_metric_results(site_data, metrics, fltr, site, xcallback, scale):
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

def get_daily_metrics(self, data, metrics):
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
    path = f"data/rules_{name}.txt"
    with open(path, 'w') as f:
        f.write(rules)

def pca_plot(data, labels, name):
    normalized_df=(data - data.min()) / (data.max() - data.min()).astype(float)
    pca = pd.DataFrame(pca_nd(normalized_df, 2))
    group_vals = labels.astype("category")
    cat_codes = group_vals.cat.codes
    nunique = group_vals.nunique()
    colors = pd.Series([tab20(float(x)/nunique) for x in cat_codes])
    cbars = None
    full_labels = [soundscape_sites[x] for x in labels]
    Plots.scatter_plot(pca[0], pca[1], ("PCA Dim 0", "PCA Dim 1"), f"pca_{name}", legend=full_labels, color=colors, colbar=cbars)

def write_all_rules(rules):
    fname = f"data/n_rules.csv"
    with open(fname, 'w+') as f:
        cols = 'Dataset,Band,Metric,Rules,Locations\n'
        f.write(cols)
        for name, n_rules, n_locations in rules:
            formatted_name = name.replace('_', ',')
            ln = f"{formatted_name},{n_rules},{n_locations}\n"
            f.write(ln)

def write_counts_data(typ, counts):
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

def process_sscodes(sscodes, n_day_groups):
    test_proportion:float = 0.3
    x_callback = set_x_markers
    n_rules_data =[]
    index_counts_data = []
    time_counts_data = []
    for fltr, data in sscodes.items():
        for metric in partial_metrics:
            data[metric] = data[metric].astype(float)

        data['D'] = data['D'].astype(float)
        data["scaled_group"] = data["scaled_day"].apply(lambda x: int(n_day_groups*x/25))
        ranges = {x: None for x in partial_metrics + ['D']}
        for site, site_data in data.groupby('soundtrap'):
            get_metric_results(site_data, partial_metrics, fltr, site, x_callback, ranges)
            par_data = site_data.dropna()
            get_metric_results(par_data, ['D'], fltr, site, x_callback, ranges)

        daily_metrics, labels = get_daily_metrics(data, partial_metrics)
        partial_data = data[~data['D'].isna()]
        d_metrics, d_labels = get_daily_metrics(partial_data, ['D'])
        daily_metrics['D'] = d_metrics['D']
        labels['D'] = d_labels['D']
        splitter = StratifiedShuffleSplit(test_size=test_proportion, n_splits=1)
        accs = []
        for metric, metric_values in daily_metrics.items():
            f1s, n_rules, counts, tcounts = assess_df(metric_values, labels[metric], splitter, f"{fltr}_{metric}")
            accs.append(f1s)
            n_rules_data.append(n_rules)
            metric_output_name = f"{fltr}_{metric}"
            index_counts_data.append((metric_output_name, counts))
            time_counts_data.append((metric_output_name, tcounts))
            self.log(f"F1 scores for {data_name} {metric} in {fltr}: {f1s}")
            pca_plot(daily_metrics[metric], labels[metric], metric_output_name)

        order = ['F1 micro', 'F1 macro', 'F1 weighted', 'Accuracy']
        combined_metrics = pd.concat(daily_metrics.values(), axis=1)
        pca_plot(combined_metrics, labels["lprms"], f"{fltr}_combined")
        pca_plot(combined_metrics, labels["lprms"], f"{fltr}_algae_combined", False)
        f1s, n_rules, counts, tcounts = assess_df(combined_metrics, labels['lprms'], splitter, f"{fltr}_combined")
        accs.append(f1s)
        n_rules_data.append(n_rules)
        index_counts_data.append((f"{fltr}_combined", counts))
        time_counts_data.append((f"{fltr}_combined", tcounts))
        tests = list(daily_metrics.keys()) + ["Combined"]
        for i, v in enumerate(list(zip(*accs))):
            Plots.categorical_bar_plot(tests, v, "", f"result_{fltr}_{order[i].replace(' ', '_')}_plot_gap", ("Metric", "F1 Score"), y_limits=(0, 1))

    write_all_rules(n_rules_data)
    for typ, counts_data in [("index", index_counts_data), ("time", time_counts_data)]:
        write_counts_data(typ, counts_data)