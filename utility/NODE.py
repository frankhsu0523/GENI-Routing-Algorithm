import pprint
from  utility.ssh import get_node_ofport, get_node_datapath_id


class NODE:

    def __init__(self, name):
        self.name = name
        self.datapath_id = None
        self.intf = dict()
        self.login = dict()
        self.node_to_intf = dict()
        self.type = 'host' if name[0] == 'h' else 'switch'
        if self.type is 'host':
            self.server_script = list()
            self.client_script = list()
            self.server_port = 5566
            self.server_data = list()
        if self.type is 'switch':
            self.flow_table = list()
            #self.flow_table.append('sudo ovs-ofctl add-flow br0 table=0,udp,priority=0,actions=resubmit\(,1\)')
            self.flow_limit = None

    def set_intf(self, info ):
        intf_id = info.attrib['client_id']
        ip_address = info[0].attrib['address']
        mac_address = ":".join([info.attrib['mac_address'][i:i+2] \
                                for i in range(0, len(info.attrib['mac_address']), 2)])
        self.intf[intf_id] = {'mac_address': mac_address, 'ip_address':ip_address}

    def set_login(self, info ):
        self.login = { 'hostname':info['hostname'],\
                        'username':info['username'],\
                        'port':info['port'] }

    def set_intf_ofport( self ):
        if self.login and self.intf:
            mac_to_ofport = get_node_ofport( info = self.login )
            for intf_id, info in self.intf.items():
                mac_address = info['mac_address']
                ofport = mac_to_ofport[mac_address]
                info['ofport'] = ofport
        else:
            print("error: can't get login information")

    def set_node_to_intf(self, node, intf):
        self.node_to_intf[node]=intf
    
    def set_node_datapath_id( self ):
        self.datapath_id = get_node_datapath_id( info = self.login )

    def get_ip(self):
        if self.type == 'host':
            for intf, info in self.intf.items():
                ip = info['ip_address']
        return ip

    def get_intf(self, direction ):
        intf_id = self.node_to_intf[direction]
        return self.intf[intf_id]

    def __str__(self):
        print('NAME: {0} type: {1}'.format(self.name, self.type))
        pprint.pprint(self.intf, width=1)
        pprint.pprint(self.login, width=1)
        pprint.pprint(self.node_to_intf, width=1)
        if self.type == 'host':
            print("server_script:")
            #print(*self.server_script, sep='\n')
            print("client_script:")
            #print(*self.client_script, sep='\n')
        if self.type == 'switch':
            print("datapath_id: {0}".format(self.datapath_id))
            print("flow_limit: {0}".format(self.flow_limit))
            print("flow_table:")
            #print(*self.flow_table, sep='\n')

        return '='*50
