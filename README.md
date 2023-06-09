# INFEST

INFEST for k**IN**ematic o**F** l**ES**ion developmen**T** computes the kinematics of lesion development caused by the necrotrophic fungus _Sclerotinia sclerotiorum_.
INFEST was developed for [QIP](http://qiplab.weebly.com/overview.html) (quantitative immunity in plant) @ LIPM (Lab of plant microbes interaction) in Toulouse by Adelin Barbacci with contributions from Darcy Jones.
**INFEST was founded by Sylvain Raffaele's ERC varywim**.

Although the software was developed to phenotype _Sclerotinia sclerotiorum_ infections, it should also work well for other necrotrophic plant pathogens.


**For academic use please cite:**

> Barbacci, A., Navaud, O., Mbengue, M., Barascud, M., Godiard, L., Khafif, M., Lacaze, A., Raffaele, S., 2020 **Rapid identification of an Arabidopsis NLR gene conferring susceptibility to _Sclerotinia sclerotiorum_ using real-time automated phenotyping**. (2020) Plant J. 103(2) 903-917. [10.1111/tpj.14747](https://doi.org/10.1111/tpj.14747)


![Kinematic of lesion development](examples/example.gif)


**We list the programs and options below, but you can also follow a worked example in the [tutorial](/TUTORIAL.md).**


## Quick install

The easiest way to install INFEST is with the conda package manager.
Instructions to install conda on linux are [here](https://docs.conda.io/projects/conda/en/latest/user-guide/install/linux.html)

I suggest that you install INFEST in a [conda environment](https://conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html), because it avoids problems where you don't have permission to install software or if you need multiple versions of the same software (which might also be incompatible with other software).
To create an [environment](https://conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html) you can run the following:

```
curl -o environment.yml https://raw.githubusercontent.com/darcyabjones/INFEST/master/environment.yml

conda env create -f environment.yml -p ./condaenv
conda activate ./condaenv
```

Then whenever you want to run the INFEST analysis in a new terminal, you just re-run `conda activate ./condaenv`.

If you want to update the version of INFEST, the easist thing is to just delete this folder and re-create the environment.

```
rm -rf -- ./condaenv
conda env create -f environment.yml -p ./condaenv
```


For other install options, see the [INSTALL.md](/INSTALL.md) page.


## Required inputs

- jpeg or png images stored in a directory and named by an integer _e.g._ `1.jpg` to `N.jpg` corresponding to the time course order.
  Numbers may be missing in the series (e.g. if you exclude a time point because the image is poor).
  Date and times as `YYMMDDHHMMSS` may also be appropriate. As long as they can be converted to integers and the sorted order corresponds to the time-course order it will work.
- The layout file described below.

A suggested folder structure is like this:

```
my_pictures/
    0.jpg
    1.jpg
    2.jpg
    3.jpg
    grid_layout/grid_layout.layout
```


The layout file is a tab separated file containing the leaf ids and positions leaf bounding boxes, with the following columns:


| column | type   | description                             |
|--------|--------|-----------------------------------------|
| id     | string | The sample id of the leaf               |
| ymin   | int    | The minimum y-value of the bounding box |
| xmin   | int    | As above but for x                      |
| ymax   | int    | The maximum y-value of the bounding box |
| xmax   | int    | As above but for x                      |


Note that this file should not have a header.
An example file is provided in `examples/layout.tsv`


**Some example images and layout files used for testing is available for [Arabidopsis](/src/INFEST/data/atha) and [Soybean](src/INFEST/data/gmax).**


## INFEST

Quantifies lesion characteristics for a given panel of leaves over many sampled times.
For each leaf bounding box indicated by the layout file, this program masks the background and quantifies the proportion of pixels where the red value is greater than green (lesion), green is greater than red (leaf=this + lesion area), and a linear model of the three channels indicating chlorophyll content.

Optionally, you can run default normalisation at the same time (but running separately is recommended) and/or write animations of each leaf (which are helpful when evaluating curves).

Setting the `--masktype` depends on your data and you may find it helpful to run multiple times with different values.
There is little difference in runtimes.
`watershed` (default) is the most accurate of the leaf detection methods, but it can still struggle with plugs close to the edges of leaves. This is recommended for many broad-leaf plants.
`none` means that the background is not removed at all and the values will include the background pixels.
However because the background is more-or-less static, this can help avoid much of the noise caused by difficulties in differentiating plugs or white regions of the background from the lesions. This is recommended for narrow leaves.
`original` is the original method based on a hard colour saturation threshold.


```
usage: infest [-h] [-o OUTFILE] [-w WRITE_VIDEO] [-n NCPU] [-d DPI]
              [-s FRAMESTEP] [--normalise {uniform,nonuniform}]
              [-t {threshold,otsu,watershed,original,none}]
              layout images [images ...]

positional arguments:
  layout                Provide the locations of the leaves for quantification.
  images                The pictures you want to quantify.


options:
  -h, --help            show this help message and exit
  -o OUTFILE, --outfile OUTFILE
                        Where should we write the tab separated results?
                        Default: dirname/analysis.txt where "dirname" is the directory containing
                        the first image provided.
  -w WRITE_VIDEO, --write-video WRITE_VIDEO
                        Write videos of samples to this directory.
  -n NCPU, --ncpu NCPU  How many images to process in parallel.
  -d DPI, --dpi DPI     If writing a video, what resolution should it have? Default: 150
  -s FRAMESTEP, --framestep FRAMESTEP
                        If writing a video, how many milliseconds should each image be
                        displayed for. E.g. framestep=50 (default) means 20
                        images will be displayed per second.
  --normalise {uniform,nonuniform}
                        Normalise the image background colour before leaf analysis.
                        Default: no normalisation. See also 'infest-norm'
  -t {threshold,otsu,watershed,original,none}, --masktype {threshold,otsu,watershed,original,none}
                        What algorithm to use to detect the background. Default: watershed
```


#### Output

A tab separated file with 6 columns:

| column      | type   | description                                                   |
|-------------|--------|---------------------------------------------------------------|
| id          | string | The sample id of the leaf                                     |
| time        | int    | The time point that the measurement is from                   |
| lesion_area | int    | The number of pixels where the (1.1 * red) > green            |
| leaf_area   | int    | lesion_area + the number of pixels where (1.1 * red) < green  |
| ichloro_sum | float  | The chlorophyll content index                                 |
| x           | float  | The x mid-point of the bounding box given in the layout file  |
| y           | float  | The y mid-point of the bounding box given in the layout file  |

An example result is provided in `examples/analysis.tsv`

If `--write-video` is given a directory, mp4 videos of each leaf will be written to that directory.
The directory will be created if it doesn't already exist.

> Writing the animations is quite slow. A regular analysis of ~400 images might take 2 mins to complete,
> but then the animations could take a few hours to write.
> If you want to experiment with different `--masktype` values, I suggest you run
> it without animations first and then run with animations for the final run.


#### Examples


```
# Runs the default pipeline.
# Results will be in my_pictures/analyse.txt
infest my_pictures/grid_layout/grid_layout.layout my_pictures/*.jpg

infest \
  --masktype original \
  my_pictures/grid_layout/grid_layout.layout \
  my_pictures/*.jpg

# As above but using the original background removal method.

# Runs the above but using 4 cpus, writing animations 
# into a new folder "my_animations", and providing an explicit out
# file name.
# Note that writing the animations can take a long time.
infest --write-video my_animations \
  --ncpu 4 \
  --outfile my_analysis.tsv \
  my_pictures/grid_layout/grid_layout.layout \
  my_pictures/*.jpg
```


## Check layout

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
  -a, --animate         Should we write the output as an mp4?
  -o OUTFILE, --outfile OUTFILE
                        Where to save the output file(s) to.
                        If multiple images are provided, this should be a directory.
                        If you specify multiple images and the --animate option,
                        this should be the mp4 filename.
                        If a single image is given, this should be the jpeg filename.
                        Default: grid_layout/panel.jpg, grid_layout/panel/{0..1}.jpg, grid_layout/panel.mp4
  -d DPI, --dpi DPI     What resolution should the image have? Default: 150
  -s FRAMESTEP, --framestep FRAMESTEP
                        If writing a video, how many milliseconds should each image be displayed for.
                        E.g. framestep=50 (default) means 20 images will be displayed per second.
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

# Multiple images, will create a directory called 'grid_layout/panel'
infest-check-layout -o grid_layout/panel layout.tsv *.jpg

# A video
infest-check-layout -a -o grid_layout/panel.mp4 layout.tsv *.jpg
```


## Normalise background colour

Lighting conditions can significantly effect the colour balance of images between time points.
To improve consistency we normalise the colour balance to an approximate known white background.

This script automatically finds the white background (i.e. paper towel/tissue paper on which the leaves are placed), 
and recalibrates the image to have a more normal colour balance.

By default, this recalibration applies non-uniformly across the image.
It is common, for example, for growth lights to illuminate the center of the nauvitron more than the edges.
Normalising to a single value typically causes the center to be saturated and the edges to be a bit too dark.
Instead, we find mean colour balances in a non-overlapping grid, and find a smoothed background colour gradient using b-splines, which simultaneously interpolates the expected values of the white background would have been behind the leaves.

You can apply a uniform recalibration by supplying the `--uniform` parameter.
If there is little apparent lighting difference across the image this gives reasonable results.

The background detection can be difficult in some cases and may affect the results.
The "watershed" method is the most accurate, but is a bit slower. Use this for images with especially dark patches.
For most cases the default "otsu" method works well, but may occasionally fail to mask out very light sections of the leaf.
In practise this doesn't matter much because the spline isn't strongly affected by extreme values.
Finally, although providing the layout grid (the same one used in the final `infest` program) is optional, it is highly recommended if you have very uneven lighting.
Sometimes the background detection will think a particularly dark patch of background is a leaf, and the background won't be normaliseed. Adding the layout simply excludes these regions.



```
usage: infest-norm [-h] [-l LAYOUT] [-o OUTDIR] [-u] [-g GRIDSIZE] [-m MINSIZE] [-t {threshold,otsu,watershed}] [-n NCPU]
                   images [images ...]

positional arguments:
  images                The path to the image you want to overlay the layout onto.

options:
  -h, --help            show this help message and exit
  -l LAYOUT, --layout LAYOUT
                        Provide the locations of the leaves to help in finding the background.
  -o OUTDIR, --outdir OUTDIR
                        Where to save the output file(s) to.
  -u, --uniform         Instead of applying region specific normalisation, normalise by average background
  -g GRIDSIZE, --gridsize GRIDSIZE
                        How big should the grid be? NOTE: Smaller values use more memory. Default: 10
  -m MINSIZE, --minsize MINSIZE
                        The minimum size of a foreground object for background detection. Default: 500.
  -t {threshold,otsu,watershed}, --masktype {threshold,otsu,watershed}
                        What algorithm to use to detect the background. Default: otsu
  -n NCPU, --ncpu NCPU  How many images to process in parallel.
```

#### Examples

```
infest-norm \
  --outdir images_corrected \
  --masktype watershed \
  --ncpu 4 \
  images_raw/*.jpg
```

Will process each image in `images_raw` ending with the extension `.jpg`.
It will use the watershed method to distinguish the leaves from the background.
This will output a single colour corrected image for each input image into `images_corrected`.


## Get example data

We have a command to retrieve the example data we use for tutorials, testing and development.

```
usage: infest-example [-h] [-o OUTDIR] {atha,gmax,marca}

positional arguments:
  {atha,gmax,marca}     Which dataset to get.

options:
  -h, --help            show this help message and exit
  -o OUTDIR, --outdir OUTDIR
                        Where to save the example directory to.
                        Will raise an error if the target directory already exits.
```


#### Examples

```
infest-example -o ./my_atha_data atha
```

Will create a local folder `./my_atha_data` containing some arabidopsis example data.


## Troubleshooting

*The animations won't show in my video software*
The earlier versions of Darcy's infest updates used a codec that wasn't compatible with many players.
If you have animations from older versions, try running the following command in the same directory as the mpeg videos, to convert them to the more compatible mp4.

```bash
for MPG in *.mpeg
do
    ffmpeg -i "${MPG}" -c:v libx264 -strict -2 -preset slow -pix_fmt yuv420p -vf "scale=trunc(iw/2)*2:trunc(ih/2)*2" -f mp4 "${MPG%.mpeg}.mp4"
done
```


***

## Latest news

- Version 1 available
- An updated version of INFEST for Python3, with support for multiple cpus, background colour correction, and different masking options was contributed by Darcy Jones ![here](https://github.com/darcyabjones/INFEST)


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

## Contact us 

This software was primarily written by Adelin Barbacci, with contributions by Darcy Jones.
The best way to get help is to [raise an issue on GitHub](https://github.com/A02l01/INFEST/issues).
Alternatively, you can email us.

We are on also twitter
[AB](https://twitter.com/A_Barbacci),
[SR](https://twitter.com/QIPlab).
