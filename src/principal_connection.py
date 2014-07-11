import socket
import threading
import sys
import os

from ryu.lib import rpc
from ryu.ofproto import ofproto_v1_3, ofproto_v1_3_parser
from ryu.ofproto import ofproto_protocol
# from ryu.controller.controller import Datapath
from principal_datapath import PrincipalDatapath
from ryu.lib import hub

from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, CONFIG_DISPATCHER
from ryu.controller.handler import HANDSHAKE_DISPATCHER
from ryu.controller.handler import set_ev_cls, set_ev_handler

from conf import pluribus_logger


sys.path.append(
    os.path.join(
        os.path.dirname( os.path.abspath(__file__)),
        '..','parser'))
import extended_v3_parser


class PrincipalConnection(object):

    def __init__(self,ipaddr,tcp_port,principal):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((ipaddr, tcp_port))

        self.principal = principal
        self.datapath = PrincipalDatapath(self,s,(ipaddr,str(tcp_port)))
        self.perform_handshake()
        

    def perform_handshake(self):
        '''
        Sends ofp hello to other side
        '''
        pluribus_logger.debug(
            'Sending handshake to principal %i' % self.principal.id)
        t = threading.Thread(target=self.datapath.serve)
        t.start()


    def receive_principal_message(self,msg):
        '''
        Receive some message from principal.
        '''
        if isinstance(msg, extended_v3_parser.OFPFeaturesRequest):
            self.principal.handle_features_request(msg)
        else:
            pluribus_logger.error(
                'Received unknown message from principal of type' +
                str(type(msg)))
