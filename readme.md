# INFEST
## Overview
INFEST for k**IN**ematic o**F** l**ES**ion developmen**T**. This plugin was used to compute the kinematic of lesion caused by the necrotrophic fungus _Sclerotinia sclerotiorum_. Feel free to use it.
For academics used please cite :

Barbacci, A., Navaud, O., Mbengue, M., Vincent, R., Barascud, M., Aline, L., Raffaele, S., n.d. **Rapid identification of an Arabidopsis NLR gene conferring susceptibility to Sclerotinia sclerotiorum using real-time automated phenotyping**. Rev.


### command line :

infest.py path_containing_images start stop
- path_containing_images the full path of the directory containing pictures (e.g. /home/foo/bar/)
- start (optional, default 0) an integer corresponding to the first image to consider.
- stop (optional, default max(image_name)) an integer corresponding to the last image to consider.

### Examples
- infest.py /home/foo/bar/ 0 250
- infest.py /home/foo/bar/ 0
- infest.py /home/foo/bar/

Tested with ubuntu 18.10
### Latest news

Please cite ...
# Getting started
# Installation instructions

# Tuto
All data are in the data_tuto/ directory

## Prerequist
Name of images 1.jpg to N.jpg
Layout file grid_layout.layout in the directory
Layout file must is composed by 'name'<tab>'ymin','xmin','ymax','xmax'
## Command line prototype
infest.py path_containing_images start stop


![Kinematic of lesion development for the leaf 'Col-0_154'](./data_tuto/results/results.jpeg)
