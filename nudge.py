#! /usr/bin/env python
import argparse
import matplotlib.pyplot as plt
import matplotlib.patheffects as PE
from scipy.ndimage.interpolation import shift
import pyfits
import os.path
from os import mkdir
import numpy as np
from ds9norm import DS9Normalize
from mpl_toolkits.axes_grid1 import make_axes_locatable
from matplotlib.backend_bases import NavigationToolbar2, Event

def IQR(data):
    q75, q25 = np.percentile(data, [75 ,25])
    return q25,q75

home = NavigationToolbar2.home
def new_home(self, *args, **kwargs):
    s = 'home_event'
    event = Event(s, self)
    self.canvas.callbacks.process(s, event)
    home(self, *args, **kwargs)

NavigationToolbar2.home = new_home

dplotter = None

'''
def handle_update(event):
    if dplotter:
        dplotter.active_data = dplotter.refP.active_data - \
                               dplotter.linkedP.active_data
        dplotter.display(dplotter.active_data)
'''
        
class Plotter(object):
    def handle_home(self,event):
        plt.figure(self.fig.number)
        plt.gca().set_ylim(self.iylim)
        plt.gca().set_xlim(self.ixlim)
        self.fig.canvas.draw()

    def handle_draw(self,event):
        # handle zoom
        plt.figure(self.fig.number)
        cx = plt.gca().get_xlim()
        cy = plt.gca().get_ylim()

        if cx != self.oxlim or cy != self.oylim:
            self.oxlim = cx
            self.oylim = cy

        if not self.static and self is not dplotter:
            if dplotter:
                dplotter.active_data = dplotter.refP.active_data - \
                                       dplotter.linkedP.active_data
                dplotter.display(dplotter.active_data,fig=dplotter.fig.number)


    
    def __init__(self,filelist, step=1.0,outdir='./nudged/',
                 ext='',clobber=False, static = False,title=None):

        #self.reffile = filelist[0]
        #self.refdata = pyfits.getdata(self.reffile)
        
        self.filelist = filelist
        self.title = title

        self.static = static

        if isinstance(self.filelist[0],Plotter):
            self.static = True
            self.linked = True

        else:
            self.linked = False

            
        # datalist holds current state of arrays
        if not self.static:
            self.datalist = map(pyfits.getdata,self.filelist)
            self.orig_data = pyfits.getdata(self.filelist[0])
            # store total offsets
            self.offsets = np.zeros((len(self.filelist),2))

        else:
            if self.linked:
                self.refP = self.filelist[0]
                self.linkedP = self.filelist[1]
                self.orig_data = self.refP.active_data - \
                                 self.linkedP.active_data

            else:
                self.orig_data = pyfits.getdata(self.filelist)

        self.step = step
        self.outdir = outdir
        self.ext = ext
        self.clobber = clobber
        self.current = 0
        

        self.active_data = self.orig_data

        self.iylim = (0,self.active_data.shape[0])
        self.ixlim = (0,self.active_data.shape[1])



        self.oxlim = None
        self.oylim = None

        # initialize norm
        self.norm = DS9Normalize(stretch='linear')
        vmin,vmax = IQR(self.active_data)
        self.norm.vmin = vmin
        self.norm.vmax = vmax

        # set up subparser
        self.subparser=argparse.ArgumentParser(description='Parse window text.',prog='')
        self.subparser.add_argument('--stretch',choices=['linear','sqrt','arcsinh','log','power','squared'],help='Choose image stretch (default = stretch)')
        self.subparser.add_argument('--clip_lo',type=float,help='Clip minimum intensity percentile')
        self.subparser.add_argument('--clip_hi',type=float,help='Clip maximum intensity percentile')
        self.subparser.add_argument('--vmin',type=float,help='Clip minimum intensity')
        self.subparser.add_argument('--vmax',type=float,help='Clip maximum intensity')
        if not self.static:
            self.subparser.add_argument('-s',type=float,help='Step size (default=%.1f)' % self.step)
            self.subparser.add_argument('-w',action='store_true',help="Write current frame to output directory (outdir=%s)"%self.outdir)
            self.subparser.add_argument('-wa',action='store_true',help="Write all frames to output directory (outdir=%s)"%self.outdir)
            self.subparser.add_argument('-wq',action='store_true',help="Write all frames to output directory and quit (outdir=%s)"%self.outdir)
            self.subparser.add_argument('--c',action='store_true',help='Force clobber status to True on write')
            
        self.subparser.add_argument('-r',action='store_true',help='Restore original')

            
        self.subparser.add_argument('--q',action='store_true',help='Quit')

            
        self.fig = plt.figure()
        self.fig.canvas.mpl_disconnect(self.fig.canvas.manager.key_press_handler_id)
        self.keycid = self.fig.canvas.mpl_connect('key_press_event',self.onkey)
        
        self.fig.canvas.mpl_connect('button_press_event', self.onclick)
        self.fig.canvas.mpl_connect('button_release_event', self.onrelease)
        self.fig.canvas.mpl_connect('draw_event', self.handle_draw)

        self.fig.canvas.mpl_connect('home_event', self.handle_home)

        #if not self.static:
        #    self.fig.canvas.mpl_connect('draw_event',handle_update)

        
        # Hold x,y drag coords
        self.dragfrom = None
        
        self.pausetext = '-'
        self.pid = None


        # Make directory if doesn't exist
        if not self.static:
            try:
                mkdir(self.outdir)
            except OSError:
                #directory exists. no big deal.
                pass

                
            print "Type directly into figure"
            print "'left/right/up/down' to translate image"
            print "'</>' to choose previous/next image in input list"
            print "'-h' to see additional options"
            print "'--q' to quit"
            print
        
        #Show initial
        self.display(self.active_data,init=True)

        if not self.static:
            self.displaytext('[0, 0], s=%.2f'%self.step,x=0.60)
        

    def display(self, data, fig = None,title=None,init=False):
        if fig:
            plt.figure(fig)
        else:
            plt.figure(self.fig.number)

        plt.clf()
        im = plt.imshow(data,origin='lower',interpolation='none',norm=self.norm,cmap='gray')
        if title:
            plt.title(title)
        elif self.title:
            plt.title(self.title)
        else:
            plt.title(self.filelist[self.current])


        #divider = make_axes_locatable(plt.gca())
        #cb = plt.colorbar(im,orientation='horizontal')
        #l,b,w,h = plt.gca().get_position().bounds
        if not init:
            plt.figure(self.fig.number)
            plt.gca().set_xlim(self.oxlim)
            plt.gca().set_ylim(self.oylim)

        if not self.static:
            plt.figure(self.fig.number)
            plt.gca().set_position((0,0.1,1,0.8))
        plt.gcf().canvas.draw()
        

    def displaytext(self,text,x=0.1,y=0.02,fig=None,remove=None):
        if fig:
            plt.figure(fig)
        else:
            plt.figure(self.fig.number)
        
        if remove:
            remove.remove()
        pid = plt.figtext(x, y, text)
        '''
        pid = plt.text(x,y,text,color='k',
                       horizontalalignment='left',
                       verticalalignment='bottom',
                       transform=plt.gca().transAxes,
                       path_effects=[PE.withStroke(linewidth=2,foreground='k')])
        '''
        self.fig.canvas.draw()
        return pid
        


    def parsetext(self,text):
        args = None
        
        try:
            # catch -h, or error exit
            args = self.subparser.parse_args(text.split())
        except SystemExit:
            return
            
        if not args:
            return

        if not self.static:
            if args.c:
                self.clobber = True
                print 'Force clobber on write'
            
            if args.s:
                self.step = args.s
                print 'Step size changed to %.2f' % self.step

            if args.w:
                h = pyfits.getheader(self.filelist[self.current])
                h['N_ORIG_F'] = (self.filelist[self.current],'Original file before nudge')
                h['N_XS'] = (self.offsets[self.current][0],'Xshift of nudge')
                h['N_YS'] = (self.offsets[self.current][1],'Yshift of nudge')
                outfile = os.path.basename(self.filelist[self.current])
                outfile = os.path.splitext(outfile)
                outfile = ''.join([outfile[0],self.ext,outfile[1]])
                outfile = os.path.join(self.outdir,outfile)
                try:
                    pyfits.writeto(outfile,data=self.active_data,header=h,clobber=self.clobber)
                except IOError as e:
                    print e, "'--c' to force overwrite"
                else:
                    print '%s: written to disk, s = [%.2f, %.2f]' % (outfile,self.offsets[self.current][0],self.offsets[self.current][1])

            if args.wq:
                args.wa = True
                args.q = True
                
            if args.wa:
                for idx in range(0,len(self.filelist)):
                    h = pyfits.getheader(self.filelist[idx])
                    h['N_ORIG_F'] = (self.filelist[idx],'Original file before nudge')
                    h['N_XS'] = (self.offsets[idx][0],'Xshift of nudge')
                    h['N_YS'] = (self.offsets[idx][1],'Yshift of nudge')
                    outfile = os.path.basename(self.filelist[idx])
                    outfile = os.path.splitext(outfile)
                    outfile = ''.join([outfile[0],self.ext,outfile[1]])
                    outfile = os.path.join(self.outdir,outfile)
                    try:
                        if idx == self.current:
                            pyfits.writeto(outfile,data=self.active_data,header=h,clobber=self.clobber)
                        else:
                            pyfits.writeto(outfile,data=self.datalist[idx],header=h,clobber=self.clobber)
                    except IOError as e:
                        print e, "'--c' to force overwrite"
                        args.q = False #don't quit if file fails to write
                    else:
                        print '%s: written to disk, s = [%.2f, %.2f]' % (outfile,self.offsets[idx][0],self.offsets[idx][1])


        if args.stretch:
            print 'Changed stretch to %s' % args.stretch
            self.norm.stretch = args.stretch
            self.display(self.active_data)

        if args.clip_lo is not None:
            print 'Clip lo changed to %.2f' % args.clip_lo
            self.norm.clip_lo = args.clip_lo
            self.display(self.active_data)

        if args.clip_hi is not None:
            print 'Clip hi changed to %.2f' % args.clip_hi
            self.norm.clip_hi = args.clip_hi
            self.display(self.active_data)

        if args.vmin is not None:
            print 'Vmin changed to %.2f' % args.vmin
            self.norm.vmin = args.vmin
            self.display(self.active_data)

        if args.vmax is not None:
            print 'Vmax changed to %.2f' % args.vmax
            self.norm.vmax = args.vmax
            self.display(self.active_data)
            
        if args.r:
            self.active_data = self.orig_data.copy()
            self.offsets[self.current][0] = 0.0
            self.offsets[self.current][1] = 0.0
            plt.gca().set_xlim(self.ixlim)
            plt.gca().set_ylim(self.iylim)
            self.norm = DS9Normalize(stretch='linear')
            self.norm.vmin,self.norm.vmax = IQR(self.active_data)
            self.display(self.active_data,init=True)
            print 'Restored image from %s' % self.filelist[self.current]

        if args.q:
            plt.close()
            exit()


        
    def pausekey(self,event):
        if event.key == 'enter':
            self.fig.canvas.mpl_disconnect(self.keycid)
            self.keycid = self.fig.canvas.mpl_connect('key_press_event',self.onkey)
            self.parsetext(self.pausetext)
            self.pausetext = '-'
            self.display(self.active_data)

            if not self.static:
                self.displaytext('[%.2f, %.2f] s=%.2f'%
                                 (self.offsets[self.current][0],
                                  self.offsets[self.current][1],
                                  self.step),
                                 x=0.60)
            return

        elif event.key == 'backspace':
            self.pausetext = self.pausetext[0:-1]
            
        elif len(event.key) > 1:
            return
            
        else:
            self.pausetext = ''.join([self.pausetext,event.key])

        self.pid = self.displaytext(self.pausetext,remove=self.pid)
        return
        
    
    def onkey(self, event):
        if event.key in ['.','>']:
            if self.static:
                return
            if self.current >= len(self.filelist)-1:
                return
            self.datalist[self.current] = self.active_data
            self.current += 1
            self.orig_data = pyfits.getdata(self.filelist[self.current])
            self.active_data = self.datalist[self.current]
            
        elif event.key in [',','<']:
            if self.static:
                return
            if self.current == 0:
                return
            self.datalist[self.current] = self.active_data
            self.current -= 1
            
            self.orig_data = pyfits.getdata(self.filelist[self.current])
            self.active_data = self.datalist[self.current]

        elif event.key == '-':
             self.fig.canvas.mpl_disconnect(self.keycid)
             self.pausetext = '-'
             self.pid = self.displaytext(self.pausetext)
             self.keycid = self.fig.canvas.mpl_connect('key_press_event',self.pausekey)
             return

        elif event.key == 'left':
            if self.static:
                return
            if self.active_data is None:
                return
            self.active_data = shift(self.active_data,[0,-self.step])
            self.offsets[self.current][0] -= self.step

        elif event.key == 'right':
            if self.static:
                return
            if self.active_data is None:
                return
            self.active_data = shift(self.active_data,[0,self.step])
            self.offsets[self.current][0] += self.step

        elif event.key == 'down':
            if self.static:
                return
            if self.active_data is None:
                return
            self.active_data = shift(self.active_data,[-self.step,0])
            self.offsets[self.current][1] -= self.step

        elif event.key == 'up':
            if self.static:
                return
            if self.active_data is None:
                return
            self.active_data = shift(self.active_data,[self.step,0])
            self.offsets[self.current][1] += self.step

        self.display(self.active_data)
        if not self.static:
            self.displaytext('[%.2f, %.2f] s=%.2f'%
                             (self.offsets[self.current][0],
                              self.offsets[self.current][1],
                              self.step),
                             x=0.60)


    def onclick(self, event):
        if event.button == 3:  # rightclick
            #start dragfrom
            self.dragfrom = [event.xdata, event.ydata]

    def onrelease(self, event):
        if event.button != 3 and self.dragfrom is not None:
            return

        try:
            dx = self.dragfrom[0] - event.xdata
            dy = self.dragfrom[1] - event.ydata

        except:
            return

        self.dragfrom = None

        trans = 2.0
        fx = trans * dx/np.abs(np.diff(self.fig.gca().get_xlim()))
        fy = trans * dy/np.abs(np.diff(self.fig.gca().get_ylim()))

        bias = self.norm.bias - fx
        if bias > 1:
            self.norm.bias = 1.0
        elif bias < 0.01:
            self.norm.bias = 0.01
        else:
            self.norm.bias = bias

        contrast = self.norm.contrast - fy
        if contrast > 2:
            self.norm.contrast = 2.0
        elif contrast < -2:
            self.norm.contrast = -2.0
        else:
            self.norm.contrast = contrast
        
        self.display(self.active_data,fig=event.canvas.figure.number)


def main():
    parser = argparse.ArgumentParser(description='Nudge an image, or series of images, by a given step size')
    parser.add_argument('filelist',nargs='+',help='List of input FITS files to be nudged.')
    parser.add_argument('-s',type=float,default=5.0,help='Specify initial step size (default=5.0).')
    parser.add_argument('-o',type=str,default='./nudged/',help="Output directory (default='./nudged/').")
    parser.add_argument('-e',type=str,default='',help="Prefix for filename extension on output (default='').")
    parser.add_argument('--c',action='store_true',help="Clobber on output (default=False.")

    args = parser.parse_args()

    # first file is reference
    reffile = args.filelist[0]
    compfiles = args.filelist[1:]

    rplotter = Plotter(reffile,static=True,title='REF %s' % reffile)
    cplotter = Plotter(compfiles,args.s,args.o,args.e,args.c)
    global dplotter
    dplotter = Plotter([rplotter,cplotter],title='RESIDUAL')
    plt.show()

    


if __name__ == '__main__':
    main()







