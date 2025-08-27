partial_metrics = ['acorr3', 'B', 'lprms', 'lppk']
full_metrics = partial_metrics + ['D'] # dissimilarity has a different number of points to the others; separation can be useful

soundscape_sites = { # hydrophone serials to site names
    5072: 'Mazie 5072',
    5073: 'Mazie 5073',
    6376: 'Mazie site 2',
    7252: 'Shelving site 1',
    7255: 'Monkey Taylor',
    7257: 'Miall Taylor',
    7259: 'Humpy',
    7262: 'Home Taylor',
    6407: 'Mazie Taylors',
    7254: 'Middle Taylor',
    7256: 'Halfway',
    7258: 'Clam Bay',
    7261: 'Home Cathie'
}

benthic_site_map = { # site name translations for the benthic data
    'Clam 8': "Clam Bay",
    'Halfway 3': "Halfway",
    'Home_Cathie': "Home Cathie",
    'Home_Taylor': "Home Taylor",
    'Humpy 1': "Humpy",
    'Mazie 2': "Mazie site 2",
    'Mazie_Taylor': "Mazie Taylors",
    'Miall': "Miall Taylor",
    'Middle': "Middle Taylor",
    'Monkey': "Monkey Taylor",
    'Shelving 1': "Shelving site 1"
}

metric_full_names = { # SSC translations from shorthand to full metric names
    'acorr3': 'periodicity',
    'B': 'kurtosis',
    'D': 'dissimilarity',
    'lppk': 'peak sound level',
    'lprms': 'RMS sound level'
}
