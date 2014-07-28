class mpo_do_mdsplus(object):
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
    def __init__(self, mpo):
        self.mpo = mpo
        print('mdsplus init returning')

    def create(self,  server=None, tree=None, shot_number=None, path=None, verbose=False):
        print ("constructing a mdsplus object for server=%s tree=%s shot=%d path=%s"%(server, tree, shot_number, path,))
        return ("mdsplus://%s/?tree=%s&shot=%d&path=%s"%(server, tree, shot_number, path,))

    def cli(self, *args):
        import copy
        import argparse
        parser = argparse.ArgumentParser(description='mdsplus data object creator',
                                         epilog="""Metadata Provenance Ontology project""",
                                         prog='mpo create --protocol=mdsplus')

    #note that arguments will be available in functions as arg.var

        #global mdsplus options
        parser.add_argument('--server','-s',action='store',help='''Specify server.''')
        parser.add_argument('--tree','-t',action='store',help='''Specify tree.''')
        parser.add_argument('--shot-number','--shot', '-n', action='store',help='Shot number of the tree', type=int)
        parser.add_argument('--verbose','-v',action='store_true',help='Turn on debugging info',
                            default=False)
        parser.add_argument('--path', '-p', action='store', help='Path in the tree for this data object')

        ans = parser.parse_args(*args)
        return copy.deepcopy(ans.__dict__)
