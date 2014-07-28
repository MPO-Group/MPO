class mpo_dataobject(object):
    """
    A class to construct data objects from files in the users file system.
    No file manipulation is done.  

    This simply creates or returns an existing data object that referes to a 
    particular file.

    command line syntax:
        mpo create [--protocol=| -p ] filesys [--filespec=|-f ] [file-name | directory-name]

    for example:
        mpo create --protocol=filesys --filespec=/usr/local/cmod/shared/some-file.dat
    """
    def __init__(self, mpo):
       self.mpo = mpo

    def create(self, filespec=None, verbose=False):
        print ("constructing a filespec object for %s"%filespec)
        return ("filesys://%s"%filespec)

    def cli(self, *args):
        import copy
        import argparse
        parser = argparse.ArgumentParser(description='filespec data object creator',
                                         epilog="""Metadata Provenance Ontology project""",
                                         prog='mpo create --protocol=filespec')
        parser.add_argument('--verbose','-v',action='store_true',help='Turn on debugging info',
                            default=False)

    #note that arguments will be available in functions as arg.var

        #global mdsplus options
        parser.add_argument('--filespec','-f',action='store',help='''Specify file or directory.''')
        ans = parser.parse_args(*args)
        return copy.deepcopy(ans.__dict__)
