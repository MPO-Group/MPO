import mpo_ar_dataobject as _ar

class mpo_ar_mdsplus(_ar.mpo_ar_dataobject):
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

    def archive(self, server=None, tree=None, shot=None, path=None, verbose=False):
        if verbose:
            print ("constructing an MDSplus object for server=%s tree=%s shot=%d path=%s"%(server,tree,shot,path,))
        if server==None:
            server=""
        uri = r'mdsplus://%s/%s/%d&path=%s'%(server,tree,shot,path,)
        return(uri)

    def archive_parse(self, *args):
        import copy
        import argparse

        #global filespec options
        self.parser.add_argument('--server','-S',action='store',help='Specify the server.')
        self.parser.add_argument('--tree','-t',action='store',help='Specify the tree name.', required=True)
        self.parser.add_argument('--shot','-s',action='store',help='Specify the shot number.', required=True, type=int)
        self.parser.add_argument('--path','-p',action='store',help='Specify the tree path.', required=True)
        ans = self.parser.parse_args(*args)
        return copy.deepcopy(ans.__dict__)

    def restore(self, uri=None, verbose=False):
        if verbose:
            print("NOOP ! restoring an MDSplus data object uri = %s"%(uri,))
        if uri==None :
            raise Exceptions("MDSplus Restore - must specifiy a URI")
        return uri

    def restore_parse(self, *args):
        self.parser.add_argument('--uri','-u',action='store',help='Specify the uri')

    def ls(self, uri=None, verbose=False):
        if verbose:
            print("listing a filespec data object uri = %s"%(uri,))
        return uri

    def ls_parse(self, *args):
        self.parser.add_argument('--uri','-u',action='store',help='Specify the uri')
