from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.ofproto import ether, inet
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types
from ryu.lib.packet.udp import udp
from ryu.lib.packet.ipv4 import ipv4 

import pickle
import array


class controller(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(controller, self).__init__(*args, **kwargs)
        with open('/tmp/rule.pickle', 'rb') as file:
            self.flows =  pickle.load(file)
        
        
        for i, d in self.flows.items():
            print i
            for j, k in d.items():
                print j,k

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # install table-miss flow entry
        #
        # We specify NO BUFFER to max_len of the output action due to
        # OVS bug. At this moment, if we specify a lesser number, e.g.,
        # 128, OVS will send Packet-In with invalid buffer_id and
        # truncated packet data. In that case, we cannot output packets
        # correctly.  The bug has been fixed in OVS v2.1.0.

        match = parser.OFPMatch(eth_type=ether.ETH_TYPE_IP,
                                ip_proto=inet.IPPROTO_UDP )
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        #actions = [parser.OFPActionOutput(port=1)]
        self.add_flow(datapath, 0, match, actions)

    def add_flow(self, datapath, priority, match, actions, buffer_id=None, hard_timeout=None):
        #print('add_flow!!!!!!!!!!!')
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]
        if buffer_id:
            if hard_timeout:
                mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id,
                                        priority=priority, match=match,
                                        instructions=inst, hard_timeout=hard_timeout)
            else:
                mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id,
                                        priority=priority, match=match,
                                        instructions=inst)
        else:
            if hard_timeout:
                mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                        match=match, instructions=inst,
                                        hard_timeout=hard_timeout)
            else:
                mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                        match=match, instructions=inst)
        print('send_msg!!!!')
        datapath.send_msg(mod)
        #print('send_msg!!!!!!!!!!!')

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        # If you hit this you might want to increase
        # the "miss_send_length" of your switch
        if ev.msg.msg_len < ev.msg.total_len:
            self.logger.debug("packet truncated: only %s of %s bytes",
                              ev.msg.msg_len, ev.msg.total_len)
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']

        pkt = packet.Packet(array.array('B',msg.data))
        print 'datapath_id %s'%(datapath.id)

        if pkt.get_protocol(ipv4):
            ipv4_pkt = pkt.get_protocol(ipv4)
            #print('src ip: %s, dst ip: %s'%(ipv4_pkt.src, ipv4_pkt.dst))
            
        if pkt.get_protocol(udp):
            udp_pkt = pkt.get_protocol(udp)
            #print('src port: %d, dst port: %d'%(udp_pkt.src_port, udp_pkt.dst_port))
        
        key = ('nw_src:{0}, nw_dst:{1}, tp_dst:{2}'.format(ipv4_pkt.src, ipv4_pkt.dst, udp_pkt.dst_port))
        #print self.flows[datapath.id][key]
        match = parser.OFPMatch(eth_type=ether.ETH_TYPE_IP,
                                ip_proto=inet.IPPROTO_UDP,
                                ipv4_src=ipv4_pkt.src,
                                ipv4_dst=ipv4_pkt.dst,
                                udp_dst=udp_pkt.dst_port)
        
        if key not in self.flows[datapath.id]:
            key = ('nw_src:{0}, nw_dst:{1}, tp_src:{2}'.format(ipv4_pkt.src, ipv4_pkt.dst, udp_pkt.src_port))
            match = parser.OFPMatch(eth_type=ether.ETH_TYPE_IP,
                                ip_proto=inet.IPPROTO_UDP,
                                ipv4_src=ipv4_pkt.src,
                                ipv4_dst=ipv4_pkt.dst,
                                udp_src=udp_pkt.src_port)
        
        #print self.flows[datapath.id][key]
        if key in self.flows[datapath.id]:
            for i in self.flows[datapath.id][key]:
                if 'mod_dl_src' in i:
                    mod_dl_src = i.split('=')[1]
                    print 'mod_dl_src:',mod_dl_src
                elif 'mod_dl_dst' in i:
                    mod_dl_dst = i.split('=')[1]
                    print 'mod_dl_dst:',mod_dl_dst
                elif 'output' in i:
                    output = i.split(':')[1]
                    print 'output:',output
         
            actions = [parser.OFPActionSetField(eth_src=mod_dl_src), parser.OFPActionSetField(eth_dst=mod_dl_dst), parser.OFPActionOutput(port=int(output))]
        #actions = [parser.OFPActionOutput(port=int(output))]
        if 'tp_dst' in key:
            self.add_flow(datapath, 6, match, actions, hard_timeout=3000)
        #else:
        #    self.add_flow(datapath, 6, match, actions)

            data = None
            if msg.buffer_id == ofproto.OFP_NO_BUFFER:
                data = msg.data
            
            out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                        in_port=in_port, actions=actions, data=data)
            datapath.send_msg(out)




       

        

