# INFEST

INFEST for k**IN**ematic o**F** l**ES**ion developmen**T**. This plugin was used to compute the kinematic of lesion caused by the necrotrophic fungus _Sclerotinia sclerotiorum_. INFEST was developed for [QIP](http://qiplab.weebly.com/overview.html) (quantitative immunity in plant) @ LIPM (Lab of plant microbes interaction) in Toulouse by Adelin Barbacci. **INFEST was founded by Sylvain Raffaele's ERC varywim**. Feel free to use it.


**For academic use please cite:**

> Barbacci, A., Navaud, O., Mbengue, M., Barascud, M., Godiard, L., Khafif, M., Lacaze, A., Raffaele, S., 2020 **Rapid identification of an Arabidopsis NLR gene conferring susceptibility to Sclerotinia sclerotiorum using real-time automated phenotyping**. Rev.

We are on twitter
[AB](https://twitter.com/A_Barbacci),
[SR](https://twitter.com/QIPlab)

![Kinematic of lesion development for the leaf 'Col-0_154'](https://github.com/A02l01/d/blob/master/d/inf.gif)


### INFEST

```
usage: infest [-h] [-f FIRST] [-l LAST] mpath

positional arguments:
  mpath                 Path to the directory containing pictures

optional arguments:
  -h, --help            show this help message and exit
  -f FIRST, --first FIRST
                        Number of the first picture
  -l LAST, --last LAST  Number of the last picture
  -w DIR, --write-video DIR Write animations of each leaf to this directory.
                            Default: don't write animations.
  -n INT, --ncpu INT    How many cpus can we use? Default 1.
  -d DPI, --dpi DPI     If writing a video, what resolution should it have? Default 300.
  -s FRAMESTEP, --framestep FRAMESTEP
                        If writing a video, how many milliseconds should each image be displayed for.
                        E.g. framestep=100 (default) means 10 images will be displayed per second.
```

#### Output
`analyse.txt` file created in the  `mpath` directory containing 3 columns: the **id** of leaf, the **time** extracted from pictures name, the **lesion_area** and the **leaf_area**.

If `--write-video` is given a directory, mpeg videos will be written to that directory.


#### Examples


```
# Processes images between 0 and 400.
infest.py mpath -f 0 -l 400
# Same as above
infest.py mpath -l 400

# Write animations and use 4 cpus.
infest.py mpath --write-video mpath_animations --ncpu 4
```


### fit INFEST

> **NOTE:** This method is no longer used in practise.
> You should probably use the R script stored in [`scripts/slopes.R`](#using-the-r-script)

```
usage: infest-fit [-h] [-ft FIRST] [-g] path_in path_out

positional arguments:
  path_in               the path to the file containing temporal data computed
                        by INFEST
  path_out              the path to the file containing LDT and Latency

optional arguments:
  -h, --help            show this help message and exit
  -ft FIRST, --first FIRST
                        the first time to consider for the computation of the
                        LDT
  -g, --graph           monitoring the fit of the curve
```

#### Output

A txt file specified in `path_out` directory containing 9 columns: the **Id** of leaf, the parameters **a1** to **a5** resulting from the fit, the **residuals** of the fit, the lesion doubling time **LDT**, and the **Latency**

### Check layout

Check that your bounding boxes in the layout actually cover the leaves.

You can run this for a single image, or multiple.
Optionally, you can output an animation to easily check the boxes for the whole experiment run (e.g. accounting for movement and focus).

```
usage: infest-check-layout [-h] [-a] [-o OUTFILE] [--dpi DPI] layout images [images ...]

positional arguments:
  layout                A tsv file detailing the experiment layout.
  images                The path to the image you want to overlay the layout onto.

options:
  -h, --help            show this help message and exit
  -a, --animate         Should we write the output as an mpeg?
  -o OUTFILE, --outfile OUTFILE
                        Where to save the output file(s) to. If multiple images are provided, this should be a directory. If you specify multiple images and the --animate option, this should be the mpeg filename. If a single image is given, this should be the jpeg filename.
                        Default: grid_layout/panel.jpg, grid_layout/panel/{0..1}.jpg, grid_layout/panel.mpeg
  --dpi DPI             What resolution to save the image as.
```

#### Output

A depending on the number of images provided:
- Single JPEG image showing leaf positions in the image.
- Multiple JPEG images in a directory.
- A single MPEG video.


#### Examples

```
# Single image
infest-check-layout -o grid_layout/panel.jpg layout.tsv 0.jpg

# Multiple images, will create a directory grid_layout/panel
infest-check-layout -o grid_layout/panel layout.tsv *.jpg

# A video
infest-check-layout -a -o grid_layout/panel.mpeg layout.tsv *.jpg
```


### Latest news
- Version 1 available

### Install

#### Prerequisites

INFEST needs these python packages to work.

- scikit-image
- numpy
- scipy
- pandas
- matplotlib

These can be installed using either [conda](https://docs.conda.io/en/latest/) or [pip](https://pip.pypa.io/en/stable/).


If you want to plot animations of the leaves, you'll also need the [ffmpeg](https://ffmpeg.org/) tool installed.
On ubuntu/debian this can be installed with:

```
sudo apt update && sudo apt install ffmpeg
```

Alternatively you can use conda.

Both of the installation options described below also require git.


#### Using Conda

Install conda
- For linux install please see: [here](https://docs.conda.io/projects/conda/en/latest/user-guide/install/linux.html)
- For other systems: [here](https://docs.conda.io/projects/conda/en/latest/user-guide/install/#system-requirements)

To create an environment you can run the following:

```
curl -o environment.yml https://raw.githubusercontent.com/darcyabjones/INFEST/master/environment.yaml

conda env create -f environment.yml -n INFEST
conda activate INFEST

# OR 

conda env create -f environment.yml -p ./condaenv
conda activate ./condaenv
```

The difference is that with `-n` you can load the environment from anywhere (but files are always stored in your home directory), whereas with `-p` you can specify where the files are kept.
On supercomputers or other places where your home disk space is small, the `-p` option is often better.

Any time you want to use the program after restarting your terminal, you'll need to run the appropriate `conda activate` command as above.


#### Using pip

Pip will usually come installed with any new python installation.
But if it isn't available, you can install it on debian/ubuntu with:

```
sudo apt update && sudo apt install python3-pip
```

> NOTE: on some operating systems you may need to substitute `python3` for `python` (e.g. some new linux versions), or `Python` (Windows CMD).

I highly recommend that you install the program into a virtual environment of some kind.
This avoids compatibility issues with other software.

```
python3 -m venv ./env 
source ./env/bin/activate

python3 -m pip install git+https://github.com/darcyabjones/INFEST.git
```

To use the virtual environment in the future, you'll need to run `source ./env/bin/activate` whenever you re-start the terminal.


If you don't want to use a virtual environment, it's better to install as user (rather than a whole system installation).

```
python3 -m pip install --user git+https://github.com/darcyabjones/INFEST.git
```

You may then need to add that directory to your `PATH`. e.g.

```
# The directory may be different, but this is fairly common on linux.
echo 'export PATH="${PATH:-}:${HOME}/.local/bin"' >> ~/.bashrc
```


#### Using pip, without git

If you don't have git installed (and can't install it), you can install it like this:

```
# OPTIONAL but recommended
# Create a conda or virtualenv

# You could also do this with a browser if you prefer.
curl -o INFEST.zip https://github.com/darcyabjones/INFEST/archive/refs/heads/master.zip
unzip INFEST.zip

# Or with --user
# If you want to be able to edit the package and have changes work immediately you can also specify `-e` or `--editable`
python3 -m pip install ./INFEST/
```



### Pictures & Files

- Jpeg images stored in a directory and named by an integer _e.g._ `1.jpg` to `N.jpg` corresponding to the time course.
- the layout file `grid_layout.layout` in the subdirectory `grid_layout` of the directory containing pictures (e.g. `my_pictures/grid_layout/grid_layout.layout` _c.f._ tutorial)
- The layout file provide the Id and the bounding boxes of leaves _e.g._


```
id_leaf_1\tymin\txmin\tymax\txmax\n
id_leaf_1\tymin\txmin\tymax\txmax\n
id_leaf_3\t...
```
with `\t ` a tabulation.


***

## Tutorial
> This tutorial was designed for linux users. It is easily transposable for macOS and Windows users by replacing most of command lines by fastidious mouse clicks.

In this short tutorial we will use **INFEST** to compute the kinematic of lesion development of a single detached leaf of _Arabidopsis thaliana_ coined _Col-0_154_.

## Download data
Data are in the `data_tuto/` directory. Download and extract data with git:

`$ git clone https://github.com/A02l01/tuto.git`


![Col-0_154 leaf](https://github.com/A02l01/tuto/blob/master/data_tuto/pictures/grid_layout/panel.jpg)

Other kinematics can be computed by adding bounding boxes of leaves in the `grid_layout.layout` file.

### creation of the layout file
- Downloaded data contains yet a layout file but in the general case you must generate this file and put in the right directory
- If needed creates a directory  in the pictures directory and the file `grid_layout.layout` in `grid_layout/` _e.g._ `./tuto/data_tuto/pictures/grid_layout/grid_layout.layout`. Fill `grid_layout.layout` with the coordinates of the bounding rectangles of leaves. We used [ImageJ](https://imagej.nih.gov/ij/download.html) to obtain coordinates. In this example the single line added in the `grid_layout.layout` file is `Col-0_154	1410	2574	1497	2721`.

with:
 - `Col-0_154` the **Id** of the leaf,
 - `1410` **ymin** of the rectangle,
 - `2574` **xmin** of the rectangle,
 - `1497` **ymax** of the rectangle,
 - `2721` **xmax** of the rectangle.

> **Items are separated by a tab character**.

You can then check that your layout file is ok:

```
conda activate INFEST
cd tuto/data_tuto
infest-check-layout -o pictures/grid_layout/panel.jpg pictures/grid_layout/grid_layout.layout pictures/0.jpg
```

Have a look at `panel.jpg` to see if the samples are well bounded.


### Compute kinematics of Lesion


```
infest -n 4 --write-video ./animations pictures
```

results are stored in `./pictures/analyse.txt'`

![Kinematic of lesion development for the leaf 'Col-0_154'](https://github.com/A02l01/tuto/blob/master/data_tuto/results/results.jpeg)


### Compute the lesion LDT

We show that LDT is a good proxy of the level of plant resistance in Barbacci et al. 2020. Nevertheless other proxy could be derived from the kinematics computed by INFEST.

To extract the lesion doubling time (LDT) from the kinematic of lesion development using the python script `fit_INFEST.py`:

```
infest-fit --graph ./pictures/analyse.txt ./pictures/ldt.txt
```

Leading to:

![Kinematic of lesion development for the leaf 'Col-0_154'](https://raw.githubusercontent.com/A02l01/d/master/d/ldt.png)

### Using the R-script

Sometimes the lesion doubling time can be difficult to determine automatically.
The R-script helps you to interactively select the best regions to find the slopes.

You'll need to have the following R packages:

- ggplot2
- ggrepel
- segmented
- cowplot

```r
install.packages(c("ggplot2", "ggrepel", "segmented", "cowplot"))
```

To use the script, you can download it locally:

```
curl -o slopes.R https://raw.githubusercontent.com/darcyabjones/INFEST/master/scripts/slopes.R
```

Now open an interactive R terminal (e.g. Rstudio), and `source` this script to use the main function `compute_slope`.

```r
source("slopes.R")

# Load your data
df <- read.table("./picture/analyse.txt", header = TRUE)

# _IF_ your data was analysed by a previous tool

if (paste(names(df), collapse = " ") != "id time lesion_area leaf_area") {
  if ((ncol(df) == 3) && all(names(df) == c("Id", "time", "Lesion"))) {
    names(df) <- c("id", "time", "lesion_area")
  } else if ((ncol(df) == 3) && all(names(df) == c("Id", "time", "Lesion"))) {
    names(df) <- c("id", "time", "lesion_area")
  } else {
    print("WARNING: couldn't figure out how to map your column names.")
  }
}

compute_slope(df, "manual_slopes.tsv")
```

You'll be presented plots of the data and asked to enter ranges and check whether the data are ok.
You may wish to view the animated videos if the curve is a bit odd.


***

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
