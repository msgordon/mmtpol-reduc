#! /usr/bin/env python
import argparse
import pyfits
import os
import glob
import ConfigParser
import cdspair

REQ_OPTIONS = set(('prefix','start','stop','dither_pattern',
                   'obs_per_pos','outdir'))

def proc_section(config, section, sim = False):
    options = config.options(section)
    if not set(options) >= REQ_OPTIONS:
        print 'Required options %s not in section %s' % \
            (list(REQ_OPTIONS-set(options)), section)
        return None

    filelist = get_filelist_by_range(config.get(section,'prefix'),
                                     config.getint(section,'start'),
                                     config.getint(section,'stop'))
    print section
    print '\t', '\n\t'.join(filelist)

    # make directory for obs
    outdir = config.get(section,'outdir')
    if not sim:
        try:
            os.mkdir(outdir)
        except OSError:
            # directory exists
            pass

    return filelist,outdir


def cds_pair_subtract(filelist, secdir, pairdir='cdspair',sim=False):
    cdsout = os.path.join(secdir,pairdir)
    cdspair.pipe_run(filelist, outdir=cdsout,sim=sim)
    print '-> %s' % cdsout
    return cdsout
    

def get_filelist_by_range(prefix, start, stop):
    filelist = glob.glob('%s*' % prefix)
    numlist = [int(name.split('.')[1]) for name in filelist]
    filelist = [name for name,num in zip(filelist,numlist) if (num <= stop) and (num >= start)]
    filelist.sort()
    return filelist


def qu_pair_subtract(config, section, secdir, cdsdir,qudir='qupair',sim=False):
    pattern = config.get(section, 'dither_pattern')
    obs_per_pos = config.getint(section, 'obs_per_pos')

    quout = os.path.join(secdir,qudir)
    if not sim:
        try:
            os.mkdir(quout)
        except OSError:
            # directory exists
            pass

    #if obs_per_pos > 1:
        # co add pairs
        
    


def main():
    parser = argparse.ArgumentParser(description='Process observations from .cfg file')
    parser.add_argument('cfg',type=str,help='Config file with obs params.')
    parser.add_argument('--sim',action='store_true',help='If specified, simulate without writing files')

    args = parser.parse_args()

    config = ConfigParser.SafeConfigParser()
    config.read(args.cfg)
    
    for section in config.sections():
        # get filelist for each section
        filelist, secdir = proc_section(config, section, args.sim)

        # perform cdspair subtraction
        cdsdir = cds_pair_subtract(filelist, secdir,sim=args.sim)

        # QU pair
        
        
        
if __name__ == '__main__':
    main()
