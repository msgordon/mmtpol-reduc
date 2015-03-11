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

    elif method == 'quad':
        data = np.sqrt(np.sum([x**2 for x in data],axis=0))

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

def scalar_math(filename,scalar,method,out=None):
    data, header = pyfits.getdata(filename,header=True)
    if method == 'sum':
        data += scalar
    elif method == 'sub':
        data -= scalar
    elif method == 'mult':
        data *= scalar
    elif method == 'div':
        data /= scalar
    else:
        print 'Method %s not supported for scalar arithmetic' % method
        exit()
    
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
    elif method == 'quad':
        data = np.sqrt(op1[0].data**2 + op2[0].data**2)

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
    parser.add_argument('-o',required=True,type=str,help='Output file')
    parser.add_argument('-method',choices=('sum','sub','mult','div','mean','median','quad'),default='sum',help='Operation (default="sum")')
    parser.add_argument('-s',metavar='scalar',type=float,default=None,help='If specified, perform scalar arithmetic')

    
    args = parser.parse_args()
    if args.s is not None:
        if len(args.filelist) != 1:
            print 'Only one file allowed for scalar arithmetic'
            exit(1)
            
    
    if len(args.filelist) < 2:
        print 'At least two files required'
        exit(1)

        
    if args.method in ['sub','div']:
        if len(args.filelist) != 2:
            print "Only two files allowed for method '%s'" % args.method
            exit(1)
        data,header = combine(args.filelist[0],args.filelist[1],args.method,args.o)

    else:
        data, header = coadd(args.filelist,method=args.method,out=args.o)
        print '-> %s' % args.o

    if data is None:
        return 1

    return 0
    
if __name__ == '__main__':
    main()
