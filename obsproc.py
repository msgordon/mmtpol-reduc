#! /usr/bin/env python
import argparse
import pyfits
import os
import glob



def get_filelist_by_range(prefix, start, stop):
    filelist = glob.glob('%s*' % prefix)
    numlist = [name.split('.')[1] for name in filelist]
    filelist = [name if ((num <= stop) or (num >= start)) for name,num in zip(filelist,numlist)]

    filelist.sort()
    return filelist

def main():
    parser = argparse.ArgumentParser(description='Process observations from .cfg file')
    parser.add_argument('cfg',type=str,help='Config file with obs params.')

    args = parser.parse_args()

    print get_filelist_by_range(MMTPol_2015Mar06,241,245)


if __name__ == '__main__':
    main()
