import Tkinter,tkFileDialog
import os, sys


def main(filelist, outdir):
	for f in filelist:
		print f
	print "Outdir is %s" %outdir

if __name__ == '__main__':

    root = Tkinter.Tk()
    root.withdraw()
    # Select files to parse
    filelist = tkFileDialog.askopenfilenames(parent=root,title='Choose files to parse')
    filelist = list(filelist)
    # Select output directory to save out to
    outdir = tkFileDialog.askdirectory(parent=root,initialdir=os.getcwd(), title='Please select output directory')
    # Run script
    main(filelist, outdir)