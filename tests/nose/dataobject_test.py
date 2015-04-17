from __future__ import print_function
from nose.tools import *
from nose.plugins.attrib import attr
import unittest
import json

import mpo_setup #custom method to set up api instance for these tests.
class DataobjectTest(unittest.TestCase):
    """
    Dataobject api route testing class.
    """
    @classmethod
    def setup_class(self):
        self.m = mpo_setup.setup()
        print( __name__,": setting up module with user certificate, ",self.m.cert,".\n")
        pass


    @classmethod
    def teardown_class(self):
        mpo_setup.teardown(self.m)
        print (__name__,": tearing down.\n")

    def create_object_workflow_new_test(self):
        "Add a new dataobject to a workflow in the MPO."
        workflow = self.m.search(route='workflow')[0]
        wid = workflow.get('uid')
        print( "Adding databobject to workflow ",wid)
        dataobject=self.m.add(name="ImportantFile",desc="Adding a dataobject in nose test",
                   uri="ftp://some.server.com/somefile", workflow_ID=wid, parentobj_ID=wid)
        output=json.dumps(dataobject,separators=(',', ':'),indent=4)
        print('dataobject in create_object_workflow_new_test',output)
        doi=dataobject.get('uid')
        dataobject2 = self.m.search('workflow/{workid}/dataobject/{uid}'.format( workid=wid, uid=doi ) )
        output=json.dumps(dataobject2,separators=(',', ':'),indent=4)
        print( "created a dataobject in create_object with uid: "+ str(doi),output )
        assert doi

        
    def create_object_workflow_test(self):
        "Add an existing dataobject by uid to a workflow in the MPO."
        workflow = self.m.search(route='workflow')[0]
        wid = workflow.get('uid')
        print( "Adding databobject to workflow ",wid)
        dataobject = self.m.search(route='dataobject')[0]
        doi = dataobject.get('uid')
        dataobject_post=self.m.add(name="ImportantFile2",desc="Adding a dataobject by uid to workflow in nose test",
                   uid=doi, workflow_ID=wid, parentobj_ID=wid)
        #for now, return record is incomplete. you have to fetch record to get all info, take care to get instance
        dataobject2 = self.m.search('workflow/{workid}/dataobject/{uid}'.format( workid=wid, uid=dataobject_post.get('uid') )  )
        output=json.dumps(dataobject,separators=(',', ':'),indent=4)
        print ('dataobject',output)
        output=json.dumps(dataobject_post,separators=(',', ':'),indent=4)
        print ('dataobject_post', output)
        output=json.dumps(dataobject2,separators=(',', ':'),indent=4)
        print ('dataobject2', output)
        do_uid=dataobject2['result'][0].get('do_uid')
        print("doi,do_uid",doi,do_uid)
        assert do_uid==doi
        print( "created a dataobject in create_object with uid: "+ str(do_uid) +","+str(doi) )

        

    def create_object_bare_test(self):
        "creating dataobject by itself."
        dataobject=self.m.add(name="ImportantFile",desc="Adding a bare dataobject from uri in nose test",
                   uri="ftp://some.server.com/somefile4")
        print ('create object bare test',dataobject)
        doi=dataobject[0].get('uid')
        print( "created a bare dataobject in create_object with uid: "+ str(doi) )
        assert doi

    @attr(only='this')
    def create_object_bare_two_test(self):
        "creating duplicate dataobject by itself."
        #do=self.m.search(route='dataobject', params={'uri':"ftp://some.server.com/somefile"} )[0]
        do=self.m.search(route='dataobject' )[0] #get first one and use its uri
        print('making duplicate of do:',do)
        dataobject=self.m.add(name="ImportantFile",desc="Adding a bare dataobject from uri in nose test",
                              uri=do.get('uri'))
#                   uri="ftp://some.server.com/somefile")[0]
        print ('create object bare two test dataobject:',dataobject)
        doi=dataobject[0].get('uid')
        print( "created a duplicate bare dataobject in nose test with uid: "+ str(doi) )
        assert doi==do.get('uid')

    #other tests:
    #search for dataobject by ID also returns all instances.
    #add a dataobject vs an instance (ie member of a workflow)
