#! /usr/bin/env python
import argparse
import pyfits
import xCorrAlign

filter_dict = {'Ks (2.199 um)':'Ks','3.1 narrow':'3.1'}

def get_filter(filename):
    f = pyfits.getval(filename,'FILTER')
    return filter_dict[f]
    
def get_pol(filename):
    p = pyfits.getval(filename,'POLPAIR')
    return p

def get_beam(filename):
    b = pyfits.getval(filename,'BEAM')
    return b
    

def main():
    parser = argparse.ArgumentParser(description='Align and combine images')
    parser.add_argument('filelist',nargs='+',help='Images to combine')
    parser.add_argument('-f',required=True,metavar='filter',help='Specify filter',choices = ('3.1','Ks'))
    parser.add_argument('-o',required=True,metavar='outdir',help='Output directory')
    parser.add_argument('-s',metavar='size',type=int, default=None, help='Specify box size for correlation. Default is the full image, which can be very slow')
    parser.add_argument('-c',metavar=('x_cen', 'y_cen'),type=int,nargs=2, default=None,help="If '-s' specified, optionally include a center for the box region. Default is the center of image1.")
    parser.add_argument('--sim',action='store_true',help='If specified, simulate without writing files')

    
    args = parser.parse_args()

    filelist = [filename for filename in args.filelist if get_filter(filename) == args.f]
    Exlist = [filename for filename in filelist if get_beam(filename) == 'Ex']
    ORlist = [filename for filename in filelist if get_beam(filename) == 'Or']

    xCorrAlign.pipe_run(Exlist,args.o,size=args.s,center=args.c,sim=args.sim)
    

    
    


if __name__ == '__main__':
    main()
