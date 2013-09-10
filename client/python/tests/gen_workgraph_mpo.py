#!/usr/bin/env python
import pydot
import os
import requests
#this version works with uri method /workflow/id/graph
def gen_workgraph(wid,prefix='workflow'):

    mpo_host='http://localhost:8080'
    mpo_version='v0'
    if os.environ.has_key('MPO_HOST'):
        mpo_host=os.environ['MPO_HOST']
    if os.environ.has_key('MPO_VERSION'):
        mpo_version=os.environ['MPO_VERSION']

    r=requests.get('{host}/{version}/workflow/{wid}/graph'.format(host=mpo_host,version=mpo_version,wid=wid))
    gf=r.json()

    nodeshape={'activity':'rectangle','dataobject':'ellipse','data_object':'ellipse','workflow':'diamond'}

    graph=pydot.Dot(graph_type='digraph')
    nodes = gf['nodes']

#add workflow node explicitly since in is not a child
    graph.add_node( pydot.Node(wid,label=nodes[wid]['name'],shape=nodeshape[nodes[wid]['type']]))
    for item in gf['connectivity']:
        pid=item['parent_uid']
        cid=item['child_uid']
        name=nodes[cid]['name']
        theshape=nodeshape[nodes[cid]['type']]
        graph.add_node( pydot.Node(cid, label=name, shape=theshape) )
        if item['child_type']!='workflow':
            graph.add_edge( pydot.Edge(pid, cid) )
        
    graph.write(prefix+'.gv')
    graph.write_png(prefix+'.png')
    return

####main block
if __name__ == '__main__':
    
    import sys
    args=sys.argv

    if len(args)==1:
        gen_workgraph(None)
    elif len(args)==2:
        gen_workgraph(args[1])
    elif len(args)==3:
        gen_workgraph(args[1],args[2])
