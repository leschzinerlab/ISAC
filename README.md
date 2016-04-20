# ISAC
Repository with python wrapper for running ISAC (Iterative stable alignment and clustering) for analyzing single particle cryo-electron microscopy data.

## Dependencies
This program will run sxisac.py over a cluster using MPI. Therefore, you will need: 

* Sparx
* EMAN2parx
* MPI

Read more [here] (http://sparx-em.org/sparxwiki/Installer).

## Overall workflow

This program will perform the following preparatory steps on your particle stack from the command line (not submitted to a cluster yet)

1. Scale particles to box sizes of 64 x 64 pixels
2. Convert .img/hed stack to bdb format
3. Initialize header values to 0 for bdb stack
4. Center particles using sxali2d.py
5. Apply shifts from centering to particle stack
6. Write cluster submission script for user to submit

These preparation steps for ISAC were adapted from the [Run Through example on the Sparx wiki] (http://sparx-em.org/sparxwiki/RunThroughExample). 

## Running ISAC.py

Generally, users should not run computational tasks on cluster head nodes. Therefore, this script should be run from a cluster node directly. 

For us, we use the [Triton Shared Computing Cluster] (http://www.sdsc.edu/support/user_guides/tscc-quick-start.html) at UCSD where we can start an interactive node with a single cpu: 

<pre>$ qsub -I -l nodes=1:ppn=1 -l walltime=3:50:00</pre>

After on this node, we will run the ISAC.py command. When this command finishes, we log OUT of the interactive node and then submit the job: 

<pre> qsub isac_123333.submit</pre>

## Input options for ISAC.py

Generally, this script is meant to only require the particle stack in Imagic format. The box size can be any size, as the program will automatically rescale the box size down to 64 x 64 pixels.

Depending on your cluster setup, you will need to edit the queue names and cluster submission template within this python script. Contact us if you need help editing this. 

Commadn line options:
<pre>$ ./ISAC.py 
Usage: ISAC.py -i <stack> --nodes=<nodes> --threads=<threads>

Options:
  -h, --help      show this help message and exit
  -i FILE         Input stack
  --queue=STRING  Queue for job submission. (Default=hotel)
  --nodes=INT     Number of nodes to distribute job over. (Default=20)
  --threads=INT   Number of threads per node to run. (Default=8)
  --walltime=INT  Walltime for job (estimated run time, in hours). (Default=6)
  -d              debug</pre>
