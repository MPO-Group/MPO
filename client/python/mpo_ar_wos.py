import mpo_ar_dataobject as _ar

class mpo_ar_wos(_ar.mpo_ar_dataobject):
    """
    A class to construct data objects from objects stored in the WOS object store.
    No file manipulation is done.  

    This simply creates or returns an existing data object that referes to a 
    particular object given the hostname and the objectid

    command line syntax:
        mpo create [--protocol=| -p ] wos [--server=|-s ] server-name [--oid=|-o ] object-id

    for example:
        mpo create --protocol=wos --server=SERVERNAME --oid=A_Ff3iTD5W-hVA_ICg1Ezj09DzUvZikc1NLN3HC
    """

    def archive(self, server=None, oid=None, verbose=False):
        if verbose:
            print ("constructing an wos object for server=%s oid=%s"%(server,oid,))
        uri = r'wos://%s/objects/%s'%(server,oid,)
        return(uri)

    def archive_parse(self, *args):
        import copy
        import argparse

        #global filespec options
        self.parser.add_argument('--server','-S',action='store',help='Specify the server.', required=True)
        self.parser.add_argument('--oid','-o',action='store',help='Specify the object id.', required=True)
        try:
            ans = self.parser.parse_args(*args)
        except SystemExit:
            return None
        return copy.deepcopy(ans.__dict__)


    def restore(self, uri=None, verbose=False):
        if verbose:
            print("NOOP ! restoring an wos data object uri = %s"%(uri,))
        if uri==None :
            raise Exceptions("MDSplus Restore - must specifiy a URI")
        return uri

    def ls(self, uri=None, verbose=False):
        if verbose:
            print("listing a wos data object uri = %s"%(uri,))
        return uri
