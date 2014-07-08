import threading
import time

from ryu.base import app_manager
from ryu.controller import mac_to_port
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, CONFIG_DISPATCHER
from ryu.controller.handler import set_ev_cls, set_ev_handler
from ryu.ofproto.ofproto_v1_3_parser import OFPInstructionGotoTable
from ryu.ofproto.ofproto_v1_3_parser import OFPEchoRequest
from ryu.ofproto.ofproto_v1_3_parser import OFPPortDescStatsRequest
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.controller import conf_switch
from ryu.controller import dpset
import ryu.utils

class PluribusSwitch(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    _CONTEXTS = {'dpset': dpset.DPSet}
    
    def __init__(self, *args, **kwargs):
        super(PluribusSwitch, self).__init__(*args, **kwargs)
        self.switch_dp = None
        self.switch_num_tables = None
        
    def try_install(self):
        '''
        Simple example method to try installing a dummy rule
        '''
        time.sleep(20)
        
        if self.switch_dp is None:
            print 'No attached switch'
            return

        print '\nSending request\n'
        self.send_port_stats_request()
        
        # try to install a new flow mod
        match = self.switch_dp.ofproto_parser.OFPMatch(
            in_port=1)
        
        priority = self.switch_dp.ofproto.OFP_DEFAULT_PRIORITY
        table_id = 1
        # test is to add a goto
        instructions = [OFPInstructionGotoTable(table_id+1)]
        self.add_flow_mod(match,instructions,priority,table_id)
        
    def send_feature_request(self):
        '''
        Send a request to get switch's features
        '''
        if self.switch_dp is not None:
            feature_msg = self.switch_dp.ofproto_parser.OFPFeaturesRequest(
                self.switch_dp)
            self.switch_dp.send_msg(feature_msg)
        else:
            # not yet initialized
            assert False

    def send_echo_request(self):
        '''
        Send an echo to switch
        '''
        if self.switch_dp is not None:
            print '\nSending echo request\n'
            echo_msg = OFPEchoRequest(self.switch_dp)
            self.switch_dp.send_msg(echo_msg)
        else:
            # not yet initialized
            assert False

    def send_port_stats_request(self):
        '''
        Request port stats
        '''
        print '\nSending port stats request\n'
        port_desc_stats_msg = OFPPortDescStatsRequest(self.switch_dp)
        self.switch_dp.send_msg(port_desc_stats_msg)
            
            
    def add_flow_mod(self,match,instructions,priority,table_id):
        flow_mod_msg = self.switch_dp.ofproto_parser.OFPFlowMod(
            self.switch_dp, # datapath
            0, # cookie
            0, # cookie_mask

            table_id,
                        
            self.switch_dp.ofproto.OFPFC_ADD, # command
            0, # idle_timeout
            0, # hard_timeout

            priority, # priority

            self.switch_dp.ofproto.OFP_NO_BUFFER, # buffer_id
            0, # out_port
            0, # out_group
            0, # flags
            
            match,
            instructions)

        self.switch_dp.send_msg(flow_mod_msg)
        print '\nSending flow mod\n'

    @set_ev_cls(ofp_event.EventOFPPortDescStatsReply, [MAIN_DISPATCHER])
    def recv_port_stats_response(self,ev):
        ports = []
        print '\nReceived port stats response\n'
        for p in ev.msg.body:
            ports.append('port_no=%d hw_addr=%s name=%s config=0x%08x '
                         'state=0x%08x curr=0x%08x advertised=0x%08x '
                         'supported=0x%08x peer=0x%08x curr_speed=%d '
                         'max_speed=%d' %
                         (p.port_no, p.hw_addr,
                          p.name, p.config,
                          p.state, p.curr, p.advertised,
                          p.supported, p.peer, p.curr_speed,
                          p.max_speed))
        print '\n'
        for port in ports:
            print port + '\n'
        print '\n'
                
    @set_ev_cls(ofp_event.EventOFPErrorMsg,
                [CONFIG_DISPATCHER, MAIN_DISPATCHER])
    def error_msg_handler(self, ev):
        msg = ev.msg

        print '\n'
        print ('OFPErrorMsg received: type=0x%02x code=0x%02x' %
               (msg.type, msg.code))
        print (ryu.utils.hex_array(msg.data))
        print msg.data
        print '\n'
        
    @set_ev_cls(ofp_event.EventOFPEchoRequest,[MAIN_DISPATCHER])
    def recv_echo_response(self, ev):
        print '\nReceived echo response\n'
        
    @set_ev_cls(ofp_event.EventOFPSwitchFeatures,[CONFIG_DISPATCHER])
    def recv_switch_features_response(self,ev):
        msg = ev.msg
        datapath = msg.datapath
        self.switch_num_tables = msg.n_tables

    @set_ev_cls(dpset.EventDP, [CONFIG_DISPATCHER])
    def dp_evt (self,ev):
        print 'Got new switch'
        self.switch_dp = ev.dp
        print self.switch_dp.ofproto
        t = threading.Thread(target=self.try_install)
        t.start()
