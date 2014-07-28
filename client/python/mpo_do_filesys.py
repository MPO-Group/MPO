import mpo_do_dataobject as _do

class mpo_do_filesys(_do.mpo_do_dataobject):
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

    def create(self, filespec=None, description=None, name=None, verbose=False):
        if verbose:
            print ("constructing a filespec object for %s"%(filespec,))
        uri = "filesys://%s"%filespec
        return(self.mpo.add(None, None,name=name, desc=description, uri=uri))

    def cli(self, *args):
        import copy
        import argparse

        #global filespec options
        self.parser.add_argument('--filespec','-f',action='store',help='''Specify file or directory.''', required=True)
        ans = self.parser.parse_args(*args)
        return copy.deepcopy(ans.__dict__)
