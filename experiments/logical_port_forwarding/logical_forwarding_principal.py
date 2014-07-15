'''
Listens on a target port and sends configurations into controller to
forward between virtual switches.
'''
import threading
import time
from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, CONFIG_DISPATCHER
from ryu.controller.handler import HANDSHAKE_DISPATCHER, set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.controller import dpset

ARP_ETH_TYPE = 0x0806

PORT_1 = 1
PORT_2 = 2
PORT_3 = 3
PORT_4 = 4

class LogicalForwardingPrincipal(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    _CONTEXTS = {'dpset': dpset.DPSet}

    @set_ev_cls(ofp_event.EventOFPDescStatsReply,
                [HANDSHAKE_DISPATCHER, CONFIG_DISPATCHER, MAIN_DISPATCHER])
    def recv_desc_stats(self, ev):
        print '\n\nReceived desc stats\n\n'
        t = threading.Thread(
            target=self.send_delayed_flow_mods,args=(ev.msg.datapath,))
        t.start()
        
    def send_delayed_flow_mods(self,datapath):
        time.sleep(5)
        print '\nSending flow mod\n'

        table_id = 0
        arp_priority = 3000

        # handling arp packets
        actions_arp = [
            datapath.ofproto_parser.OFPActionOutput(
                datapath.ofproto.OFPP_NORMAL)]
        instruction_actions = datapath.ofproto_parser.OFPInstructionActions(
            datapath.ofproto.OFPIT_APPLY_ACTIONS,actions_arp)
        instructions = [ instruction_actions ]

        match_arps_between = datapath.ofproto_parser.OFPMatch(
            eth_type=ARP_ETH_TYPE)
        self.send_flow_mod(
            datapath,table_id,arp_priority,match_arps_between,instructions)

        # can't figure out how to pass in command line arguments to
        # switch.  instead, just going to try to send sets of flow
        # mods for both right and left switches.  For each switch, one
        # set of flow mods will cause an exception on virtualization
        # layer.  But, that shouldn't be too big of a deal for the
        # controller.
        self.left_switch_flow_mods(datapath)
        self.right_switch_flow_mods(datapath)
        
        

    def left_switch_flow_mods(self,datapath):
        # left switch holds ports one and four
        self.ingress_egress_switch(datapath,PORT_1,PORT_4)

    def right_switch_flow_mods(self,datapath):
        # right switch houses ports two and three
        self.ingress_egress_switch(datapath,PORT_2,PORT_3)
        
    def ingress_egress_switch(self,datapath,left_port,right_port):
        table_id = 0
        priority = 10

        # ingress on port left_port, output on right_port
        in_left_out_right_match = datapath.ofproto_parser.OFPMatch(
            in_port=left_port)
        in_left_out_right_actions_to_apply = [
            datapath.ofproto_parser.OFPActionOutput(right_port)]
        self.send_flow_mod_with_actions_to_apply(
            datapath,table_id,priority,in_left_out_right_match,
            in_left_out_right_actions_to_apply)

        # ingress on port right_port, output on left_port
        in_right_out_left_match = datapath.ofproto_parser.OFPMatch(
            in_port=right_port)
        in_right_out_left_actions = [
            datapath.ofproto_parser.OFPActionOutput(left_port)]
        self.send_flow_mod_with_actions_to_apply(
            datapath,table_id,priority,in_right_out_left_match,
            in_right_out_left_to_apply)
        

    def send_flow_mod_with_actions_to_apply(
        self,datapath,table_id,priority,match,actions_to_apply):
        
        instruction_actions = datapath.ofproto_parser.OFPInstructionActions(
            datapath.ofproto.OFPIT_APPLY_ACTIONS,actions_to_apply)

        self.send_flow_mod(datapath,table_id,priority,match,instruction_actions)
        
        
    def send_flow_mod(self,datapath,table_id,priority,match,instructions):
        flow_mod_msg = datapath.ofproto_parser.OFPFlowMod(
            datapath, # datapath
            20, # cookie
            0, # cookie_mask

            table_id,
                        
            datapath.ofproto.OFPFC_ADD, # command
            0, # idle_timeout
            0, # hard_timeout

            priority, # priority

            datapath.ofproto.OFP_NO_BUFFER, # buffer_id
            23, # out_port
            0, # out_group
            0, # flags
            
            match,
            instructions)
        datapath.send_msg(flow_mod_msg)
