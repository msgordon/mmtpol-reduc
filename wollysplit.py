#! /usr/bin/env python
import pyfits
import os
import argparse
import numpy as np


def get_filenum(name,prefix):
    stripped = os.path.basename(name).split(prefix)
    num = stripped[1].split('_')[0]
    return int(num)

def split(filename,outdir,sim=False):
    basename, ext = os.path.splitext(filename)
    basename = os.path.basename(basename)
    basename = os.path.join(outdir,basename)
    
    Orfile = ''.join([basename,'.Or',ext])
    Exfile = ''.join([basename,'.Ex',ext])


    if not sim:
        try:
            os.mkdir(outdir)
        except OSError:
            # directory exists
            pass

        f = pyfits.open(filename)

        xdim = f[0].header['NAXIS1']/2

        Ordat = f[0].data[:,xdim:]   #left
        Exdat = f[0].data[:,0:xdim]  #right


        hdr = f[0].header
        hdr['BEAM'] = ('Or','Image half')
        #hdr['FILENUM'] = (get_filenum(filename,prefix),'Observation number')
    
        pyfits.writeto(Orfile,Ordat,header=hdr,clobber=True)
                
        hdr['BEAM'] = ('Ex','Image half')
        pyfits.writeto(Exfile,Exdat,header=hdr,clobber=True)
        f.close()

    return (Orfile, Exfile)

    
def pipe_run(filelist, outdir='wollydir',groups=False,sim=False):
    filelist = list(filelist)

    #if groups, list has been divided into sections
    if not groups:
        outlist = [split(x,outdir,sim=sim) for x in filelist]
    else:
        outlist = []
        for group in filelist:
            outlist.append([split(x,outdir,sim=sim) for x in group])

    return outlist
        
    


def main():
    parser = argparse.ArgumentParser(description='Split MMTPOL images into A and B components.')

    parser.add_argument('file',nargs='+',help='Input file(s)')
    parser.add_argument('-o',metavar='outdir',dest='outdir',required=True,help='Output directory')
    parser.add_argument('-prefix',required=True,help='Filename prefix before filenumber.')

    args = parser.parse_args()

    for filename in args.file:
        print pipe_run(filename,args.prefix,args.outdir)

    print 'Split %i files to %s' % (len(args.file),args.outdir)
            

if __name__ == '__main__':
    main()
