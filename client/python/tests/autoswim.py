#!/usr/bin/env python
import os, sys, traceback
import subprocess

#setup django environment
sys.path.append("/var/www/swim/")
sys.path.append("/var/www/swim/mysite")
os.environ["DJANGO_SETTINGS_MODULE"] = "settings"
from django.contrib.auth.models import User
from django.db import models
from monitor import models as mymonitor

#setup client environment
os.environ["MPO_HOST"] = "https://mpo.gat.com:9443"
os.environ["MPO_VERSION"] = "v0"
os.environ["MPO_HOME"] = "/home/abla/projects/mposvn/trunk"
MPO_HOME = "/home/abla/projects/mposvn/trunk"
MPO = MPO_HOME + "/client/python/mpo_testing.py"
os.environ["MPO_AUTH"] = MPO_HOME + "/MPODemoUser.pem"


def test_env():
	print(" == environment == ")
	print("%s" %(os.environ["MPO_HOST"] ))
	print("%s" %(os.environ["MPO_VERSION"] ))
	print("%s" %(os.environ["MPO_HOME"] ))
	print("%s" %(os.environ["MPO_AUTH"] ))
	print("%s" %(MPO))

def main(run='29710', simname="ss_36001_Vmod_22"):
    sum = mymonitor.summary.objects.get(portal_runid=run)
    print("%s:%s" %(sum.user, sum.simname))

def swim_workflow(run='29710'):
    try:
        sum = mymonitor.summary.objects.get(portal_runid=run)
        sim = mymonitor.simulation.objects.filter(portal_runid=run)

	# initial debug
	print("====sum====")
	print(sum)
	print("====sim====")
	print(sim[0])
 
	#create workflow and metadata
        wid = create_workflow(run=sum.portal_runid, simname=sum.simname)        
	create_meta(wid, metaname="user", metadata=sum.user)
	create_meta(wid, metaname="simname", metadata=sum.simname)
	create_meta(wid, metaname="host", metadata=sum.host)
	create_meta(wid, metaname="date", metadata=sum.date)
	create_meta(wid, metaname="state", metadata=sum.state)
	create_meta(wid, metaname="code", metadata=sum.code)
	create_meta(wid, metaname="phystimestamp", metadata=sum.phystimestamp)
	create_meta(wid, metaname="comment", metadata=sum.comment)
	create_meta(wid, metaname="tokamak", metadata=sum.tokamak)
	create_meta(wid, metaname="shotno", metadata=sum.shotno)
	create_meta(wid, metaname="outprefix", metadata=sum.outprefix)
	create_meta(wid, metaname="tag", metadata=sum.tag)
	create_meta(wid, metaname="logfile", metadata=sum.logfile)
	create_meta(wid, metaname="vizurl", metadata=sum.vizurl)
	
	#create configuration file data Object
	path = "http://portal.nersc.gov/project/m876/dbb/"
	uri = "<a href=%s%s_monitor_file.nc> %s%s_monitor_file.nc </a>" %(path, sum.portal_runid, path, sum.portal_runid)
    	oid2 = create_object(wid, wid, name ="IPS Configuration File", desc="IPS configuration description", uri=uri)

	#create input files 
    	oid3 = create_object(wid, wid, name = "IPS Input Files", desc="Input files", uri=path)
	
	#create Read Input File Activity
        aid1 = create_activity(wid, oid2, "Read Input Files", "IPS Staging...", path, input=oid3 )		

	#create IPS Tasks Activity -- Will come back to this!
        """
	desc = "tasks: "
	for item in sim:
		if item.eventtype=='IPS_LAUNCH_TASK':
			desc = desc + " =>" + item.code

	uri = "http://swim.gat.com/detail/?id=%s" %(run)
	aid2 = create_activity(wid, aid1, "Run IPS", desc, uri)
	"""

	uri = "http://swim.gat.com/detail/?id=%s" %(run)
	launch_count = 0
	for item in sim:
		if item.eventtype=='IPS_LAUNCH_TASK':
			launch_count = launch_count + 1

	if launch_count > 0:
		launch = []
		count = 0
		for item in sim:
			if item.eventtype=='IPS_LAUNCH_TASK':
				name = item.code
				desc = item.comment
				if count == 0:
					temp_id = create_activity(wid, aid1, name, desc, uri)
				else:
					temp_id = create_activity(wid, launch[count-1], name, desc, uri)
				launch.append(temp_id)
				count = count + 1
		aid2 = launch[count-1]					

	else:
		desc = "IPS subtasks"
        	aid2 = create_activity(wid, aid1, "Run IPS", desc, uri)
		 
	#create Plasma State file Object
	uri = "http://portal.nersc.gov/project/m876/dbb/%s_monitor.nc" %(run)
        oid4 = create_object(wid, aid2, name = "Plasma State File", desc="IPS Plasma State Monitor File", uri=uri )
	
	vis = "http://swim.gat.com/media/plot/all.php?run_id=%s" %(run) 
        pdf = "http://swim.gat.com/media/plot/pdf/%s.pdf" %(run)
    	create_meta(oid4, "Visualization", vis)
    	create_meta(oid4, "Visualization(Hard Copy)", pdf)

	#create Output Files Object
	uri = "<a href=http://portal.nersc.gov/project/m876/dbb/> http://portal.nersc.gov/project/m876/dbb/ </a>"
        oid5= create_object(wid, aid2, name="Simulation Output Files", desc="Simulation Output Files", uri=uri)

	#create Simulation Ended Activity and metadata
	uri = "http://swim.gat.com/detail/?id=%s" %(run) 
    	aid3 = create_activity(wid, oid4, "Simulation Ended", "Completed", uri)
    	create_meta(aid3, 'Last updated', '2014-02-13 09:50:32')

    except KeyboardInterrupt:
        print("Exit requested.... exiting")
    except:
	traceback.print_exc(file=sys.stdout)
    exit(0)

