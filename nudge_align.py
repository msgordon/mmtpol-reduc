#! /usr/bin/env python
import argparse
import matplotlib.pyplot as plt
from scipy.ndimage.interpolation import shift
import pyfits
import os.path
from os import mkdir
import numpy as np
from ds9norm import DS9Normalize
from matplotlib.backend_bases import NavigationToolbar2, Event

home = NavigationToolbar2.home
def new_home(self, *args, **kwargs):
    s = 'home_event'
    event = Event(s, self)
    self.canvas.callbacks.process(s, event)
    home(self, *args, **kwargs)

NavigationToolbar2.home = new_home

def IQR(data):
    q75, q25 = np.percentile(data, [75 ,25])
    return q25,q75

class WindowParser(object):
    subparser = argparse.ArgumentParser(description='Parse window text.',prog='')

    def __init__(self, caller):
        if not isinstance(caller, Plotter):
            exit('WindowParser must be instantiated with a Plotter object')
            
        self.caller = caller
        
        self.subparser.add_argument('--stretch',choices=['linear','sqrt','arcsinh','log','power','squared'],help='Choose image stretch (default = stretch)')
        self.subparser.add_argument('-s',type=float,help='Step size (default=%.1f)' % self.caller.step)
        self.subparser.add_argument('-w',action='store_true',help="Write current frame to output directory (outdir=%s)"%self.caller.outdir)
        self.subparser.add_argument('-wa',action='store_true',help="Write all frames to output directory")
        self.subparser.add_argument('-wq',action='store_true',help="Write all frames to output directory and quit")
        self.subparser.add_argument('--c',action='store_true',help='Force clobber status to True on write')
        self.subparser.add_argument('-r',action='store_true',help='Restore original')

        self.subparser.add_argument('--clip_lo',type=float,help='Clip minimum intensity percentile')
        self.subparser.add_argument('--clip_hi',type=float,help='Clip maximum intensity percentile')
        self.subparser.add_argument('--vmin',type=float,help='Clip minimum intensity')
        self.subparser.add_argument('--vmax',type=float,help='Clip maximum intensity')
        self.subparser.add_argument('--q',action='store_true',help='Quit')
        

    def parse(self, text):
        try:
            # catch -h, or error exit
            args = self.subparser.parse_args(text.split())
        except SystemExit:
            return

        if not args:
            return

        if args.c:
            self.caller.clobber = True
            print 'Force clobber on write'
            
        if args.s:
            self.caller.step = args.s
            print 'Step size changed to %.2f' % args.s

        if args.w:
            h = pyfits.getheader(self.caller.compfiles[self.caller.current])
            h['N_ORIG_F'] = (self.caller.compfiles[self.caller.current],'Original file before nudge')
            h['N_XS'] = (self.caller.offsets[self.caller.current][0],'Xshift of nudge')
            h['N_YS'] = (self.caller.offsets[self.caller.current][1],'Yshift of nudge')
            outfile = os.path.basename(self.caller.compfiles[self.caller.current])
            outfile = os.path.splitext(outfile)
            outfile = ''.join([outfile[0],self.caller.ext,outfile[1]])
            outfile = os.path.join(self.caller.outdir,outfile)
            try:
                pyfits.writeto(outfile,data=self.caller.active_data,header=h,clobber=self.caller.clobber)
            except IOError as e:
                print e, "'--c' to force overwrite"
            else:
                print '%s: written to disk, s = [%.2f, %.2f]' % (outfile,self.caller.offsets[self.caller.current][0],self.caller.offsets[self.caller.current][1])

        if args.wq:
            args.wa = True
            args.q = True
                
        if args.wa:
            for idx in range(0,len(self.caller.compfiles)):
                h = pyfits.getheader(self.caller.compfiles[idx])
                h['N_ORIG_F'] = (self.caller.compfiles[idx],'Original file before nudge')
                h['N_XS'] = (self.caller.offsets[idx][0],'Xshift of nudge')
                h['N_YS'] = (self.caller.offsets[idx][1],'Yshift of nudge')
                outfile = os.path.basename(self.caller.compfiles[idx])
                outfile = os.path.splitext(outfile)
                outfile = ''.join([outfile[0],self.caller.ext,outfile[1]])
                outfile = os.path.join(self.caller.outdir,outfile)

                # Store for return
                self.caller.outfiles.append(outfile)
                
                try:
                    if idx == self.caller.current:
                        pyfits.writeto(outfile,data=self.caller.active_data,header=h,clobber=self.caller.clobber)
                    else:
                        pyfits.writeto(outfile,data=self.caller.compdata[idx],header=h,clobber=self.caller.clobber)
                except IOError as e:
                    print e, "'--c' to force overwrite"
                    args.q = False #don't quit if file fails to write
                else:
                    print '%s: written to disk, s = [%.2f, %.2f]' % (outfile,self.caller.offsets[idx][0],self.caller.offsets[idx][1])

        if args.stretch:
            print 'Changed stretch to %s' % args.stretch
            self.caller.norm.stretch = args.stretch
            self.caller.display()

        if args.clip_lo is not None:
            print 'Clip lo changed to %.2f' % args.clip_lo
            self.caller.norm.clip_lo = args.clip_lo
            self.caller.display()

        if args.clip_hi is not None:
            print 'Clip hi changed to %.2f' % args.clip_hi
            self.caller.norm.clip_hi = args.clip_hi
            self.caller.display()

        if args.vmin is not None:
            print 'Vmin changed to %.2f' % args.vmin
            self.caller.norm.vmin = args.vmin
            self.caller.display()

        if args.vmax is not None:
            print 'Vmax changed to %.2f' % args.vmax
            self.caller.norm.vmax = args.vmax
            self.caller.display()
            
        if args.r:
            self.caller.active_data = self.caller.orig_data.copy()
            self.caller.diff_update()
            self.caller.offsets[self.caller.current][0] = 0.0
            self.caller.offsets[self.caller.current][1] = 0.0
            plt.figure(self.caller.fig.number)
            plt.gca().set_xlim(self.caller.ixlim)
            plt.gca().set_ylim(self.caller.iylim)
            self.caller.norm = DS9Normalize(stretch='linear')
            self.caller.norm.vmin,self.caller.norm.vmax = IQR(self.caller.active_data)
            self.caller.display()
            print 'Restored image from %s' % self.caller.compfiles[self.caller.current]

        if args.q:
            plt.close()
            exit()


                    
