#!/usr/bin/env python


import optparse
from sys import *
import os,sys,re
from optparse import OptionParser
import glob
import subprocess
from os import system
import linecache
import time
#=========================
def setupParserOptions():
        parser = optparse.OptionParser()
        parser.set_usage("%prog -i <stack> --nodes=<nodes> --threads=<threads>")
        parser.add_option("-i",dest="stack",type="string",metavar="FILE",
                help="Input stack")
        #parser.add_option("--apix",dest="apix",type="float", metavar="FLOAT",
        #        help="Pixel size")
	#parser.add_option("--lp",dest="lp",type="int", metavar="INT",default=15,
        #        help="Low pass filter to use during alignment. (Default=15 A)")
	#parser.add_option("--hp",dest="hp",type="int", metavar="INT",default=500,
        #        help="High pass filter to use during alignment. (Default=500 A)")
	parser.add_option("--queue",dest="queue",type="string", metavar="STRING",default='hotel',
                help="Queue for job submission. (Default=hotel)")
	parser.add_option("--nodes",dest="nodes",type="int", metavar="INT",default=20,
                help="Number of nodes to distribute job over. (Default=20)")
	parser.add_option("--threads",dest="threads",type="int", metavar="INT",default=8,
                help="Number of threads per node to run. (Default=8)")
	parser.add_option("--walltime",dest="walltime",type="int", metavar="INT",default=6,
                help="Walltime for job (estimated run time, in hours). (Default=6)")
	parser.add_option("-d", action="store_true",dest="debug",default=False,
                help="debug")
        options,args = parser.parse_args()

        if len(args) > 1:
                parser.error("Unknown commandline options: " +str(args))

        if len(sys.argv) < 3:
                parser.print_help()
                sys.exit()
        params={}
        for i in parser.option_list:
                if isinstance(i.dest,str):
                        params[i.dest] = getattr(options,i.dest)
        return params
#=============================
def checkConflicts(params):

	if not os.path.exists(params['stack']):
		print 'Error: stack %s does not exist. Exiting' %(params['stack'])
		sys.exit()

	if params['stack'][-4:] != '.img':
		print 'Error: stack extension %s is not recognized as .img. Exiting' %(params['stack'][4:])
		sys.exit()

	if os.path.exists('dir_%s' %(params['stack'][:-4])):
		print 'Error: output directory dir_%s already exists. Exiting.' %(params['stack'][:-4])
		sys.exit()
		
#=========================
def getEMANPath():
        emanpath = subprocess.Popen("env | grep EMAN2DIR", shell=True, stdout=subprocess.PIPE).stdout.read().strip()

        if emanpath:
                emanpath = emanpath.replace("EMAN2DIR=","")
        if os.path.exists(emanpath):
                return emanpath
        print "EMAN2 was not found, make sure it is in your path"
        sys.exit()

#==============================
def convertIMG_to_BDB(params,scaling):

	print '\n'	
	print 'Converting imagic stack to BDB format: %s.img -----> bdb:%s' %(params['stack'][:-4],params['stack'][:-4])
	print '...this can take a while\n' 
	
	#Remove existing images if they are there
	if os.path.exists('EMAN2DB/%s.bdb' %(params['stack'][:-4])):
		os.remove('EMAN2DB/%s.bdb' %(params['stack'][:-4]))
		os.remove('EMAN2DB/%s_64x64x1' %(params['stack'][:-4]))

	if os.path.exists('EMAN2DB/%s_ali.bdb' %(params['stack'][:-4])):
                os.remove('EMAN2DB/%s_ali.bdb' %(params['stack'][:-4]))
                os.remove('EMAN2DB/%s_ali_64x64x1' %(params['stack'][:-4]))

	#Convert stack from imagic to bdb format
	cmd='e2proc2d.py %s.img bdb:%s --scale=%f --clip=64,64' %(params['stack'][:-4],params['stack'][:-4],float(scaling))
	if params['debug'] is True:
		print cmd
	subprocess.Popen(cmd,shell=True).wait()	

	return 'bdb:%s' %(params['stack'][:-4])

#==============================
def getBoxSize(stack):

	cmd='iminfo %s > tmp2222.txt' %(stack)
	subprocess.Popen(cmd,shell=True).wait()	

	line=linecache.getline('tmp2222.txt',4)
	boxsize=int(line.split()[-1].split('x')[0])

	os.remove('tmp2222.txt')

	return boxsize

