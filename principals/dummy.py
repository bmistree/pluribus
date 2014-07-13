
'''
Dummy principal just listens for connections on target port.

Important to not use default port: middleware layer is using target
port.
'''
import threading
import time
from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, CONFIG_DISPATCHER
from ryu.controller.handler import HANDSHAKE_DISPATCHER, set_ev_cls
#from ryu.controller.handler import set_ev_handler
from ryu.ofproto.ofproto_v1_3_parser import OFPEchoRequest,OFPEchoReply
from ryu.ofproto import ofproto_v1_3
from ryu.controller import dpset

class PluribusSwitch(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    _CONTEXTS = {'dpset': dpset.DPSet}

    @set_ev_cls(ofp_event.EventOFPHello, 
                [HANDSHAKE_DISPATCHER, CONFIG_DISPATCHER, MAIN_DISPATCHER])
    def recv_hello(self, ev):
        print '\n\nReceived hello\n\n'

    
    @set_ev_cls(ofp_event.EventOFPEchoReply,
                [HANDSHAKE_DISPATCHER, CONFIG_DISPATCHER, MAIN_DISPATCHER])
    def recv_echo_response(self, ev):
        print '\n\nReceived echo response\n\n'


    @set_ev_cls(ofp_event.EventOFPEchoRequest,
                [HANDSHAKE_DISPATCHER, CONFIG_DISPATCHER, MAIN_DISPATCHER])
    def recv_echo_response(self, ev):
        print '\n\nReceived echo request\n\n'

    @set_ev_cls(ofp_event.EventOFPDescStatsReply,
                [HANDSHAKE_DISPATCHER, CONFIG_DISPATCHER, MAIN_DISPATCHER])
    def recv_desc_stats(self, ev):
        print '\n\nReceived desc stats\n\n'
        t = threading.Thread(
            target=self.send_delayed_flow_mod,args=(ev.msg.datapath,))
        t.start()
        
    def send_delayed_flow_mod(self,datapath):
        time.sleep(5)
        print '\nSending flow mod\n'

        table_id = 0
        priority = 30
        match = datapath.ofproto_parser.OFPMatch(
            in_port=30)
        instructions = [
            datapath.ofproto_parser.OFPInstructionGotoTable(1)]
        
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
            0, # out_port
            0, # out_group
            0, # flags
            
            match,
            instructions)
        datapath.send_msg(flow_mod_msg)


        
    @set_ev_cls(ofp_event.EventOFPErrorMsg,
                [HANDSHAKE_DISPATCHER,CONFIG_DISPATCHER, MAIN_DISPATCHER])
    def error_msg_handler(self, ev):
        msg = ev.msg
        
        if self.state not in SwitchState.RUNNING:
            # no graceful retries or anything if get an error while
            # setting up head tables, getting port descriptors, etc.
            # Just fail.
            pluribus_logger.error(
                'OFPErrorMsg received during initialization: ' +
                ('type=0x%02x code=0x%02x  ' % (msg.type, msg.code)) +
                'QUITTING')
            assert False

        pluribus_logger.error(
            'Received ofp error.  Must finish handler method.')


    @set_ev_cls(ofp_event.EventOFPSwitchFeatures,
                [HANDSHAKE_DISPATCHER,CONFIG_DISPATCHER, MAIN_DISPATCHER])
    def recv_switch_features_response(self,ev):
        msg = ev.msg
        self.switch_num_tables = msg.n_tables
        self.switch_dp = msg.datapath

        print ('\nReceived switch response with tables %i\n' %
               msg.n_tables)
        
