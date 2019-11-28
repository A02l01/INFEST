# INFEST
## Overview
INFEST for k**IN**ematic o**F** l**ES**ion developmen**T**. This plugin was used to compute the kinematic of lesion caused by the necrotrophic fungus _Sclerotinia sclerotiorum_. INFEST was developed for QIP (quantitative immunity in plant) @ LIPM (Lab of plant microbes interaction) in Toulouse by Adelin Barbacci. **INFEST was founded by Sylvain Raffaele's ERC varywim**. Feel free to use it.


 **For academics use please cite :**

 >Barbacci, A., Navaud, O., Mbengue, M., Barascud, M., Godiard, L., Khaffif, M., Aline, L., Raffaele, S., 2020 **Rapid identification of an Arabidopsis NLR gene conferring susceptibility to Sclerotinia sclerotiorum using real-time automated phenotyping**. Rev.



![Kinematic of lesion development for the leaf 'Col-0_154'](https://github.com/A02l01/d/blob/master/d/inf.gif)


### Command line :

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

### Examples
```
python infest.py mpath -f 0 -l 400

python infest.py mpath -f 0

python infest.py mpath```


### Latest news
- Version 1 available

# Getting started
## Details
This version has been developed and tested under ubuntu 18.10 with python 2.7. The dependancies are:
- matplotlib==2.2.4
- numpy==1.16.5
- scikit-image==0.14.5
- pandas==

## Prerequists
### Pictures & Files
- Jpeg images stored in a directory and named by an integer _e.g._ `1.jpg` to `N.jpg` corresponding to the time course.
- the layout file `grid_layout.layout` in the subdirectory `grid_layout` of the directory containing pictures (e.g. `my_pictures/grid_layout/grid_layout.layout` _c.f._ tutorial)
- The layout file provide the Id and the bounding boxes of leaves _e.g._


 ```'
id_leaf_1\tymin\txmin\tymax\txmax\n
id_leaf_1\tymin\txmin\tymax\txmax\n
id_leaf_3\t...```
with `\t ` a tabulation.

### Python packages
- for running INFEST
  - matplotlib==2.2.4
  - numpy==1.16.5
  - scikit-image==0.14.5

  are required

- for running fit_INFEST
  - Pandas==

> __We strongly recommand to use virtual env such as conda virtual env to run INFEST__

> Install conda
- For linux install please see: [here](https://docs.conda.io/projects/conda/en/latest/user-guide/install/linux.html)
- For other systems: [here](https://docs.conda.io/projects/conda/en/latest/user-guide/install/#system-requirements)
- Creation of a conda environment
 - `conda env create -n INFEST -f env_Infest.yml`
 - `conda activate INFEST`
 - In the virtual environment
 - `python infest.py path_to_picture`

### Download the INFEST and fit INFEST:

`wget --no-check-certificate --content-disposition https://github.com/A02l01/INFEST/tarball/master`


## fit INFEST



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


# Tutorial
> This tutorial was designed for linux users. It is easily transposable for macOs and Windows users by replacing most of command lines by fastidious mouse clicks.

In this short tutorial we will use **INFEST** to compute the kinematic of lesion development of a single detached leaf of _Arabidopsis thaliana_ coined 'Col-0_154'.

## Download data
Data are in the `data_tuto/` directory. Download and extract data:

`wget --no-check-certificate --content-disposition https://github.com/A02l01/tuto/tarball/master`

`tar xvzf A02l01-tuto-08e3f70.tar.gz`


![Col-0_154 leaf](https://github.com/A02l01/tuto/blob/master/data_tuto/pictures/grid_layout/panel.jpg)

Other kinematics can be computed by adding bounding boxes of leaves in the `grid_layout.layout` file.

## creation of the layout file
- Downloaded data contains yet a layout file but in the general case you must generate this file and put in the right directory
- If needed creates a directory  in the pictures directory and the file `grid_layout.layout` in `grid_layout/`. Is looks like `.../A02l01-tuto-08e3f70/data_tuto/pictures/grid_layout/grid_layout.layout`. Fill `grid_layout.layout` with the coordinates of the bounding rectangles of leaves. We used [ImageJ](https://imagej.nih.gov/ij/download.html) to obtain coordinates. In this example the single line added in the `grid_layout.layout` file is

`Col-0_154       1410    2574    1497    2721`

with:
 - `Col-0_154` the **Id** of the leaf,
 - `1410` **ymin** of the rectangle,
 - `2574` **xmin** of the rectangle,
 - `1497` **ymax** of the rectangle,
 - `2721` **xmax** of the rectangle.

>**Items are separeted by a tabulation**.

## Compute kinematics of Lesion

`python infest.py '.../A02l01-tuto-08e3f70/data_tuto/pictures/' -f 0 -l 270`

results are stored in `'.../A02l01-tuto-08e3f70/data_tuto/pictures/analyse.txt'`

![Kinematic of lesion development for the leaf 'Col-0_154'](https://github.com/A02l01/tuto/blob/master/data_tuto/results/results.jpeg)

## Compute the lesion LDT
We extract the lesion doubling time (LDT) from the kinematic of lesion development using the python script `fit_INFEST.py`:
`python fit_INFEST.py '.../A02l01-tuto-08e3f70/data_tuto/pictures/analyse.txt' '.../A02l01-tuto-08e3f70/data_tuto/pictures/ldt.txt' -g
`
leading to
![Kinematic of lesion development for the leaf 'Col-0_154'](https://github.com/A02l01/tuto/blob/master/data_tuto/results/ldt.png)

We we show that LDT is a good proxy of the level of plant resistance in Barbacci et al. 2020. Nevertheless other proxy could be derived from the kinematics computed by INFEST.
