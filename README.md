## MMTPol Python Reduction Pipeline
This repository is a collection of programs useful for organizing the many files associated with imaging polarimetry. ```obsproc.py``` is the single entry point and performs the following tasks:

- CDS pair subtraction
- Dither pair subtraction
- QU pair subtraction (optional)
- Coadd dither pairs (for ABBA pattern, optional)
- Wolly split

More on these steps below.

### Requirements
The following python modules are required.

- [stsci_python](http://www.stsci.edu/institute/software_hardware/pyraf/stsci_python/installation)
- [SciPy stack](http://www.scipy.org/install.html)

### Installation
The repository can simply be downloaded as a [.zip](https://github.com/msgordon/mmtpol-reduc/archive/master.zip), but if possible, please use ```git```:

```git clone https://github.com/msgordon/mmtpol-reduc.git```

For ease of use, place the code directory in your ```PATH``` environment.

### Usage
All modules have an integrated help menu that can be displayed with the ```-h``` command-line switch.

Each set of observations is run through the main ```obsproc.py``` program using a config file.  This file must be constructed for each object based on information from the observation log.  An example is included in the repository above (```p_HD_38563A.cfg```), but the syntax is also reviewed below.
```
[OBS1]
object = p_HD_38563A       # object name
outdir = p_HD_38563A       # output directory, relative to here
prefix = MMTPol_2015Mar06  # prefix of filename before filenum, including path 
                           #   ex. /path/to/files/MMTPol_2015Mar06.0272.fits
			   #   --->  prefix = /path/to/files/MMTPol_2015Mar06
dither_pattern = ABBA      # dither pattern used
                           #   currently, ABBA is the only supported pattern
obs_per_pos = 1            # number of observations per HWP pos
                           #   typically = 1
start = 125                # first exposure file number in the sequence
stop = 140                 # last exposure file number in the sequence
```

Multiple observation sets of the same object can (and should) be placed in the same config file by adding additional section headers (```[OBS2]```, ```[OBS3]```, etc).

Assuming ```obsproc.py``` is in your ```PATH```, run the program in the same directory as the data as follows:

```obsproc.py p_HD_38563A.cfg```

If you would like to do a 'dry-run' without actually writing files, add the ```--sim``` switch:

```obsproc.py p_HD_38563A.cfg --sim```

Additionally, if you would like to coadd the two ```ABBA``` dither pairs (```[A1-B1]``` + ```[A2-B2]```), use the ```--dithadd``` switch.  To perform QU pair subtraction (```Q``` = ```[00]-[45]```, ```U``` = ```[22]-[67]```), use the ```--qusub``` switch.  These can be applied together, in which case the resulting images are coadds of the QU pairs.

```obsproc.py p_HD_38563A.cfg --qusub --dithadd```

Usage instructions can be seen, again, by using the ```-h``` switch:

```obsproc.py -h```

The resulting images from this example are written to:

```-> p_HD_38563A/wollysplit```

I have only tested this on a few observations from the March 2015 observing run, so please send me any issues you encounter, as well as the config file you used.

### Notes
I would urge caution using the ```--qusub``` mode if observing structure in extended sources.  Careful subpixel alignment is required to form the QU pairs, and I do not provide an automated mechanism for this.

Instead, I have written a module, ```nudge_align.py```, that allows for manual shifts in an interactive ```matplotlib``` window.  While I have found this extremely useful, I have not yet written adequate documentation.  Please email me if you would like a tutorial.

Please send me any feedback, or post an issue on github.
