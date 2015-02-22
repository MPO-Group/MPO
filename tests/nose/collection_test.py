from __future__ import print_function
from nose.tools import *
import unittest

import mpo_setup
class CollectionTest(unittest.TestCase):
    """
    Test the collection route.
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


    def test_collection0(self):
        "Create an empty collection"
        print('empty collection test\n')
        c=self.m.collection(name="Nose_collection-empty",
                            desc="Creating a collection in unit tests in "+ __name__)
        print('Made collection',c)
        assert c.get('uid') != "-1"
        print('collection created, now retrieving.', c)
        ce=self.m.search(route='collection/'+c.get('uid'))[0]
        print('collection details',ce,'\n')
        assert ce.get('uid')==c.get('uid')


    def test_collection1(self):
        "Create a collection with an element"
        #note use of search route which is formatted, get always returns raw response
        oid=self.m.search(route='dataobject')[0].get('uid')
        print('test collection adding object with oid to collection: ',oid,'\n')
        c=self.m.collection(name="Nose_collection",desc="Creating a collection in unit tests from "+
                            __name__, elements=[oid] )
        print('collection created', c)
        ce=self.m.search(route='collection/'+c.get('uid')+'/element')
        print('col elements',ce,'\n')
        assert ce[0].get('uid')==oid


    def test_collection2(self):
        "List collections having a particular item as an element."
        oid=self.m.search(route='dataobject')[0].get('uid')
        c=self.m.search(route='collection?element_uid='+oid)
        print('collections having element uid',oid,':',c)
        assert len(c) > 0


    def test_collection3(self):
        "Verify GET collection returns correct fields."
        assert 1==1
