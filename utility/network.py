
import csv, pickle
from tempfile import TemporaryDirectory
from collections import defaultdict

from utility import geni
from utility import ssh
from utility import cal

class net:

    def __init__( self ):
        self.topo = None
        self.demand_map_file = dict()

    def set_topo(self, file):
        with open(file, 'rb') as file:
            self.topo =  pickle.load(file)

    def clean_geni_folder(self):
        I = geni.GENI()
        I.G = self.topo
        I.clear_all()

    def upload_node_script(self):
        with TemporaryDirectory() as dirname:
            print('dirname', dirname)
            for n, info in self.topo.nodes(data=True):
                node = info['object']
                if node.type == "switch" and node.flow_table:
                    with open(dirname +'/'+ node.name + '.sh', 'w') as f:
                        f.write('#!/bin/bash\n')
                        for row in node.flow_table:
                            if 'tp_dst' in row:
                                f.write(row + '\n')
                    print(dirname +'/'+ node.name + '.sh')
                if node.type == "host":
                    if node.server_script:
                        #print(n,node.server_script)
                        with open(dirname +'/'+ node.name + '_server.sh','w') as f:
                            f.write('#!/bin/bash\n')
                            for row in node.server_script:
                                f.write(row + '\n')
                        print(dirname +'/'+ node.name + '_server.sh')
                    if node.client_script:
                        with open(dirname +'/'+ node.name + '_client.sh','w') as f:
                            f.write('#!/bin/bash\n')
                            for row in node.client_script:
                                f.write(row + '\n')
                        print(dirname +'/'+ node.name + '_client.sh')

            #I = geni.GENI()
            #I.G = self.topo
            #I.clear_all()
            ssh.send_switch_script( self.topo, dirname = dirname)
            ssh.send_host_server(self.topo, dirname = dirname)
            #ssh.run_host_server(self.topo, dirname = dirname)
            ssh.send_host_client(self.topo, dirname = dirname)

    def run_traffic(self):
        I = geni.GENI()
        I.G = self.topo
        I.run_traffic()

    def run_server(self):
        I = geni.GENI()
        I.G = self.topo
        I.run_server_script()

    def download_node_data(self, path_file):
        with TemporaryDirectory() as dirname:
            print('dirname', dirname)
            ssh.get_host_data( self.topo, dirname = dirname)

            calculate = cal.Calculate()
            calculate.set_demand_map_file( self.demand_map_file )
            calculate.set_path( path_file )
            calculate.get_data( dirname = dirname )
            calculate.write_data( path_file.split('/')[2] )



