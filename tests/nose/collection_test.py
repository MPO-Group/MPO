from __future__ import print_function
from nose.tools import *
from nose.plugins.attrib import attr
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
        print('collection created with element', c,str(type(c)))
        ce=self.m.search(route='collection/'+c.get('uid')+'/element')
        print('col elements',ce,'\n')
        assert ce[0].get('uid')==oid


    def test_collection2(self):
        "List collections having a particular item as an element."
        oid=self.m.search(route='dataobject')[0].get('uid')
        c=self.m.search(route='collection?element_uid='+oid)
        print('collections having element uid',oid,':',c)
        assert len(c) > 0


    @nottest
    def test_collection3(self):
        "Verify GET collection returns correct fields."
        assert 1==1

    @attr(only='this')
    def test_collection4(self):
        "Collection of workflows. Also tests adding elements to existing collection."
        c1=self.m.collection(name="Nose_collection-workflows",
                             desc="Creating a collection of workflows in unit tests in "+ __name__)
        print ('c1 is ', c1)
        #add a workflow
        wid=self.m.search(route='workflow')[0].get('uid')
        print(' adding workflow ',wid)
        eid=self.m.collection(collection=c1['uid'],elements=[wid]) #[0].get('uid')
        print ('eid is ', eid)
        ce=self.m.search(route='collection/'+c1.get('uid')+'/element')
        print('col element',ce,'should match',wid,' in ',c1.get('uid'),'\n')
        assert ce[0].get('uid')==wid

        
    def test_collection5(self):
        "Collection of collections"
        c1=self.m.collection(name="Nose_collection-member1",
                             desc="Creating a collection in unit tests in "+ __name__)
        c2=self.m.collection(name="Nose_collection-member2",
                             desc="Creating a collection in unit tests in "+ __name__)
        cgroup=self.m.collection(name="Nose_collection_of_collections",
                                 desc="Creating a collection of collections in unit tests in "+ __name__,
                                 elements=[c1.get('uid'),c2.get('uid')])
        print('collection of collections created', cgroup)
        ce=self.m.search(route='collection/'+cgroup.get('uid')+'/element')
        print('col elements',ce,c1,c2,'\n')
        assert ce[0].get('uid')==c1.get('uid')
        assert ce[1].get('uid')==c2.get('uid')


        
