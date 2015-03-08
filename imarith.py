#! /usr/bin/env python
import argparse
import pyfits
import numpy as np
import os

def coadd(filelist,method='sum',out=None):
    folist = [pyfits.getdata(x,header=True) for x in filelist]
    data,headers = zip(*flist)
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
        pyfits.writeto(out,data,header=header,clobber=True)

    return data,header

def combine(op1f, op2f, method, out=None):
    op1 = pyfits.open(op1f)
    op2 = pyfits.open(op2f)

    header = op1[0].header

    if method == 'add':
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
        pyfits.writeto(out,data,header=header,clobber=True)

    return data,header

def main():
    parser = argparse.ArgumentParser(description='Performs image arithmetic on input files')
    parser.add_argument('op1',type=str,help='Image file, operand 1')
    parser.add_argument('op2',type=str,help='Image file, operand 2')
    parser.add_argument('out',type=str,help='Output file')
    parser.add_argument('-method',choices=('add','sub','mult','div','mean','median'),default='sub',help='Operation (default="sub")')

    
    args = parser.parse_args()

    data,header = combine(args.op1,args.op2,args.method,args.out)

    if data is None:
        return 1

    return 0
    
if __name__ == '__main__':
    main()
