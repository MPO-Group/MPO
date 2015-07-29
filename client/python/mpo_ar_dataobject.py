class mpo_ar_dataobject(object):
    """
    Super class for mpo_ar_xxxx data object creation classes.

    initializes the members:
        mpo - the mpo object to use for requests
        parser - the parser to use for parsing the arguments

    """
    def __init__(self, mpo):
        import argparse
        self.mpo = mpo
        self.parser = argparse.ArgumentParser(description='data object creator',
                                         epilog="""Metadata Provenance Ontology project""",
                                         prog='mpo archive --protocol=xxx')
        self.parser.add_argument('--verbose','-v',action='store_true',help='Turn on debugging info',
                            default=False)