class rule:

    def __init__( self ):
        self.path = None

    def set_path(self, file):
        with open(file, 'r') as f:
            reader = csv.reader(f)
            next(reader)
            path_list = list()
            for row in reader:
                src, dst, path, size = row[0], row[1], tuple(row[3:-1]), float(row[-1])
                path_list.append((src,dst,path,size))
        self.path = path_list

    def add_path_into_net(self, net):
        graph = net.topo

        for src, dst, path, size in self.path:
            print('path: {}, size: {}k'.format(path, size))
            #print(graph.node['h' + src]['object'])

            for i, n in enumerate(path):
                #print(graph.node[n]['object'])
                if i==0:
                    """ set client server script """
                    client = graph.node['h' + src ]['object']
                    server = graph.node['h' + dst ]['object']
                    self.set_client_script(client=client, server=server, size=size)
                    file_name = self.set_server_script(server=server)
                    net.demand_map_file[(src, dst, server.server_port, path, size)] = file_name

                    """ set switch rule """
                    node = graph.node['s'+n]['object']
                    nexthop = graph.node['s'+path[i+1]]['object']
                    priorhop = graph.node['h' + src]['object']
                    self.set_switch_rule( node=node, nexthop=nexthop, priorhop=priorhop,\
                                            client=client, server=server)

                elif i == len(path)-1:
                    node = graph.node['s'+n]['object']
                    nexthop = graph.node['h' + dst]['object']
                    priorhop = graph.node['s'+path[i-1]]['object']
                    self.set_switch_rule( node=node, nexthop=nexthop, priorhop=priorhop,\
                                            client=client, server=server)
                    nexthop.server_port += 1
                else:
                    node = graph.node['s'+n]['object']
                    nexthop = graph.node['s'+path[i+1]]['object']
                    priorhop = graph.node['s'+path[i-1]]['object']
                    self.set_switch_rule( node=node, nexthop=nexthop, priorhop=priorhop,\
                                            client=client, server=server)
            #print(graph.node['h' + dst]['object'])

    def set_client_script(self, client, server, size):
        #print(client.name)
        port = server.server_port
        server_ip = server.get_ip()
        client_script = client.client_script
        if float(size) < 1000:
            cmd = "iperf -c {0} -b {1}k -t 100 -p {2} &".format(server_ip, float(size), port)
        else:
            cmd = "iperf -c {0} -b {1}k -t 100 -p {2} &".format(server_ip, float(size), port)
        client_script.append(cmd)
        #print(cmd)

    def set_server_script(self, server):
        server_ip = server.get_ip()
        port = server.server_port
        server_script = server.server_script
        file = "{0}:{1}".format(server_ip, port)
        server.server_data.append(file)
        cmd = "iperf -s -u -f k -p {0} >/tmp/{1}.txt &".format(port, file)
        #print(cmd)
        server_script.append(cmd)
        return "{0}.txt".format(file)

    def set_switch_rule(self, node, nexthop, priorhop, client, server):
        port = server.server_port
        server_ip = server.get_ip()
        client_ip = client.get_ip()
        dl_src = node.get_intf( direction = nexthop.name )['mac_address']
        dl_dst = nexthop.get_intf( direction = node.name )['mac_address']
        ofport = node.get_intf( direction = nexthop.name )['ofport']
        flow_table = node.flow_table
        flow_limit = int(node.flow_limit)
        if len(flow_table) <= 2*flow_limit + 1:
        #if True:
            cmd = "sudo ovs-ofctl -O OpenFlow13 add-flow br0 table=0,udp,hard_timeout=3000,priority=6,nw_src={0},nw_dst={1},tp_dst={2},actions=mod_dl_src={3},mod_dl_dst={4},output:{5}"\
                    .format(client_ip, server_ip, port, dl_src, dl_dst, ofport)
        else:
            cmd = "sudo ovs-ofctl -O OpenFlow13 add-flow br0 table=1,udp,hard_timeout=3000,priority=6,nw_src={0},nw_dst={1},tp_dst={2},actions=mod_dl_src={3},mod_dl_dst={4},output:{5}"\
                    .format(client_ip, server_ip, port, dl_src, dl_dst, ofport)
        flow_table.append(cmd)

        dl_src = node.get_intf( direction = priorhop.name )['mac_address']
        dl_dst = priorhop.get_intf( direction = node.name )['mac_address']
        ofport = node.get_intf( direction = priorhop.name )['ofport']
        if len(flow_table) <= 2*flow_limit + 1:
        #if True:
            cmd = "sudo ovs-ofctl -O OpenFlow13 add-flow br0 table=0,udp,hard_timeout=3000,priority=6,nw_src={0},nw_dst={1},tp_src={2},actions=mod_dl_src={3},mod_dl_dst={4},output:{5}"\
                    .format(server_ip, client_ip, port, dl_src, dl_dst, ofport)
        else:
            cmd = "sudo ovs-ofctl -O OpenFlow13 add-flow br0 table=1,udp,hard_timeout=3000,priority=6,nw_src={0},nw_dst={1},tp_src={2},actions=mod_dl_src={3},mod_dl_dst={4},output:{5}"\
                    .format(server_ip, client_ip, port, dl_src, dl_dst, ofport)
        flow_table.append(cmd)


class controller:

    def __init__( self ):
        self.flows = defaultdict(dict)

    def add_path_into_controller(self, net):
        for n, info in net.topo.nodes( data=True ):
            node = info['object']
            if node.type == 'switch':
                print('node: {}, datapath_id: {}'.format(node.name, node.datapath_id))
                for rule in node.flow_table:
                    actions = []
                    tp_dst = None
                    tp_src = None
                    for i in rule.split(','):

                        if 'nw_src' in i:
                            nw_src = i.split('=')[1]
                        elif 'nw_dst' in i:
                            nw_dst = i.split('=')[1]
                        elif 'tp_dst' in i:
                            tp_dst = i.split('=')[1]
                        elif 'tp_src' in i:
                            tp_src = i.split('=')[1]
                        elif 'actions' in i:
                            actions.append('='.join(i.split('=')[1:]))
                        elif 'mod_dl' in i or 'output' in i:
                            actions.append(i)
                    if tp_src:
                        key = 'nw_src:{0}, nw_dst:{1}, tp_src:{2}'.format(nw_src, nw_dst, tp_src)
                        self.flows[node.datapath_id][key] = actions
                        print('key: {}, actions: {}'.format(key, actions))
                    elif tp_dst:
                        key = 'nw_src:{0}, nw_dst:{1}, tp_dst:{2}'.format(nw_src, nw_dst, tp_dst)
                        self.flows[node.datapath_id][key] = actions
                        print('key: {}, actions: {}'.format(key, actions))

    def output_pickle(self):
        file = open('rule.pickle','wb')
        pickle.dump(self.flows, file, protocol=2)
        file.close()
