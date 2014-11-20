class mpo_do_dataobject(object):
    """
    Super class for mpo_do_xxxx data object creation classes.

    initializes the members:
        mpo - the mpo object to use for requests
        parser - the parser to use for parsing the arguments

    """
    def __init__(self, mpo):
        import argparse
        self.mpo = mpo
        self.parser = argparse.ArgumentParser(description='data object creator',
                                         epilog="""Metadata Provenance Ontology project""",
                                         prog='mpo create --protocol=xxx')
        self.parser.add_argument('--verbose','-v',action='store_true',help='Turn on debugging info',
                            default=False)
        self.parser.add_argument('--description', '--desc', '-d', action='store', help='''An optional description for this data object''')
        self.parser.add_argument('--name', '-n', action='store', help='''An optional name for this data object''', required=True)
