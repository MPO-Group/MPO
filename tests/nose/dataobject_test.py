from __future__ import print_function
from nose.tools import *
import unittest

import mpo_setup
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


    def create_object(self):
        "Add a dataobject to the MPO."
        self.m.add(name="ImportantFile",desc="Adding a dataobject in nose test",
                   uri="ftp://some.server.com/somefile")
        pass


