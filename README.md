# Ecoacoustic index overlap and diel representation in the Keppel Isles
This repository stores the code to reproduce an ecoacoustic analysis conducted on 11 sites in the Keppel Isles, Australia.

The main code and results are presented in Jupyter notebooks. There are several parts to the study.

The file 'environmental factors.ipynb' runs Generalised Additive Models with tide height, moon phase, scaled time of day, and temperature as predictors for each metric in the Soundscape Code.

The files 'eda.ipynb' and 'clustering.ipynb' display box plots for each metric and PCA plots for the dimensionally-reduced metrics respectively, illustrating the amount of overlap between each site.

The file 'diel_vector.ipynb' introduces a diel representation of the data, and runs decision trees for site classification and PCA for dimension reduction, displaying the degree of separation possible with this representation.

The 'data_processing' folder contains scripts to convert the original sound recordings into soundscape code metrics, and combinations with other data such as the temperature and tide heights.