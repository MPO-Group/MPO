import mpo_ar_dataobject as _ar

class mpo_ar_filesys(_ar.mpo_ar_dataobject):
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

    def archive(self, filespec=None, verbose=False):
        if verbose:
            print ("constructing a filespec object for %s"%(filespec,))
        uri = "filesys://%s"%filespec
        return(uri)

    def archive_parse(self, *args):
        import copy
        import argparse

        #global filespec options
        self.parser.add_argument('--filespec','-f',action='store',help='''Specify file or directory.''', required=True)
        ans = self.parser.parse_args(*args)
        return copy.deepcopy(ans.__dict__)

    def restore(self, filespec=None, uri=None, verbose=False):
        if verbose:
            print("NOOP ! restoring a filespec data object filespec=%s uri = %s"%(filespec, uri,))
        if filespec==None :
            if uri==None:
                raise Execption("FILESPEC Restore - must specifiy either filespec or uri")
            parts = uri.split(":///")
            filespec=parts[1]
        return filespec

    def restore_parse(self, *args):
        grp = self.parser.add_exclusive_group(required=True)
        grp.add_argument('--filespec','-f',action='store',help='Specify the file or directory')
        grp.add_argument('--uri','-u',action='store',help='Specify the uri')

    def ls(self, filespec=None, uri=None, verbose=False):
        if verbose:
            print("listing a filespec data object filespec=%s uri = %s"%(filespec, uri,))
        if filespec==None :
            if uri==None:
                raise Execption("FILESPEC ls - must specifiy either filespec or uri")
            parts = uri.split(":///")
            filespec=parts[1]
        return filespec

    def ls_parse(self, *args):
        grp = self.parser.add_exclusive_group(required=True)
        grp.add_argument('--filespec','-f',action='store',help='Specify the file or directory')
        grp.add_argument('--uri','-u',action='store',help='Specify the uri')
