#! /usr/bin/env python
import argparse
import pyfits
import os
import glob
import ConfigParser
import cdspair
import wollysplit
from imarith import combine, coadd

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

    #print 'Coadding %i obs per position' % obs_per_pos
    # co add pairs
    groups = zip(*[iter(cdslist)]*obs_per_pos)
    coaddlist = []
    for group in groups:
        filenums = [x.split('.')[-2] for x in pair]
        outfile = os.path.basename(group[0]).split('.')[0]
        outfile = '.'.join([outfile]+filenums+['fits'])
        outfile = os.path.join(codir,outfile)

        coaddlist.append(outfile)

        if not sim:
            data, header = coadd(group,method='sum')
            pyfits.writeto(outfile,data,header,clobber=True)

    print 'Coadd obs \t-> %s' % codir
    return coaddlist


def obspair_sum(dithlist,section,prefix,pattern,obspairdir='obspair_sum',sim=False):
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
        Qdata,Qheader = combine(dithlist[0],dithlist[1],method='add')
        Udata,Uheader = combine(dithlist[2],dithlist[3],method='add')

        pyfits.writeto(Qfile,Qdata,Qheader,clobber=True)
        pyfits.writeto(Ufile,Udata,Uheader,clobber=True)

    print 'Obs pairs \t-> %s' % obspairdir
    return Qfile,Ufile

def dither_subtract(qulist,section,prefix,pattern,ditherdir='dithersub',sim=False):
    if not sim:
        try:
            os.mkdir(ditherdir)
        except OSError:
            # directory exists
            pass

    outlist = []
    if pattern == 'ABBA':
        Q0file = '.'.join([prefix,section,'Q','0','fits'])
        Q1file = '.'.join([prefix,section,'Q','1','fits'])
        U0file = '.'.join([prefix,section,'U','0','fits'])
        U1file = '.'.join([prefix,section,'U','1','fits'])

        outlist += [Q0file,Q1file,U0file,U1file]
        outlist = [os.path.join(ditherdir,x) for x in outlist]

        if not sim:
            Q0data,Q0header = combine(qulist[0][0],qulist[1][0],method='sub')
            U0data,U0header = combine(qulist[0][1],qulist[1][1],method='sub')
            Q1data,Q1header = combine(qulist[3][0],qulist[2][0],method='sub')
            U1data,U1header = combine(qulist[3][1],qulist[2][1],method='sub')

            pyfits.writeto(outlist[0],Q0data,Q0header,clobber=True)
            pyfits.writeto(outlist[1],Q1data,Q1header,clobber=True)
            pyfits.writeto(outlist[2],U0data,U0header,clobber=True)
            pyfits.writeto(outlist[3],U1data,U1header,clobber=True)

    print 'Dither pairs \t-> %s' % ditherdir
    return outlist
        
    

def qu_pair_subtract(cdslist,section,prefix,pattern,qudir='qupair',sim=False):
    if not sim:
        try:
            os.mkdir(qudir)
        except OSError:
            # directory exists
            pass

    outlist = []            
    if pattern == 'ABBA':
        # group by four HWP pos
        groups = zip(*[iter(cdslist)]*4)
        for files,pos,obs in zip(groups,pattern,['0','0','1','1']):
            f00,f45,f22,f67 = files
            outfileQ = '.'.join([prefix,section,pos,'Q',obs,'fits'])
            outfileQ = os.path.join(qudir,outfileQ)
            outfileU = '.'.join([prefix,section,pos,'U',obs,'fits'])
            outfileU = os.path.join(qudir,outfileU)
            if not sim:
                data, header = combine(f00,f45,method='sub')
                header['DITHPOS'] = (pos,'Dither position')
                header['POLPAIR'] = ('Q','Polarization pair (Q/U)')
                header['OBSSEC'] = (section, 'Observation section')
                pyfits.writeto(outfileQ,data,header,clobber=True)
                
                data, header = combine(f22,f67,method='sub')
                header['DITHPOS'] = (pos,'Dither position')
                header['POLPAIR'] = ('U','Polarization pair (Q/U)')
                header['OBSSEC'] = (section, 'Observation section')

                pyfits.writeto(outfileU,data,header,clobber=True)

            outlist.append((outfileQ,outfileU))
    
    print 'QU pairs \t-> %s' % qudir
    return outlist


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
        cdslist = cds_pair_subtract(filelist, secdir,sim=args.sim)

        # QU pair
        pattern = config.get(section, 'dither_pattern')
        obs_per_pos = config.getint(section, 'obs_per_pos')
        prefix = config.get(section, 'object')
        
        if obs_per_pos > 2:  
            cdslist = coadd_obs(cdslist,obs_per_pos,codir=os.path.join(secdir,'coaddobs'),sim=args.sim)
        
        qudir = os.path.join(secdir,'qupair')
        qulist = qu_pair_subtract(cdslist,section,prefix,pattern,qudir=qudir,sim=args.sim)

        
        #dither sub
        dithdir = os.path.join(secdir,'dither_sub')
        dithlist = dither_subtract(qulist,section,prefix,pattern,ditherdir=dithdir,sim=args.sim)

        # combine dither pairs
        obspairdir = os.path.join(secdir,'obspair')
        obspairlist = obspair_sum(dithlist,section,prefix,pattern,obspairdir=obspairdir,sim=args.sim)
        
        # wolly split
        wollydir = os.path.join(secdir,'wollysplit')
        wollylist = wolly_split(obspairlist,wollydir=wollydir,sim=args.sim)
        

        print

        
        
if __name__ == '__main__':
    main()
