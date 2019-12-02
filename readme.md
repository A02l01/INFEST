# INFEST
## Overview
INFEST for k**IN**ematic o**F** l**ES**ion developmen**T**. This plugin was used to compute the kinematic of lesion caused by the necrotrophic fungus _Sclerotinia sclerotiorum_. INFEST was developed for [QIP](http://qiplab.weebly.com/overview.html) (quantitative immunity in plant) @ LIPM (Lab of plant microbes interaction) in Toulouse by Adelin Barbacci. **INFEST was founded by Sylvain Raffaele's ERC varywim**. Feel free to use it.


 **For academics use please cite :**

 >Barbacci, A., Navaud, O., Mbengue, M., Barascud, M., Godiard, L., Khaffif, M., Lacaze, A., Raffaele, S., 2020 **Rapid identification of an Arabidopsis NLR gene conferring susceptibility to Sclerotinia sclerotiorum using real-time automated phenotyping**. Rev.

We are on twitter
[AB](https://twitter.com/A_Barbacci),
[SR](https://twitter.com/QIPlab)

![Kinematic of lesion development for the leaf 'Col-0_154'](https://github.com/A02l01/d/blob/master/d/inf.gif)


### INFEST

```
usage: infest.py [-h] [-f FIRST] [-l LAST] mpath

positional arguments:
  mpath                 Path to the directory containing pictures

optional arguments:
  -h, --help            show this help message and exit
  -f FIRST, --first FIRST
                        Number of the first picture
  -l LAST, --last LAST  Number of the last picture
```

**output**
> `analyse.txt` file created in the  `mpath` directory containing 3 columns: the **Id** of leaf, the **time** extracted from pictures name and the size of the **Lesion**

#### Examples
```
python infest.py mpath -f 0 -l 400

python infest.py mpath -f 0

python infest.py mpath
```

### fit INFEST

```
usage: fit_INFEST.py [-h] [-g] path_in path_out

positional arguments:
  path_in      the path to the file containing temporal data computed by
               INFEST
  path_out     the path to the file containing LDT and Latency

optional arguments:
  -h, --help   show this help message and exit
  -g, --graph  monitoring the fit of the curve
```
**output**
> txt file specified in `path_out` directory containing 9 columns: the **Id** of leaf, the parameters **a1** to **a5** resulting from the fit, the **residuals** of the fit, the lesion doubling time **LDT**, and the **Latency**

### Latest news
- Version 1 available

# Getting started
## Details
This version has been developed and tested under ubuntu 18.10 with python 2.7. The dependancies are:
- backports-functools-lru-cache==1.5
- cloudpickle==1.2.2
- cycler==0.10.0
- decorator==4.4.0
- kiwisolver==1.1.0
- matplotlib==2.2.4
- networkx==2.2
- numpy==1.16.5
- pillow==6.2.1
- pyparsing==2.4.2
- python-dateutil==2.8.0
- pytz==2019.3
- pywavelets==1.0.3
- scikit-image==0.14.5
- scipy==1.2.2
- six==1.12.0
- subprocess32==3.5.4
- argparse==1.1
- pandas==0.23.3
- pymodelfit==0.1

__Dependancies are listed in the `env_Infest.yml` file__
## Prerequists
### Python and conda
Install conda
- For linux install please see: [here](https://docs.conda.io/projects/conda/en/latest/user-guide/install/linux.html)
- For other systems: [here](https://docs.conda.io/projects/conda/en/latest/user-guide/install/#system-requirements)

### Pictures & Files
- Jpeg images stored in a directory and named by an integer _e.g._ `1.jpg` to `N.jpg` corresponding to the time course.
- the layout file `grid_layout.layout` in the subdirectory `grid_layout` of the directory containing pictures (e.g. `my_pictures/grid_layout/grid_layout.layout` _c.f._ tutorial)
- The layout file provide the Id and the bounding boxes of leaves _e.g._


 ```'
id_leaf_1\tymin\txmin\tymax\txmax\n
id_leaf_1\tymin\txmin\tymax\txmax\n
id_leaf_3\t...
```
with `\t ` a tabulation.
### Download INFEST and fit_INFEST
 - manually, using git or wget

`wget --no-check-certificate --content-disposition https://github.com/A02l01/INFEST/tarball/master`

 - Extract the tarball

 `tar xvzf A02l01-INFEST-719d386.tar.gz`
### Creation of the conda environment

Creation of a conda environment called INFEST from the yaml file <a name="#conda"></a>
 - download `env_Infest.yml` file in your working directory
 - `conda env create -n INFEST -f env_Infest.yml`
 - To activate INFEST env: `conda activate INFEST`
 - To deactivate INFEST env: `conda deactivate`




# Tutorial
> This tutorial was designed for linux users. It is easily transposable for macOS and Windows users by replacing most of command lines by fastidious mouse clicks.

In this short tutorial we will use **INFEST** to compute the kinematic of lesion development of a single detached leaf of _Arabidopsis thaliana_ coined _Col-0_154_.

## Download data
Data are in the `data_tuto/` directory. Download and extract data:

`wget --no-check-certificate --content-disposition https://github.com/A02l01/tuto/tarball/master`

`tar xvzf A02l01-tuto-08e3f70.tar.gz`


![Col-0_154 leaf](https://github.com/A02l01/tuto/blob/master/data_tuto/pictures/grid_layout/panel.jpg)

Other kinematics can be computed by adding bounding boxes of leaves in the `grid_layout.layout` file.

## creation of the layout file
- Downloaded data contains yet a layout file but in the general case you must generate this file and put in the right directory
- If needed creates a directory  in the pictures directory and the file `grid_layout.layout` in `grid_layout/` _e.g._ `.../A02l01-tuto-08e3f70/data_tuto/pictures/grid_layout/grid_layout.layout`. Fill `grid_layout.layout` with the coordinates of the bounding rectangles of leaves. We used [ImageJ](https://imagej.nih.gov/ij/download.html) to obtain coordinates. In this example the single line added in the `grid_layout.layout` file is

`Col-0_154       1410    2574    1497    2721`

with:
 - `Col-0_154` the **Id** of the leaf,
 - `1410` **ymin** of the rectangle,
 - `2574` **xmin** of the rectangle,
 - `1497` **ymax** of the rectangle,
 - `2721` **xmax** of the rectangle.

>**Items are separeted by a tabulation**.

## Compute kinematics of Lesion

- activate conda environment (to create the INFEST conda environment please see instructions [here](#creation-of-the-conda-environment))

`conda activate INFEST`

`python infest.py '.../A02l01-tuto-08e3f70/data_tuto/pictures/' -f 0 -l 270`

results are stored in `'.../A02l01-tuto-08e3f70/data_tuto/pictures/analyse.txt'`

![Kinematic of lesion development for the leaf 'Col-0_154'](https://github.com/A02l01/tuto/blob/master/data_tuto/results/results.jpeg)

## Compute the lesion LDT
We show that LDT is a good proxy of the level of plant resistance in Barbacci et al. 2020. Nevertheless other proxy could be derived from the kinematics computed by INFEST.

To extract the lesion doubling time (LDT) from the kinematic of lesion development using the python script `fit_INFEST.py`:
`python fit_INFEST.py '.../A02l01-tuto-08e3f70/data_tuto/pictures/analyse.txt' '.../A02l01-tuto-08e3f70/data_tuto/pictures/ldt.txt' -g
`
leading to
![Kinematic of lesion development for the leaf 'Col-0_154'](https://raw.githubusercontent.com/A02l01/d/master/d/ldt.png)


```
  ##     ###             ###     ##
 #       ###             ###       #
#                                   #
#        ###     ###     ###        #
#        ###     ###     ###        #
 #        #       #       #        #
  ##     #       #       #       ##

QiP Team LIPM Toulouse
```