class Plotter(object):

    def __init__(self, reffile, compfiles,
                 step=1.0,outdir='./nudged',ext='',clobber=False):

        self.reffile = reffile
        self.refdata = pyfits.getdata(self.reffile)

        self.compfiles = compfiles
        self.compdata = map(pyfits.getdata, self.compfiles)
        
        self.step = step
        self.outdir = outdir
        self.ext = ext
        self.clobber = clobber

        self.subparser = WindowParser(self)

        # Initialize offsets to zero
        self.offsets = np.zeros((len(self.compfiles),2))

        # Current displayed plot
        self.current = 0
        self.orig_data = pyfits.getdata(self.compfiles[0])
        self.active_data = self.orig_data

        # Difference
        self.diff_data = self.refdata - self.active_data

        # Initial limits
        self.ixlim = (0, self.active_data.shape[1])
        self.iylim = (0, self.active_data.shape[0])

        # Old limits
        self.oxlim = None
        self.oylim = None

        # Initialize norm
        self.norm = DS9Normalize(stretch='linear')
        self.norm.vmin,self.norm.vmax = IQR(self.active_data)

        self.fig, self.axes = plt.subplots(ncols=2)
        self.fig.subplots_adjust(top=0.9)

        # Connect handlers
        self.fig.canvas.mpl_disconnect(self.fig.canvas.manager.key_press_handler_id)
        self.keycid = self.fig.canvas.mpl_connect('key_press_event',self.onkey)
        self.fig.canvas.mpl_connect('draw_event', self.ondraw)
        self.fig.canvas.mpl_connect('home_event', self.onhome)


        # For return
        self.outfiles = []
        
        # Pausetext
        self.pausetext = '-'
        self.pid = None

        self.display()
        self.displaytext('[0, 0], s=%.2f'%self.step,x=0.3)

    def display(self):
        plt.figure(self.fig.number)
        plt.clf()

        red_cmap = plt.cm.Reds
        red_cmap.set_under(color="white", alpha="0")
        
        ax1 = plt.subplot(121)
        plt.title('Overlay %i/%i' % (self.current+1, len(self.compfiles)))
        static_im = plt.imshow(self.refdata,origin='lower',
                                        interpolation='none',
                                        norm=self.norm,cmap='gray')

        active_im = plt.imshow(self.active_data,origin='lower',
                                        cmap=red_cmap,interpolation='none',
                                        norm=self.norm,alpha=0.2)

        ax2 = plt.subplot(122, sharex = ax1, sharey = ax1)
        plt.title('Residual')
        residual_im = plt.imshow(self.diff_data,origin='lower',
                                 cmap='Blues',interpolation='none',
                                 norm=self.norm)
        self.fig.suptitle('%s|%s' % (os.path.basename(self.reffile),
                                     os.path.basename(self.compfiles[self.current])))

        if all([self.oxlim,self.oylim]):
            plt.gca().set_xlim(self.oxlim)
            plt.gca().set_ylim(self.oylim)

        self.fig.canvas.draw()

    def displaytext(self,text,x=0.1,y=0.02,remove=None):
        if remove:
            remove.remove()
        pid = plt.figtext(x, y, text)
        self.fig.canvas.draw()
        return pid

    def diff_update(self):
        self.diff_data = self.refdata - self.active_data
        return


    def show(self):
        plt.show()
        

    def onkey(self, event):
        if event.key in ['.','>']:
            if self.current >= len(self.compfiles)-1:
                return
            self.compdata[self.current] = self.active_data
            self.current += 1
            self.orig_data = pyfits.getdata(self.compfiles[self.current])
            self.active_data = self.compdata[self.current]
            self.diff_update()
            
        elif event.key in [',','<']:
            if self.current == 0:
                return
            self.compdata[self.current] = self.active_data
            self.current -= 1
            
            self.orig_data = pyfits.getdata(self.compfiles[self.current])
            self.active_data = self.compdata[self.current]
            self.diff_update()

        elif event.key == '-':
            self.fig.canvas.mpl_disconnect(self.keycid)
            self.pausetext = '-'
            self.pid = self.displaytext(self.pausetext)
            self.keycid = self.fig.canvas.mpl_connect('key_press_event',self.pausekey)
            return

        elif event.key == 'left':
            if self.active_data is None:
                return
            self.active_data = shift(self.active_data,[0,-self.step])
            self.diff_update()
            self.offsets[self.current][0] -= self.step

        elif event.key == 'right':
            if self.active_data is None:
                return
            self.active_data = shift(self.active_data,[0,self.step])
            self.diff_update()
            self.offsets[self.current][0] += self.step

        elif event.key == 'down':
            if self.active_data is None:
                return
            self.active_data = shift(self.active_data,[-self.step,0])
            self.diff_update()
            self.offsets[self.current][1] -= self.step

        elif event.key == 'up':
            if self.active_data is None:
                return
            self.active_data = shift(self.active_data,[self.step,0])
            self.diff_update()
            self.offsets[self.current][1] += self.step

        elif event.key == 'h':
            self.onhome(None)
            return

        self.display()
        self.displaytext('[%.2f, %.2f] s=%.2f'%
                         (self.offsets[self.current][0],
                          self.offsets[self.current][1],
                          self.step), x=0.3)


    def pausekey(self,event):
        if event.key == 'enter':
            self.fig.canvas.mpl_disconnect(self.keycid)
            self.keycid = self.fig.canvas.mpl_connect('key_press_event',self.onkey)
            self.subparser.parse(self.pausetext)
            self.pausetext = '-'
            self.display()

            self.displaytext('[%.2f, %.2f] s=%.2f'%
                             (self.offsets[self.current][0],
                              self.offsets[self.current][1],
                              self.step),x=0.3)
            return

        elif event.key == 'backspace':
            self.pausetext = self.pausetext[0:-1]
            
        elif len(event.key) > 1:
            return
            
        else:
            self.pausetext = ''.join([self.pausetext,event.key])

        self.pid = self.displaytext(self.pausetext,remove=self.pid)
        return

        
    def ondraw(self,event):
        # handle zoom
        plt.figure(self.fig.number)
        cx = plt.gca().get_xlim()
        cy = plt.gca().get_ylim()
        
        if cx != self.oxlim or cy != self.oylim:
            self.oxlim = cx
            self.oylim = cy

        return

    def onhome(self,event):
        plt.figure(self.fig.number)
        plt.gca().set_ylim(self.iylim)
        plt.gca().set_xlim(self.ixlim)
        self.fig.canvas.draw()



def pipe_run(filelist,step=5.0,outdir='.',ext='',clobber=True):
    reffile = filelist[0]
    compfiles = filelist[1:]
    plotter = Plotter(reffile,compfiles,step,outdir,ext,clobber)
    plotter.show()
    return plotter.outfiles

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
    plotter = Plotter(reffile,compfiles,args.s,args.o,args.e,args.c)
    plotter.show()


if __name__ == '__main__':
    main()
