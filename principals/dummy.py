
'''
Dummy principal just listens for connections on target port.

Important to not use default port: middleware layer is using target
port.
'''

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, CONFIG_DISPATCHER
from ryu.controller.handler import HANDSHAKE_DISPATCHER, set_ev_cls
from ryu.ofproto.ofproto_v1_3_parser import OFPEchoRequest,OFPEchoReply
from ryu.ofproto import ofproto_v1_3
from ryu.controller import dpset

class PluribusSwitch(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    _CONTEXTS = {'dpset': dpset.DPSet}

    
    @set_ev_cls(ofp_event.EventOFPEchoReply,
                [HANDSHAKE_DISPATCHER, CONFIG_DISPATCHER, MAIN_DISPATCHER])
    def recv_echo_response(self, ev):
        print '\n\nReceived echo response\n\n'


    @set_ev_cls(ofp_event.EventOFPEchoRequest,
                [HANDSHAKE_DISPATCHER, CONFIG_DISPATCHER, MAIN_DISPATCHER])
    def recv_echo_response(self, ev):
        print '\n\nReceived echo request\n\n'

        
