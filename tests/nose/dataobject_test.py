from __future__ import print_function
from nose.tools import *
import unittest

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


    def create_object_test(self):
        "Add a dataobject to a workflow in the MPO."
        workflow = self.m.search(route='workflow')[0]
        wid = workflow.get('uid')
        print( "Adding databobject to workflow ",wid)
        dataobject=self.m.add(name="ImportantFile",desc="Adding a dataobject in nose test",
                   uri="ftp://some.server.com/somefile", workflow_ID=wid, parentobj_ID=wid)
        doi=dataobject.get('uid')
        assert doi
        print( "created a dataobject in create_object with uid: "+ doi )



    #other tests:
    #search for dataobject by ID also returns all instances.
