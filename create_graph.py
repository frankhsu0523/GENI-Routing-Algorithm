"""

Usage:
    create_graph.py <rspec.xml> <topo.txt>

Options:
    -h --help Show this screen

"""

from docopt import docopt
import xml.etree.ElementTree as ET
import networkx as nx
import pickle
import sys, os

from utility.NODE import NODE

def get_network_graph( file ,flow_limit):
    G = nx.Graph()
    tree = ET.parse(file)
    root = tree.getroot()

    for child in root:
        if 'node' in child.tag and child.attrib['client_id'] != 'GDGN0' and child.attrib['client_id'] != 'AAGCTRL0':
            node_client_id = child.attrib['client_id']
            node = NODE( name = node_client_id )
            for node_data in child:
                if 'interface' in node_data.tag:
                    info = node_data
                    node.set_intf( info = info )
                if 'services' in node_data.tag:
                    info = node_data[0].attrib
                    node.set_login( info = info )
            if node.type == 'switch':
                node.flow_limit = flow_limit[node_client_id]
                node.set_intf_ofport()
                node.set_node_datapath_id()
            G.add_node(node_client_id, object=node)

        if 'link' in child.tag:
            link_intf = [ l.attrib['client_id'] for l in child if 'interface_ref' in l.tag]
            for n, info in G.nodes_iter(data=True):
                node = info['object']
                if link_intf[0] in node.intf:
                    head = n
                if link_intf[1] in node.intf:
                    tail = n

            head_node = G.node[head]['object']
            head_node.set_node_to_intf( node=tail, intf=link_intf[0])

            tail_node = G.node[tail]['object']
            tail_node.set_node_to_intf( node=head, intf=link_intf[1])

            G.add_edge(head, tail)
    return G

def get_flow_limit( file ):
    with open( file, 'r') as f:
        output = f.readlines()
    flow_limit = dict()
    for row in output[2:]:
        #print(row)
        elements = row.rstrip().split(' ')
        if len(elements) == 2:
            node, table_size = elements[:]
            flow_limit['s'+ node] = table_size
    return flow_limit

def write_pickle( G, dir_path ):
    file = open(dir_path + '/graph.pickle','wb')
    pickle.dump(G, file, protocol=2)
    file.close

def main():
    args = docopt(__doc__)
    flow_limit = get_flow_limit( args['<topo.txt>'] )
    print('flow_limit: ',flow_limit)
    dir_path = os.path.dirname(os.path.realpath(args['<topo.txt>']))
    G = get_network_graph( args['<rspec.xml>'] ,flow_limit )
    write_pickle( G, dir_path )
    for n, info in G.nodes(data=True):
        node = info['object']
        print(node)
    
if __name__ == '__main__':
    main()
