class dataobject(object):
    """
    A class to construct data objects from files in the users file system.
    No file manipulation is done.  

    This simply creates or returns an existing data object that referes to a 
    particular file.
    """
    def __init__(self, mpo, filespec=None, f=None):
       self.mpo = mpo
       self.filespec=filespec or f

    def create(self):
        print ("constructing a filespec object for %s"%self.filespec)
        return ("filesys://%s"%self.filespec)