def create_workflow(run='29710', simname="ss_36001_Vmod_22"):
	command = subprocess.Popen([MPO, "init", "--name=SWIM", "--desc=%s : %s"%(run, simname) ], stdout=subprocess.PIPE)
	output, err = command.communicate()
	wid = output.rstrip()
	return wid

def create_meta(wid, metaname="RunID", metadata="29710"):
	command = subprocess.Popen([MPO, "meta", wid, metaname, metadata], stdout=subprocess.PIPE )
	output, err = command.communicate()

def create_object(wid, parent, name="IPS Input Files", desc="IPS configuration file", uri="http://portal.nersc.gov/project/m876/dbb/"):
	command = subprocess.Popen([MPO, "add", wid, parent, "--name=%s"%(name), "--desc=%s"%(desc), "--uri=%s"%(uri)], stdout=subprocess.PIPE )
	output, err = command.communicate()
	oid = output.rstrip()
	return oid

def create_activity( wid, parent, name, desc, uri, input=False ):
        if input:
	    command = subprocess.Popen([MPO, "step", wid, parent, "--input=%s"%(input), "--name=%s"%(name), "--desc=%s"%(desc),"--uri=%s"%(uri)],  stdout=subprocess.PIPE )
	else:
	    command = subprocess.Popen([MPO, "step", wid, parent, "--name=%s"%(name), "--desc=%s"%(desc),"--uri=%s"%(uri)],  stdout=subprocess.PIPE )
        output, err = command.communicate()
        aid = output.rstrip()
        return aid

def test():
    test_env()
    main(runid)
    wid = create_workflow()
    create_meta(wid)
    create_meta(wid, "User", "Batchelor")
    oid2 = create_object(wid, wid, name ="IPS Configuration File", desc="IPS configuration description", uri="http://portal.nersc.gov")
    print oid2
    oid3 = create_object(wid, wid, name = "IPS Input Files", desc="Input files", uri="file:/project/m876/dbb/")
    print oid3
    create_meta(oid3, "Input File", "hy040510_1.5sec_3steps_ps.cdf")
    create_meta(oid3, "Input File", "hy040510_1.5sec_3steps_ps.jso")
    aid1 = create_activity(wid, oid2, "Read Input Files", "IPS Staging...", "http://swim.gat.com/", input=oid3 )
    print "aid1=%s" %(aid1)
    aid2 = create_activity(wid, aid1, "Run IPS", "tasks: epa__tsc -> nb__nubeam -> nb__nubeam -> epa_tsc -> nb__nubeam -> epa__tsc -> nb__nubeam -> epa__tsc", "http://swim.gat.com/detail/?id=29710")
    print "aid2=%s" %(aid2)
    oid4 = create_object(wid, aid2, name = "Plasma State File", desc="IPS Plasma State Monitor File", uri="http://portal.nersc.gov/project/m876/dbb/")
    print "oid4=%s" %(oid4) 
    create_meta(oid4, "Visualization", "http://swim.gat.com/media/plot/pdf")
    create_meta(oid4, "Visualization(Hard Copy)", "http://swim.gat.com/media/plot/pdf")
    oid5= create_object(wid, aid2, name="Simulation Output Files", desc="Simulation Output Files", uri="<a href='http://portal.nersc.gov/project/m876/dbb/'> http://portal.nersc.gov/project/m876/dbb/ </a>")
    print "oid5=%s" %(oid5)   
    aid3 = create_activity(wid, oid4, "Simulation Ended", "Completed", "http://swim.gat.com/detail/?id=29710")
    print "aid3=%s" %(aid3)
    create_meta(aid3, 'Last updated', '2014-02-13 09:50:32')
 
	
if __name__ == "__main__":
    if len(sys.argv) < 2:
        run = '29710'    
    else:
	run = sys.argv[1]

    #test()
    swim_workflow(run=run)

