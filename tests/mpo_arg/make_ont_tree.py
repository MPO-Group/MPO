#!/usr/bin/env python
import os,sys
import treelib as t

cert=os.environ.get('MPO_AUTH')
api=os.environ.get('MPO_HOST')
home=os.environ.get('MPO_HOME')
if not (api or cert or home):
    print("certificate or mpo host or home not set, exiting.")
    sys.exit(1)

sys.path.insert(0,home+'/client/python')
import mpo_arg

m=mpo_arg.mpo_methods(api_url=api,cert=cert,debug=True)

records=m.get('ontology/term').json()
ot_tree=t.Tree()

ot_tree.create_node('root','0')

while len(records)>0:
    for o in records:
        pid=o['parent_uid']
        if pid==None:
            pid='0'
        try:
            ot_tree.create_node(o['name'],o['uid'],parent=pid)
            #print('adding node with parent ',o['name'],o['uid'],pid)
            records.remove(o)
        except t.tree.NodeIDAbsentError, e: #treelib.tree.NodeIDAbsentError
            pass
            #print("didn't find parent, going to next record.",e,type(e),o['name'])


ot_tree.show()

