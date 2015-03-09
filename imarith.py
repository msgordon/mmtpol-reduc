#! /usr/bin/env python
import argparse
import pyfits
import numpy as np
import os
import warnings

def coadd(filelist,method='sum',out=None):
    folist = [pyfits.getdata(x,header=True) for x in filelist]
    data,headers = zip(*folist)
    if method == 'sum':
        data = np.sum(data,axis=0)

    elif method == 'median':
        data = np.median(data,axis=0)

    elif method == 'mean':
        data = np.mean(data,axis=0)

    else:
        print 'Invalid method %s' % method
        return None,None


    header = headers[0]
    header['COADD'] = (len(filelist),'Num files coadded')
    header['COADD_TY'] = (method,'Coadd type')

    if out:
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            pyfits.writeto(out,data,header=header,clobber=True)

    return data,header

def combine(op1f, op2f, method, out=None):
    op1 = pyfits.open(op1f)
    op2 = pyfits.open(op2f)

    header = op1[0].header

    if method == 'sum':
        data = op1[0].data + op2[0].data
    elif method == 'sub':
        data = op1[0].data - op2[0].data
    elif method == 'mult':
        data = op1[0].data * op2[0].data
    elif method == 'div':
        data = op1[0].data / op2[0].data
    elif method == 'mean':
        data = np.mean([op1[0].data, op2[0].data],axis=0)
    elif method == 'median':
        data = np.median([op1[0].data, op2[0].data],axis=0)
    else:
        print 'Invalid method %s' % method
        return None,None
        
    header['OP1'] = (op1f,'Operand1')
    header['OPER'] = (method,'Operation performed')
    header['OP2'] = (op2f,'Operand2')

    if out:
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
        pyfits.writeto(out,data,header=header,clobber=True)

    return data,header

def main():
    parser = argparse.ArgumentParser(description='Performs image arithmetic on input files')

    parser.add_argument('filelist',nargs='+',help='Input FILES files')
    parser.add_argument('out',type=str,help='Output file')
    parser.add_argument('-method',choices=('sum','sub','mult','div','mean','median'),default='sum',help='Operation (default="sum")')

    
    args = parser.parse_args()
    if len(filelist) < 2:
        print 'At least two files required'
        exit(1)

    if method in ['sub','div']:
        if len(filelist) != 2:
            print "Only two files allowed for method '%s'" % args.method
            exit(1)
        data,header = combine(args.filelist[0],args.filelist[1],args.method,args.out)

    else:
        data, header = coadd(args.filelist,method=args.method,out=args.out)

    if data is None:
        return 1

    return 0
    
if __name__ == '__main__':
    main()
