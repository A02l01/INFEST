# INFEST
## Overview
INFEST for k**IN**ematic o**F** l**ES**ion developmen**T**. This plugin was used to compute the kinematic of lesion caused by the necrotrophic fungus _Sclerotinia sclerotiorum_. INFEST was developed for QIP (quantitative immunity in plant) @ LIPM (Lab of plant microbes interaction) in Toulouse by Adelin Barbacci. Feel free to use it.


> **For academics used please cite :**
>
>Barbacci, A., Navaud, O., Mbengue, M., Vincent, R., Barascud, M., Aline, L., Raffaele, S., n.d. **Rapid identification of an Arabidopsis NLR gene conferring susceptibility to Sclerotinia sclerotiorum using real-time automated phenotyping**. Rev.



![Kinematic of lesion development for the leaf 'Col-0_154'](https://github.com/A02l01/d/blob/master/d/inf.gif)


### command line :

`python infest.py path_containing_images start stop`
- `path_containing_images` the full path of the directory containing pictures (e.g. /home/foo/bar/). Pictures must be named by an integer corresponding to time (e.g. `1.jpg`,`100.jpg`)
- `start` (optional, default 0) an integer corresponding to the first image to consider.
- `stop` (optional, default max(image_name)) an integer corresponding to the last image to consider.

**output**
> `analyse.txt` file created in the  `path_containing_images` directory containing 3 columns: the **Id** of leaf, the **time** extracted from pictures name and the size of the **Lesion**

### Examples
`infest.py /home/foo/bar/ 0 250`

`infest.py /home/foo/bar/ 0`

`infest.py /home/foo/bar/`


### To go further
>To compute the growth rate associated to kinematic of lesion development we advice to use the 'segmented' R library after a log transform of the curve obtained with INFEST.
### Latest news
- Version 1 available

# Getting started
## Details
This version has been developed and tested under ubuntu 18.10 with python 2.7. The dependancies are:
- matplotlib==2.2.4
- numpy==1.16.5
- scikit-image==0.14.5

## Prerequists
Having python and conda install on your machine.
- For linux install please see: [here](https://docs.conda.io/projects/conda/en/latest/user-guide/install/linux.html)
- For other systems: [here](https://docs.conda.io/projects/conda/en/latest/user-guide/install/#system-requirements)
## Installation instructions
- Download the python sources:
- wget
- Creation of a conda environment

`conda env create -n INFEST -f env_Infest.yml`

`conda activate INFEST`

`python infest.py path_to_picture`



# Tutorial
In this short tutorial we will use **INFEST** to compute the kinematic of lesion development of a single detached leaf of _Arabidopsis thaliana_ coined 'Col-0_154'.

All data are in the `data_tuto/` directory

![Col-0_154 leaf](https://github.com/A02l01/tuto/blob/master/data_tuto/pictures/grid_layout/panel.jpg)

Other kinematics can be computed by adding bounding boxes of leaves in the `grid_layout.layout` file.

## creation of the layout file
- Downloading pictures
- creation of the `grid_layout/` subdirectory in the picture directory. here creation of `./Image_tuto/pictures/grid_layout/`

- creation of the `grid_layout.layout` file in `./Image_tuto/pictures/grid_layout/` directory. We used [ImageJ](https://imagej.nih.gov/ij/download.html) to obtain the coordinates of the bounding rectangle. We add the single line
`Col-0_154       1410    2574    1497    2721`
to `./Image_tuto/pictures/grid_layout/grid_layout.Layout`
with `Col-0_154` the **Id** of the leaf, `1410` **ymin** of the rectangle, `2574` **xmin** of the rectangle, `1497` **ymax** of the rectangle, `2721` **xmax** of the rectangle.
>**Items are separeted by a tabulation**.





## Prerequist
Name of images 1.jpg to N.jpg
Layout file grid_layout.layout in the directory
Layout file must is composed by 'name'<tab>'ymin','xmin','ymax','xmax'
## Command line prototype
infest.py path_containing_images start stop


![Kinematic of lesion development for the leaf 'Col-0_154'](https://github.com/A02l01/tuto/blob/master/data_tuto/results/results.jpeg)
