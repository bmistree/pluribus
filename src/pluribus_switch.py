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

from port_util import set_logical_physical
from port_util import PortNameNumber
from port_util import num_principals_from_num_logical_port_pairs
from conf import PORT_STATS_DELAY_TIME

class SwitchState(object):
    # have no details about swtich
    UNINITIALIZED = 0

    # In running state, can accept commands from principals'
    # controllers.
    RUNNING = 1


class PluribusSwitch(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    _CONTEXTS = {'dpset': dpset.DPSet}
    
    def __init__(self, *args, **kwargs):
        super(PluribusSwitch, self).__init__(*args, **kwargs)
        self.state = SwitchState.UNINITIALIZED
        
        self.switch_dp = None
        self.switch_num_tables = None

        self.port_name_number_list = None
        self.logical_port_pair_halves = None
        self.num_principals_can_support = None
        
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

    def delayed_port_stats_request(self,seconds_to_delay):
        '''
        @param {int} seconds_to_delay
        
        Wait seconds_to_delay before sending a port stats request.
        '''
        t = threading.Thread(
            target=self._delayed_port_stats_request,args=(seconds_to_delay,))
        t.start()

    def _delayed_port_stats_request(self,seconds_to_delay):
        time.sleep(seconds_to_delay)
        self.send_port_stats_request()
            
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
    def recv_port_stats_response_config(self,ev):
        '''
        Note: only executes during config.  After config, should run
        different method, which returns port stats to connected
        principals.  However, currently calling in main dispatcher
        '''
        if self.state != SwitchState.RUNNING:
            self._init_recv_port_stats_response_config(ev)
        else:
            print '\nReceived port stats config\n'

    def _init_recv_port_stats_response_config(self,ev):
        '''
        As part of initialization, determine which ports are logical
        and which ports are physical.
        '''
        self.port_name_number_list = []
        for p in ev.msg.body:
            self.port_name_number_list.append(
                PortNameNumber(p.name,p.port_no))

        self.logical_port_pair_halves = (
            set_logical_physical(self.port_name_number_list))

        num_logical_port_pairs = len(self.logical_port_pair_halves)
        self.num_principals_can_support = (
            num_principals_from_num_logical_port_pairs(num_logical_port_pairs))

        self._debug_print_ports()

        if self.state == SwitchState.UNINITIALIZED:
            self.init_complete()
        #### DEBUG
        else:
            print 'Unexpected state transition when receiving response'
            assert False
        #### END DEBUG
        
    def init_complete(self):
        self.state = SwitchState.RUNNING
        print '\nFinished initialization\n'

    def _debug_print_ports(self):
        '''
        Helper method to ensure that got expected number of ports, etc.
        '''
        print '\n'
        print 'Total num ports: %i' % len(self.port_name_number_list)
        print 'Num logical port pairs: %i' % len(self.logical_port_pair_halves)
        print (
            'Num principals can support: %i' % self.num_principals_can_support)
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
        self.switch_num_tables = msg.n_tables
        self.switch_dp = msg.datapath

        
        print '\nReceived switch features\n'
        print msg
        print msg.n_tables
        
        if self.state == SwitchState.UNINITIALIZED:
             self.delayed_port_stats_request(PORT_STATS_DELAY_TIME)
        #### DEBUG
        else:
            print 'Unexpected state transition'
            assert False
        #### END DEBUG
