
import sys
import networkx as nx
import xml.etree.ElementTree as ET

class RSPEC:

    def __init__(self):
        self.G = nx.Graph()
        self.file = None

    def get_graph(self, file):
        with open( file, 'r') as f:
            output = f.readlines()
        self.file = file

        for row in output[2:]:
            elements = row.rstrip().split(' ')
            if len(elements) == 2:
                node, table_size = elements[:]
                self.G.add_node('s' + node, table_size=table_size)
                self.G.add_node('h' + node)

            if len(elements) == 3:
                head, tail, capacity = elements[:]
                if not self.G.has_edge('s'+tail, 's'+head):
                    self.G.add_edge('s'+head, 's'+tail, capacity=int(float(capacity)))
                if not self.G.has_edge('s'+head, 'h'+head):
                    self.G.add_edge('s'+head, 'h'+head, capacity=int(float(capacity)))
                if not self.G.has_edge('s'+tail, 'h'+tail):
                    self.G.add_edge('s'+tail, 'h'+tail, capacity=int(float(capacity)))

        intf = 0
        for node in self.G.nodes():
            for i, neighbor in enumerate(self.G.neighbors(node)):
                self.G.node[node][intf] = neighbor
                self.G[node][neighbor][node] = intf
                intf += 1

        for n in self.G.nodes(data=True):
            print(n)

        for n in self.G.edges(data=True):
            print(n)

    def write_rspec(self):
        rspec = ET.Element('rspec')
        for node, attr in self.G.nodes(data=True):
            e_node = ET.SubElement(rspec, 'node', client_id=node)

            e_sliver_type = ET.SubElement(e_node, 'sliver_type', name="emulab-xen")

            if node[0] == 'h':
                ET.SubElement(e_node, 'icon', xmlns="http://www.protogeni.net/resources/rspec/ext/jacks/1", url="https://portal.geni.net/images/Xen-VM.svg")
            if node[0] == 's':
                ET.SubElement(e_node, 'icon', xmlns="http://www.protogeni.net/resources/rspec/ext/jacks/1", url="https://portal.geni.net/images/router.svg")

            ET.SubElement(e_node, 'site', id="Site 1")
            if node[0] == 'h':
                ET.SubElement(e_sliver_type, 'disk_image', name="urn:publicid:IDN+emulab.net+image+emulab-ops:GDXEN160218")
            if node[0] == 's':
                ET.SubElement(e_sliver_type, 'disk_image', name="urn:publicid:IDN+emulab.net+image+emulab-ops:UBUNTU14-OVS2.31")

            for key, data in attr.items():
                if key != 'table_size':
                    ET.SubElement(e_node, 'interface', client_id= 'interface-'+ str(key))
        for i, data in enumerate(self.G.edges(data=True)):
            source, target, attr = data
            #print(data)
            e_link = ET.SubElement(rspec, 'link', client_id= "link-"+str(i))
            ET.SubElement(e_link, 'interface_ref', client_id= 'interface-'+ str(attr[source]))
            ET.SubElement(e_link, 'interface_ref', client_id= 'interface-'+ str(attr[target]))

            ET.SubElement(e_link, 'property', xmlns="http://www.geni.net/resources/rspec/3",capacity=str(self.G.edge[source][target]['capacity'])\
                            ,dest_id="interface-" + str(attr[target]), source_id= 'interface-'+ str(attr[source]))
            ET.SubElement(e_link, 'property', xmlns="http://www.geni.net/resources/rspec/3",capacity=str(self.G.edge[target][source]['capacity'])\
                            , dest_id="interface-" + str(attr[source]), source_id= 'interface-'+ str(attr[target]))


            #ET.SubElement(e_link, 'link_type', name= 'lan')
            ET.SubElement(e_link, 'site', id= 'undefined')
            ET.SubElement(e_link, 'link_attribute', key= 'nomac_learning', value='yep')
        tree = ET.ElementTree(rspec)
        tree.write(self.file[:-3] + 'xml')



def main():
    if len(sys.argv) < 2:
        print('no argument')
        sys.exit()
    if sys.argv[1].startswith('--'):
        option = sys.argv[1][2:]
        if option == 'help':
            print('enter instance.xml')
    else:
        file = sys.argv[1]
        rspec = RSPEC()
        rspec.get_graph( file )
        rspec.write_rspec()
if __name__ == '__main__':
    main()
