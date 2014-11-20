import mpo_do_dataobject as _do
class mpo_do_rsync(_do.mpo_do_dataobject):
    """
    A class to archive files and directories using rsync, returning an MPO
    data object that describes them.  

    This class archives and lists the contents of 'rsync' MPO data objects.

    Rsync the file or directory to the archive and construct a url that describes
    how to retrieve it.

    command line syntax:
        mpo create {--protocol=|-p }rsync {--server=|-s }server-name 
                   {--tree=|-t }tree-name {--shot=|-n }shot-number {--path=|-p }tree-path
    for example:
        mpo create --protocol=rsync --server=alcdaq
    """

    def create(self,  name=None, description=None, workflow_id=None, composite_id=None, 
               parent_uid=None, verbose=False, server=None, user=None, password=None, 
               certificate=None, filespec=None, prefix=None, auto_prefix=None):
        if verbose:
            print ("constructing an rsync object for  name=%s, description=%s, workflow_id=%s, "
                   "composite_id=%s, parent_uid=%s, verbose=%s, server=%s, user=%s, password=%s, "
                   "certificate=%s, filespec=%s, prefix=%s, auto_prefix=%s "%
                   ( name, description, workflow_id, composite_id, parent_uid, verbose, 
                     server, user, password, certificate, filespec, prefix, auto_prefix,))
#        uri = "mdsplus://%s/?tree=%s&shot=%d&path=%s"%(server, tree, shot_number, path,)
#        return(self.mpo.add_do(composite_id=composite_id, parent_uid=parent_uid, name=name, 
#            desc=description, uri=uri))
        return None

    def cli(self, *args):
        import copy
        import argparse

        #global mdsplus options
        self.parser.add_argument('--server','-s',action='store',help='Specify server.')
        self.parser.add_argument('--user','-u',action='store',
                                 help='Username to use with rsync server')
        self.parser.add_argument('--password', '-p', action='store', 
                                 help='password for user to use with rsync server')
        self.parser.add_argument('--certificate','--cert', '-C', action='store', 
                                 help='certificate file to use with rsync server')
        self.parser.add_argument('--filespec', '-f', action='store', 
                                 help='file or directory name to archive')
        self.parser.add_argument('--prefix', '-pre',action='store',
                                 help='a prefix to be tacked on to the front of the filename'
                                 ' in the archive')
        self.parser.add_argument('--auto_prefix','--auto','-a', 
                                 action='store_true',
                                 help='Use the composite ID of the workflow as a prefix for '
                                 'the file in the archive',
                                 default=True)

        ans = self.parser.parse_args(*args)
        return copy.deepcopy(ans.__dict__)
