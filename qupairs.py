#! /usr/bin/env python
##05/20/2016
### NOT FINISHED
import argparse
import pyfits
from imarith import combine, coadd
import glob
import os
from obsproc import columns
from collections import defaultdict

class ObsSet(object):
    hwp_map = {0.0:'00',22.5:'22',45.0:'45',67.5:'67'}
    def __init__(self,bfiles,obsname):
        self.obsname = obsname
        self.Or = {self.hwp_map[b.hwp]:b for b in bfiles if b.beam == 'Or'}
        self.Ex = {self.hwp_map[b.hwp]:b for b in bfiles if b.beam == 'Ex'}

class BeamFile(object):
    def __init__(self,filename):
        self.filename = filename
        self.data,self.header = pyfits.getdata(filename,header=True)
        self.obs = self.header.get('OBSSEC')
        self.beam = self.header.get('BEAM')
        self.hwp = self.header.get('WPLATE')

    def __str__(self):
        return str((self.filename,self.obs,self.beam))

    def __repr__(self):
        return self.__str__()

def gather_files(dirname):
    files = glob.glob(os.path.join(dirname,'*.fits'))
    if not files:
        return None
    files.sort()
    return files

def split_by_obs(bfiles):
    obs_sets = defaultdict(list)
    for b in bfiles:
        obs_sets[b.obs].append(b)

    return obs_sets


def main():
    parser = argparse.ArgumentParser(description='Form Q and U files from aligned Or and Ex images')

    parser.add_argument('dir',type=str,help='Directory with Or and Ex files')
    parser.add_argument('-o',type=str,default='./qupair',help="Specify output directory (default='./qupair')")

    args = parser.parse_args()

    filelist = gather_files(args.dir)
    bfiles = [BeamFile(f) for f in filelist]

    obs = split_by_obs(bfiles)
    ObsSet(obs['OBS1'],'OBS1')
    #split_filelist(filelist)


if __name__ == '__main__':
    main()