#=============================
def submitISAC(bdbstack,queue,nodes,threads,walltime):

	subscript='isac_%i.submit'%(int(time.time()))	
	o1=open(subscript,'w')
	cmd='#!/bin/bash\n'
	cmd+='### Inherit all current environment variables\n'
	cmd+='#PBS -V\n'
	cmd+='### Job name\n'
	cmd+='#PBS -N isac1\n'
	cmd+='### Keep Output and Error\n'
	cmd+='#PBS -o isac.o$PBS_JOBID\n'
	cmd+='#PBS -e isac.e$PBS_JOBID\n'
	cmd+='### Queue name\n'
	cmd+='#PBS -q %s\n' %(queue)
	cmd+='### Specify the number of nodes and thread (ppn) for your job.\n'
	cmd+='#PBS -l nodes=%i:ppn=%i\n' %(nodes,threads)
	cmd+='### Tell PBS the anticipated run-time for your job, where walltime=HH:MM:SS\n'
	cmd+='#PBS -l walltime=%i:00:00\n'%(walltime)
	cmd+='#################################\n'
	cmd+='### Switch to the working directory;\n'
	cmd+='cd $PBS_O_WORKDIR\n'
	cmd+='### Run:\n'
	cmd+='mpirun  /home/micianfrocco/software/EMAN2-2.12/bin/sxisac.py %s --stab_ali=2 --init_iter=1 --main_iter=1 --match_second=1 --radius=30 --max_round=5 --img_per_grp=60 --thld_err=1.75 --n_generations=1\n' %(bdbstack)
	
	o1.write(cmd)

	print '\n...Submission script generated.\n'

	print '\n Submit ISAC using the following command: \n'

	print '\n qsub %s' %(subscript)
	
#==============================
if __name__ == "__main__":

        params=setupParserOptions()
        getEMANPath()
	checkConflicts(params)
        boxSize=getBoxSize(params['stack'])
	ScalingFactor=64/float(boxSize)
	if params['debug'] is True:
		print 'ScalingFactor=%f' %(ScalingFactor)
		print 'BoxSize=%f' %(boxSize)
	
	#Filter stack
	if os.path.exists('%s_filt.img' %(params['stack'][:-4])):
		os.remove('%s_filt.img' %(params['stack'][:-4]))
	if os.path.exists('%s_filt.hed' %(params['stack'][:-4])):
                os.remove('%s_filt.hed' %(params['stack'][:-4]))

	#cmd='proc2d %s %s_filt.img apix=%f hp=%i lp=%i' %(params['stack'],params['stack'][:-4],params['apix'],params['hp'],params['lp'])
	#if params['debug'] is True:
        #        print cmd
        #subprocess.Popen(cmd,shell=True).wait()

	bdbstack=convertIMG_to_BDB(params,ScalingFactor)

	#prepare stack for isac
	print '\n ...Initializing stack...\n'
	cmd='sxheader.py %s --params=active --one' %(bdbstack)
	if params['debug'] is True:
		print cmd
	subprocess.Popen(cmd,shell=True).wait()
	
	cmd='sxheader.py %s --params=xform.align2d --zero' %(bdbstack)
	if params['debug'] is True:
                print cmd
	subprocess.Popen(cmd,shell=True).wait()

	#Centering particles
	print '\n ...Centering particles...\n'
	cmd='mpirun -np 1 sxali2d.py %s dir_%s --ou=28 --xr="2 1" --ts="1 0.5" --maxit=33 --dst=90 --MPI' %(bdbstack,params['stack'][:-4])
	if params['debug'] is True:
                print cmd
        subprocess.Popen(cmd,shell=True).wait()

	#Rotate particles according to centering
	print '\n ...Applying alignments from centering to particle stack...\n'
	cmd='sxtransform2d.py %s %s_ali' %(bdbstack,bdbstack)
	if params['debug'] is True:
                print cmd
        subprocess.Popen(cmd,shell=True).wait()

	#Create cluster submission script & submit job
	submitISAC('%s_ali' %(bdbstack),params['queue'],params['nodes'],params['threads'],params['walltime'])

