import socket


from ryu.lib import rpc
from ryu.ofproto.ofproto_v1_3_parser import OFPHello
from ryu.ofproto import ofproto_v1_3, ofproto_v1_3_parser
from ryu.ofproto import ofproto_protocol
from ryu.controller.controller import Datapath

from conf import pluribus_logger
    

class PrincipalConnection(object):

    def __init__(self,ipaddr,tcp_port,principal):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((ipaddr, tcp_port))

        table = {
            rpc.MessageType.REQUEST: self._handle_request,
            rpc.MessageType.RESPONSE: self._handle_response,
            rpc.MessageType.NOTIFY: self._handle_notification
        }

        self._principal = principal
        
        self._principal_endpoint = rpc.EndPoint(
            s,disp_table=table)
        self._datapath = Datapath(s,(ipaddr,tcp_port))
        self._perform_handshake()
        

    def _perform_handshake(self):
        '''
        Sends ofp hello to other side
        '''
        pluribus_logger.debug(
            'Sending handshake to principal %i' % self._principal.id)
        
        ofp_hello = OFPHello(self._datapath)
        ofp_hello.serialize()
        self._principal_endpoint._send_message(ofp_hello.buf)

        
    def _handle_request(self,m):
        print '\nHandling some request\n'
    def _handle_response(self,m):
        print '\nHandling some response\n'
    def _handle_notification(self,m):
        print '\nHandling some notification\n'




