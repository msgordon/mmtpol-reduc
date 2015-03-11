#! /usr/bin/env python
import argparse
import pyfits
import os
import glob
import ConfigParser
import cdspair
import wollysplit
import warnings
from imarith import combine, coadd
import nudge_align

REQ_OPTIONS = set(('prefix','start','stop','dither_pattern',
                   'obs_per_pos','outdir'))

def columns(printlist, cols=2):
    pairs = ["\t".join(printlist[i:i+cols]) for i in range(0,len(printlist),cols)]
    return "\n\t".join(pairs)

def proc_section(config, section, sim = False):
    options = config.options(section)
    if not set(options) >= REQ_OPTIONS:
        print 'Required options %s not in section %s' % \
            (list(REQ_OPTIONS-set(options)), section)
        return None

    filelist = get_filelist_by_range(config.get(section,'prefix'),
                                     config.getint(section,'start'),
                                     config.getint(section,'stop'))
    print '[%s]' % section
    #print '\t', '\n\t'.join(filelist)
    print '\t',columns(filelist)

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
    cdslist = cdspair.pipe_run(filelist, outdir=cdsout,sim=sim)
    print 'CDS pairs \t-> %s' % cdsout
    return cdslist


def wolly_split(filelist,wollydir='wollysplit',groups=False,sim=False):
    wollylist = wollysplit.pipe_run(filelist,outdir=wollydir,groups=groups,sim=sim)
    print 'Wolly split \t-> %s' % wollydir
    return wollylist
    

def get_filelist_by_range(prefix, start, stop):
    filelist = glob.glob('%s*' % prefix)
    numlist = [int(name.split('.')[1]) for name in filelist]
    filelist = [name for name,num in zip(filelist,numlist) if (num <= stop) and (num >= start)]
    filelist.sort()
    return filelist

def coadd_obs(cdslist,obs_per_pos,codir='coaddobs',sim=False):
    if not sim:
        try:
            os.mkdir(codir)
        except OSError:
            # directory exists
            pass

    # co add pairs
    groups = zip(*[iter(cdslist)]*obs_per_pos)
    coaddlist = []
    for group in groups:
        filenums = [x.split('.')[-2] for x in group]
        outfile = os.path.basename(group[0]).split('.')[0]
        outfile = '.'.join([outfile]+filenums+['fits'])
        outfile = os.path.join(codir,outfile)

        coaddlist.append(outfile)

        if not sim:
            data, header = coadd(group,method='sum')
            with warnings.catch_warnings():
                warnings.simplefilter('ignore')
                pyfits.writeto(outfile,data,header,clobber=True)

    print 'Coadd obs \t-> %s' % codir
    return coaddlist


def obspair_sum(filelist,section,prefix,pattern,obspairdir='obspair',sim=False):
    if not sim:
        try:
            os.mkdir(obspairdir)
        except OSError:
            # directory exists
            pass

    Qfile = '.'.join([prefix,section,'Q','fits'])
    Ufile = '.'.join([prefix,section,'U','fits'])

    Qfile = os.path.join(obspairdir,Qfile)
    Ufile = os.path.join(obspairdir,Ufile)

    if not sim:
        Qdata,Qheader = combine(filelist[0],filelist[1],method='sum')
        Udata,Uheader = combine(filelist[2],filelist[3],method='sum')

        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            pyfits.writeto(Qfile,Qdata,Qheader,clobber=True)
            pyfits.writeto(Ufile,Udata,Uheader,clobber=True)

    print 'Obs pairs \t-> %s' % obspairdir
    return Qfile,Ufile

def dither_subtract(cdslist,section,prefix,pattern,ditherdir='dithersub',sim=False):
    if not sim:
        try:
            os.mkdir(ditherdir)
        except OSError:
            # directory exists
            pass


    outlist = []            
    if pattern == 'ABBA':
        # group by four dith pos
        groups = zip(*[iter(cdslist)]*4)
        dithgroups = [group for group in zip(*groups)]
        HWP_PA = ['00','45','22','67']
        for files,HWP in zip(groups,HWP_PA):
            fA1,fB1,fB2,fA2 = files

            outfile0 = '.'.join([prefix,section,HWP,'0','fits'])
            outfile0 = os.path.join(ditherdir,outfile0)
            outfile1 = '.'.join([prefix,section,HWP,'1','fits'])
            outfile1 = os.path.join(ditherdir,outfile1)

            if not sim:
                data0,header0 = combine(fA1,fB1,method='sub')
                header0['DITHPOS'] = (0,'0=A1-B1,1=A2-B2')
                header0['OBSSEC'] = (section,'Observation section')
                data1,header1 = combine(fA2,fB2,method='sub')
                header1['DITHPOS'] = (1,'0=A1-B1,1=A2-B2')
                header1['OBSSEC'] = (section,'Observation section')
                with warnings.catch_warnings():
                    warnings.simplefilter('ignore')
                    pyfits.writeto(outfile0,data0,header0,clobber=True)
                    pyfits.writeto(outfile1,data1,header1,clobber=True)
                
            outlist.append((outfile0,outfile1))

            
    print 'Dither pairs \t-> %s' % ditherdir
    return outlist
        

