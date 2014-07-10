import socket
import threading

from ryu.lib import rpc
from ryu.ofproto import ofproto_v1_3, ofproto_v1_3_parser
from ryu.ofproto import ofproto_protocol
from ryu.controller.controller import Datapath
from ryu.lib import hub

from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, CONFIG_DISPATCHER
from ryu.controller.handler import HANDSHAKE_DISPATCHER
from ryu.controller.handler import set_ev_cls, set_ev_handler


from conf import pluribus_logger
    

class PrincipalConnection(object):

    def __init__(self,ipaddr,tcp_port,principal):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((ipaddr, tcp_port))

        self._principal = principal
        self._datapath = Datapath(s,(ipaddr,str(tcp_port)))
        self._perform_handshake()
        

    def _perform_handshake(self):
        '''
        Sends ofp hello to other side
        '''
        pluribus_logger.debug(
            'Sending handshake to principal %i' % self._principal.id)

        t = threading.Thread(self._datapath.serve)
        t.start()

    @set_ev_cls(ofp_event.OFPFeaturesRequest,
                [HANDSHAKE_DISPATCHER,CONFIG_DISPATCHER,MAIN_DISPATCHER])
    def recv_features_request(self, ev):
        print '\n\nReceived features request\n\n'




