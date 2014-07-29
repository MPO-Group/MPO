import mpo_do_dataobject as _do
class mpo_do_mdsplus(_do.mpo_do_dataobject):
    """
    A class to construct data objects for references to mdsplus trees..  

    This simply creates or returns an existing data object that referes to a 
    particular server, tree, shot, path.

    command line syntax:
        mpo create {--protocol=|-p }mdsplus {--server=|-s }server-name 
                   {--tree=|-t }tree-name {--shot=|-n }shot-number {--path=|-p }tree-path
    for example:
        mpo create --protocol=mdsplus --server=alcdaq --tree=cmod --shot=1090909009 --path=\\ip
    """

    def create(self,  name=None, description=None, server=None, tree=None, shot_number=None, path=None, verbose=False):
        if verbose:
            print ("constructing a mdsplus object for server=%s tree=%s shot=%d path=%s"%(server, tree, shot_number, path,))
        uri = "mdsplus://%s/?tree=%s&shot=%d&path=%s"%(server, tree, shot_number, path,)
        return(self.mpo.add_do(name=name, desc=description, uri=uri))

    def cli(self, *args):
        import copy
        import argparse

        #global mdsplus options
        self.parser.add_argument('--server','-S',action='store',help='''Specify server.''')
        self.parser.add_argument('--tree','-t',action='store',help='''Specify tree.''')
        self.parser.add_argument('--shot-number','--shot', '-s', action='store',help='Shot number of the tree', type=int)
        self.parser.add_argument('--path', '-p', action='store', help='Path in the tree for this data object')

        ans = self.parser.parse_args(*args)
        return copy.deepcopy(ans.__dict__)