def nudge(filelist,step=5.0,outdir='.',ext=''):

    try:
        os.mkdir(outdir)
    except OSError:
        # directory exists
        pass
    
    try:
        compfiles = nudge_align.pipe_run(filelist,step=step,outdir=outdir,ext=ext,clobber=True)
    except Exception as e:
        print e
        print "'nudge_align.py' failed.  Images might not be aligned"
        return filelist

    else:
        # copy f00 file to directory
        d00,h00 = pyfits.getdata(filelist[0],header=True)
        h00['N_ORIG_F'] = (filelist[0],'Original file before nudge')
        h00['N_XS'] = (0,'Xshift of nudge')
        h00['N_YS'] = (0,'Yshift of nudge')
        f00 = os.path.basename(filelist[0])
        f00 = os.path.splitext(f00)
        f00 = ''.join([f00[0],ext,f00[1]])
        f00 = os.path.join(outdir,f00)

        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            pyfits.writeto(f00,d00,header=h00,clobber=True)
        return [f00] + compfiles
    

def qu_pair_subtract(dithlist,section,prefix,pattern,qudir='qupair',sim=False):
    if not sim:
        try:
            os.mkdir(qudir)
        except OSError:
            # directory exists
            pass

    outlist = []            
    if pattern == 'ABBA':
        # group two obs positions
        dith0,dith1 = zip(*dithlist)
        f00_0, f45_0, f22_0, f67_0 = dith0
        f00_1, f45_1, f22_1, f67_1 = dith1

        outfileQ0 = '.'.join([prefix,section,'Q','0','fits'])
        outfileQ0 = os.path.join(qudir,outfileQ0)
        outfileU0 = '.'.join([prefix,section,'U','0','fits'])
        outfileU0 = os.path.join(qudir,outfileU0)

        outfileQ1 = '.'.join([prefix,section,'Q','1','fits'])
        outfileQ1 = os.path.join(qudir,outfileQ1)
        outfileU1 = '.'.join([prefix,section,'U','1','fits'])
        outfileU1 = os.path.join(qudir,outfileU1)

        outlist = [outfileQ0,outfileU0,outfileQ1,outfileU1]

        if not sim:
            dataQ0, headerQ0 = combine(f00_0,f45_0,method='sub')
            headerQ0['POLPAIR'] = ('Q','Polarization pair (Q/U)')
            dataU0, headerU0 = combine(f22_0,f67_0,method='sub')
            headerU0['POLPAIR'] = ('U','Polarization pair (Q/U)')
            dataQ1, headerQ1 = combine(f00_1,f45_1,method='sub')
            headerQ1['POLPAIR'] = ('Q','Polarization pair (Q/U)')
            dataU1, headerU1 = combine(f22_1,f67_1,method='sub')
            headerU1['POLPAIR'] = ('U','Polarization pair (Q/U)')

            datalist = [dataQ0,dataU0,dataQ1,dataU1]
            headerlist = [headerQ0,headerU0,headerQ1,headerU1]
            
            with warnings.catch_warnings():
                warnings.simplefilter('ignore')
                for filename,data,header in zip(outlist,datalist,headerlist):
                    pyfits.writeto(filename,data,header,clobber=True)
    print 'QU pairs \t-> %s' % qudir
    return outlist


def main():
    parser = argparse.ArgumentParser(description='Process observations from .cfg file')
    parser.add_argument('cfg',type=str,help='Config file with obs params.')
    parser.add_argument('--sim',action='store_true',help='If specified, simulate without writing files')

    args = parser.parse_args()

    config = ConfigParser.SafeConfigParser()
    config.read(args.cfg)

    endlist = []
    
    for section in config.sections():
        # get filelist for each section
        filelist, secdir = proc_section(config, section, args.sim)

        pattern = config.get(section, 'dither_pattern')
        prefix = config.get(section, 'object')
        obs_per_pos = config.getint(section, 'obs_per_pos')
        
        # perform cdspair subtraction
        cdslist = cds_pair_subtract(filelist, secdir,sim=args.sim)

        # coadd multi obs per pos
        if obs_per_pos > 2:  
            cdslist = coadd_obs(cdslist,obs_per_pos,codir=os.path.join(secdir,'coaddobs'),sim=args.sim)

        # perform dither subtraction
        dithdir = os.path.join(secdir,'dithersub')
        dithlist = dither_subtract(cdslist,section,prefix,pattern,ditherdir=dithdir,sim=args.sim)

        # perform QU subtraction
        qudir = os.path.join(secdir,'qupair')
        qulist = qu_pair_subtract(dithlist,section,prefix,pattern,qudir=qudir,sim=args.sim)

        # combine dither pairs
        obspairdir = os.path.join(secdir,'obspair')
        obspairlist = obspair_sum(qulist,section,prefix,pattern,obspairdir=obspairdir,sim=args.sim)

        # wolly split
        wollydir = os.path.join(secdir,'wollysplit')
        wollylist = wolly_split(obspairlist,wollydir=wollydir,sim=args.sim)

        endlist.append((section,wollydir))
        print

    for section,wollydir in endlist:
        print '%s -> %s' % (section,wollydir)
    return 0
        
if __name__ == '__main__':
    main()
