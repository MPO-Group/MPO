from __future__ import print_function
from nose.tools import *
import unittest

import mpo_setup
class TemplateTest(unittest.TestCase):
    """
    Template class to be copied for new tests. New tests should be based on test_example.
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


    def test_example(self):
        print (__name__,": running test_setup.\n")
        assert True
        pass


