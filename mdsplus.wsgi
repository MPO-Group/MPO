import mod_wsgi
import subprocess,os
os.environ["UDP_EVENTS"]="yes"
os.environ["MDS_PATH"]="/usr/local/cmod/tdi;/usr/local/mdsplus/tdi"
os.environ["PATH"]="/usr/local/mdsplus/bin:"+os.environ["PATH"]
os.environ["LD_LIBRARY_PATH"]="/usr/local/mdsplus/lib"
p=subprocess.Popen('. /usr/local/mdsplus/setup.sh; printenv | grep _path=',stdout=subprocess.PIPE,shell=True)
s=p.wait()
defs=p.stdout.read().split('\n')[:-1]
p.stdout.close()
for env in defs:
	ps=env.split('=')
        os.environ[ps[0]]=ps[1]

from MDSplus.mdsplus_wsgi import application

