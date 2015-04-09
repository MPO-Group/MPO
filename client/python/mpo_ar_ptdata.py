import mpo_ar_dataobject as _ar

class mpo_ar_ptdata(_ar.mpo_ar_dataobject):
    """
    A class to construct data objects that describe records in GA's PTDATA

    This simply creates or returns an existing data object that referes to a 
    particular file.

    command line syntax:
        mpo create [--protocol=| -p ] ptdata [--server=|-S ] server-name [--shot=|-s ] shot-number [--point=|-P ] point-name

    for example:
        mpo create --protocol=ptdata --server=ptdata.gat.com --shot=12345 --point=bcoil
    """

    def archive(self, server=None, shot=None, point=None, verbose=False):
        if verbose:
            print ("constructing an ptdata object for server=%s shot=%d point=%s"%(server,shot,point,))
        if server==None:
            server=""
        uri = r'ptdata://%s/%d/%s'%(server,shot,point,)
        return(uri)

    def archive_parse(self, *args):
        import copy
        import argparse

        #global filespec options
        self.parser.add_argument('--server','-S',action='store',help='Specify the server.')
        self.parser.add_argument('--shot','-s',action='store',help='Specify the shot number.', required=True, type=int)
        self.parser.add_argument('--point','-P',action='store',help='Specify the point name.', required=True)
        try:
            ans = self.parser.parse_args(*args)
        except SystemExit:
            return None
        return copy.deepcopy(ans.__dict__)


    def restore(self, uri=None, verbose=False):
        if verbose:
            print("NOOP ! restoring an ptdata data object uri = %s"%(uri,))
        if uri==None :
            raise Exceptions("PTDATA Restore - must specifiy a URI")
        return uri

    def ls(self, uri=None, verbose=False):
        if verbose:
            print("listing a filespec data object uri = %s"%(uri,))
        return uri

