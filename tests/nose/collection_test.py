from __future__ import print_function
from nose.tools import *
import unittest

import mpo_setup
class CollectionTests(unittest.TestCase):
    """
    Test the collection route.
    """
    @classmethod
    def setup_class(self):
        print('\n')
        self.m = mpo_setup.setup()
        print( __name__,": setting up module with user certificate, ",self.m.cert,".\n")
        pass


    @classmethod
    def teardown_class(self):
        mpo_setup.teardown(self.m)
        print('\n')
        print (__name__,": tearing down.\n")


    def test_setup(self):
        print('\n')
        print (__name__,": running test_setup.\n")
        pass


    def test_collection1(self):
        "Create a collection"
        print('\n')
        #note use of search route which is formatted, get always returns raw response
        oid=self.m.search(route='dataobject')[0].get('uid')
        print('test collection adding object with oid to collection: ',oid,'\n')
        c=self.m.collection(name="Nose_collection",desc="Creating a collection in unit tests from "+
                            __name__, elements=[oid] )
        print('collection created', c)
        ce=self.m.search(route='collection/'+c.get('uid')+'/element')
        print('col elements',ce,'\n')
        assert ce[0].get('uid')==oid
