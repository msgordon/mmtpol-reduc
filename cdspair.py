#! /usr/bin/env python
import argparse
import pyfits
import os
import warnings
import numpy as np

def pipe_run(filelist, outdir='cdspair', sim = False, verbose=False):
    try:
        os.mkdir(outdir)
    except OSError:
        if verbose:
            print 'Directory %s exists' % outdir



    outlist = []
    for filename in filelist:
        data, header = subtract(filename)
        outfile = os.path.join(outdir, filename)
        if verbose:
            print '\tWriting %s' % outfile
            
        if not sim:
            with warnings.catch_warnings():
                warnings.simplefilter('ignore')
                pyfits.writeto(outfile, data, header, clobber = True)
        outlist.append(outfile)

    return outlist


def subtract(filename,getheader=True):
    '''Subtract FITS extensions.  Return array and header'''
    hdu = pyfits.open(filename)
    
    # Subtract pre-read from post-read
    data = hdu[-1].data - hdu[1].data
    data = data.astype(np.float)

    header = hdu[0].header
    header['PIXSCALE'] = (0.043, 'arcsec/pix')
    header.remove('OBJECT')  # Two OBJECT keywords

    header['CDSSUB'] = (True, 'CDS pair subtraction performed')

    # delete the DATE-OBS and TIME-OBS keywords
    header.remove('date-obs')
    header.remove('time-obs')

    # rename the DATE keyword to become DATE-OBS, conform to FITS standard
    header.rename_keyword('date', 'date-obs')
    header.comments['date-obs'] = 'UTC date of observation'

    # rename the UT keyword to become TIME-OBS, add comment
    header.rename_keyword('ut', 'time-obs')
    header.comments['time-obs'] = 'UTC time of observation'

    return data, header


def main():
    parser = argparse.ArgumentParser(description='Perform CDS pair subtraction')
    parser.add_argument('filelist',nargs='+',help='Files to subtract')
    parser.add_argument('-o',type=str,default='cdspair',help='Specify output directory (default="cdspair"')

    args = parser.parse_args()

    try:
        os.mkdir(args.o)
    except OSError:
        print 'Directory %s exists' % args.o

    for filename in filelist:
        data, header = subtract(filename)
        outfile = os.path.join(args.o, filename)
        print '\tWriting %s' % outfile
        #pyfits.writeto(outfile, data, header, clobber = True)

    return 0
    

if __name__ == '__main__':
    main()
