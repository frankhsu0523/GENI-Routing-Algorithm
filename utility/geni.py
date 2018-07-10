"""

Usage:
    geni.py clearall <graph_pickle> 
    geni.py cleardata <graph_pickle>
    geni.py cleartable <graph_pickle>
    geni.py run <graph_pickle>
    geni.py set_ofproto_v1_3 <graph_pickle>

Options:
    -h --help Show this screen

"""

from docopt import docopt
import os, sys, threading
import pickle
from utility.ssh import run_node_cmd

outlock = threading.Lock()

class GENI:

    def __init__( self, graph_file = None ):
        if graph_file:
            self.G = self.get_graph( graph_file )
        else:
            self.G = None

    def get_graph( self, file ):
        with open(file, 'rb') as file:
            return pickle.load(file)
    def clear_all( self ):
        threads = []
        for n, data in self.G.nodes(data=True):
            node = data['object']
            #print(node.name)
            if node.type == 'host':
                #run_node_cmd(node.login, 'sudo rm /tmp/*; sudo ls /tmp/')
                t = threading.Thread(target=run_node_cmd, args=(node.login, 'sudo rm /tmp/*; sudo ls /tmp/',))
                t.start()
                threads.append(t)
            if node.type == 'switch':
                #run_node_cmd(node.login, 'sudo rm /tmp/*; sudo ls /tmp/; \
                #            sudo ovs-ofctl del-flows br0; sudo ovs-ofctl dump-flows br0')
                t = threading.Thread(target=run_node_cmd, args=(node.login, 'sudo rm /tmp/*; sudo ls /tmp/; \
                            sudo ovs-ofctl -O OpenFlow13 del-flows br0; sudo ovs-ofctl -O OpenFlow13 dump-flows br0',))
                t.start()
                threads.append(t)
        for t in threads:
            t.join()
    
    def set_ofproto_v1_3( self ):
        threads = []
        for n, data in self.G.nodes(data=True):
            node = data['object']
            if node.type == 'switch':
                cmd = 'sudo ovs-vsctl set bridge br0 protocols=OpenFlow13;sudo ovs-vsctl get bridge br0 protocols'
                print('switch: {0},command: {1}'.format(node.name, cmd))
                t = threading.Thread(target=run_node_cmd, args=(node.login, cmd))
                t.start()
                threads.append(t)
        for t in threads:
            t.join()
    
    def set_flow_table( self ):
        threads = []
        pre_flow_count = 10 #The flows have been installed in flow table before the experiment start
        for n, data in self.G.nodes(data=True):
            node = data['object']            
            if node.type == 'switch':
                cmd = 'sudo ovs-ofctl -O OpenFlow13 del-flows br0;\
                    sudo ovs-vsctl -- --id=@ft create Flow_Table flow_limit={0} overflow_policy=evict -- set Bridge br0 flow_tables:0=@ft'.format(int(node.flow_limit)+pre_flow_count)
                print('switch: {0}, command: {1}'.format(node.name, cmd))
                t = threading.Thread(target=run_node_cmd, args=(node.login, cmd))
                print("switch: {}, flow_limit: {}".format(node.name, int(node.flow_limit)+pre_flow_count))
                t.start()
                threads.append(t)
        for t in threads:
            t.join()
    
    def set_arp_table( self ):
        threads = []
        for n, data in self.G.nodes(data=True):
            node = data['object']
            if node.type == 'host':
                arp_ip = self.G.node['s'+node.name[1:]]['object'].get_intf(node.name)['ip_address']
                arp_mac_address = self.G.node['s'+node.name[1:]]['object'].get_intf(node.name)['mac_address']
                print('host: {}, arp_ip: {}, arp_mac_address: {}'.format(node.name, arp_ip, arp_mac_address))
                t = threading.Thread(target=run_node_cmd, args=(node.login, 'sudo arp -s {0} {1}'.format(arp_ip, arp_mac_address)))
                t.start()
                threads.append(t)
        for t in threads:
            t.join()

    def clear_data( self ):
        for n, data in self.G.nodes(data=True):
            node = data['object']
            print(node.name)
            run_node_cmd(node.login, 'sudo rm /tmp/*; sudo ls /tmp/')
    def clear_flow_table( self ):
        threads = []
        for n, data in self.G.nodes(data=True):
            node = data['object']
            if node.type == 'switch':
                #run_node_cmd(node.login, 'sudo ovs-ofctl del-flows br0; sudo ovs-ofctl dump-flows br0')
                t = threading.Thread(target=run_node_cmd, args=(node.login, 'sudo ovs-ofctl -O OpenFlow13 del-flows br0; sudo ovs-ofctl -O OpenFlow13 dump-flows br0',))
                t.start()
                threads.append(t)
        for t in threads:
            t.join()

    def run_traffic( self ):
        threads = []
        for n, data in self.G.nodes(data=True):
            node = data['object']
            if node.type == 'host':
                #run_node_cmd(node.login, 'sudo bash /tmp/client.sh')
                t = threading.Thread(target=run_node_cmd, args=(node.login, 'sudo bash /tmp/client.sh &',))
                t.start()
                threads.append(t)
        for t in threads:
            t.join()
    
    def run_server_script( self ):
        threads = []
        for n, data in self.G.nodes(data=True):
            node = data['object']
            if node.type == 'host':
                #run_node_cmd(node.login, 'sudo bash /tmp/client.sh')
                t = threading.Thread(target=run_node_cmd, args=(node.login, 'sudo bash /tmp/{0}_server.sh &'.format(n),))
                t.start()
                threads.append(t)
        for t in threads:
            t.join()

def main():
    args = docopt(__doc__)

    if args['clearall']:
        I = GENI( args['<graph_pickle>'] )
        I.clear_all()
    elif args['cleardata']:
        I = GENI( args['<graph_pickle>'] )
        I.clear_data()
    elif args['cleartable']:
        I = GENI( args['<graph_pickle>'] )
        I.clear_flow_table()
    elif args['run']:
        I = GENI( args['<graph_pickle>'] )
        I.run_traffic()
    elif args['set_ofproto_v1_3']:
        I = GENI( args['<graph_pickle>'] )
        I.set_ofproto_v1_3()
    

if __name__ == '__main__':
    main()
