import mpo_ar_dataobject as _ar

class mpo_ar_rsync(_ar.mpo_ar_dataobject):
    """
    A class to archive files and directories using rsync and return a url that 
    can be used  retrieve it.

    command line syntax:
        mpo archive [--protocol=| -p ] rsync \
                    [--host= |-H ] hostname \ 
                    [--filespec=|-f ] [file-name | directory-name] \
                    [--destination=|-d ] destination-filespec

    for example:
        mpo archive --protocol=rsync \
                    --host=jas@pfsctor1.psfc.mit.edu \ 
                    --filespec=/usr/local/cmod/shared/some-file.dat \
                    --destination=/archives/cmod/1090909009/diagnostic/some-file.dat
    """


    def archive(self, filespec=None, host=None, destination=None, verbose=False):
        import os
        from subprocess import check_call, CalledProcessError
        if verbose:
            print ("constructing an rsync object for %s to %s:%s"%(filespec,host,destination,))
        try:
            if os.path.isdir(filespec):
                if CheckDirRead(filespec):
                    if destination:
                        uri = "rsync://%s/%s/%s" % (host, destination,filespec, )
                        status = call(['rsync', '-a', filespec, "%s:%s"%(host,destination,)])
                    else:
                        uri =  "rsync://%s/%s" % (host, filespec, )
                        status = check_call(['rsync', '-a', filespec, "%s:"%(host,)])
                else:
                    raise Exception("Directory %s is not readable"%filespec)
            elif os.path.isfile(filespec):
                if os.access(filespec, os.R_OK):
                    if destination:
                        uri = "rsync://%s/%s/%s" % (host, destination,filespec, )
                        status = call(['rsync', filespec, "%s:%s"%(host,destination,)])
                    else:
                        uri =  "rsync://%s/%s" % (host, filespec, )
                        status = check_call(['rsync', '-a', filespec, "%s:"%(host,)])
                else:
                    raise Exception("File %s is not readable"%filespec)
            else:
                raise Exception("File/Directory %s does not exist"%filespec)
            return uri
        except CalledProcessError,e:
            return {"error": {"returncode": e.returncode, "cmd":e.cmd, "output":e.output}}
        except Exception,e:
            return e

    def archive_parse(self, *args):
        import copy
        import argparse

        #global filespec options
        self.parser.add_argument('--filespec','-f',action='store',help='''Specify file or directory.''', required=True)
        self.parser.add_argument('--host','-H',action='store',help='''Specify the rsync host''', required=True)
        self.parser.add_argument('--destination','-d',action='store',help='''Specify rsync destination''')
        try:
            ans = self.parser.parse_args(*args)
        except SystemExit:
            return None
        return copy.deepcopy(ans.__dict__)


    def restore(self, uri=None, verbose=False):
        from subprocess import call
        if verbose:
            print("Restoring a rsync data object uri = %s"%(uri,))
        if uri==None:
            raise Execption("RSYNC Restore - must specifiy a uri")
        parts = uri.split("://")
        rsync_spec=parts[1].replace('/',':',1)
        if verbose:
            print "RSYNC about to excute 'rsync -av %s ./'"%(rsync_spec,)
        status = call(["rsync", "-av", rsync_spec, "./"])
        return 1

    def ls(self, uri=None, verbose=False):
        from subprocess import check_output
        if verbose:
            print("listing a rsync data object uri = %s"%(uri,))
        if uri==None:
            raise Execption("FILESPEC ls - must specifiy either filespec or uri")
        parts = uri.split("://")
        rsync_spec=parts[1].replace('/',':',1)
        parts = rsync_spec.split(":")
        print ["ssh", parts[0], "ls", "-rl", parts[1]]
        try:
            status = check_output(["ssh", parts[0], "ls", "-rl", parts[1]])
            print status
        except Exception, e:
            print "RSYNC ls %s\n\t%s"%(uri, e,)
            status = repr(e)
        return status

