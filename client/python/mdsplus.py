class dataobject(object):
    """
    A class to construct data objects for references to mdsplus trees..  

    This simply creates or returns an existing data object that referes to a 
    particular server, tree, shot, path.
    """
    def __init__(self, mpo, server=None, tree=None, shot=None, path=None, s=None, t=None, s=None, p=None):
        self.mpo = mpo
#	for k in kw:
#            print(k)
#	    self.setattr(k, kw[k])
        try:
            self.server=server or s
            self.tree=tree or t
            shotstr = shot or s
            self.shot=int(shotstr)
            self.path=path or p
        except Exception, e:
            pass
        print "mdsplus data object creator returning"

    def create(self):
        print ("constructing a mdsplus object for server=%s tree=%s shot=%d path=%s"%(self.server, self.tree, self.shot, self.path,))
        return ("mdsplus://%s/?tree=%s&shot=%d&path=%s"%(self.server, self.tree, self.shot, self.path))
