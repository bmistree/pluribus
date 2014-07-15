import time
import threading

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, CONFIG_DISPATCHER
from ryu.ofproto import ofproto_v1_3
from ryu.ofproto import ofproto_v1_3_parser
from ryu.controller import dpset
from ryu.controller.handler import set_ev_cls
from ryu.ofproto.ofproto_v1_3_parser import OFPPortDescStatsRequest

PORT_1 = 1
PORT_2 = 2

class RegularRyu(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    _CONTEXTS = {'dpset': dpset.DPSet}
    
    def __init__(self, *args, **kwargs):
        '''
        Just install an entry that forwards any traffic from port 1 to
        port 2 and vice versa.
        '''
        super(RegularRyu, self).__init__(*args, **kwargs)
        self.switch_dp = None

    @set_ev_cls(ofp_event.EventOFPPortDescStatsReply, [MAIN_DISPATCHER])
    def recv_port_stats_response(self,ev):
        for p in ev.msg.body:
            print '\n\n'
            print p.port_no
            print '\n\n'

            if p.port_no ==  ofproto_v1_3.OFPP_LOCAL:
                # do not forward back local port to other principals
                continue


    def send_port_stats_request(self):
        '''
        Request port stats
        '''
        time.sleep(10)
        port_desc_stats_msg = OFPPortDescStatsRequest(self.switch_dp)
        self.switch_dp.send_msg(port_desc_stats_msg)
            
        
    @set_ev_cls(ofp_event.EventOFPSwitchFeatures,[CONFIG_DISPATCHER])
    def recv_switch_features_response(self,ev):
        msg = ev.msg
        print '\nGot switch response\n'
        self.switch_dp = msg.datapath

        t = threading.Thread(target=self.install_rules)
        # t = threading.Thread(target=self.send_port_stats_request)
        t.setDaemon(True)
        t.start()

    def install_rules(self):
        time.sleep(10)
        print '\nAbout to install rules\n'

        match_one_to_two = self.switch_dp.ofproto_parser.OFPMatch(
            in_port=PORT_1)
        actions_one_to_two = [ofproto_v1_3_parser.OFPActionOutput(PORT_2)]
        self.perform_mod(match_one_to_two,actions_one_to_two)
        
        match_two_to_one = self.switch_dp.ofproto_parser.OFPMatch(
            in_port=PORT_2)
        actions_two_to_one = [self.switch_dp.ofproto_parser.OFPActionOutput(PORT_1)]
        self.perform_mod(match_two_to_one,actions_two_to_one)


    def perform_mod(self,match,actions):
        table_id = 0
        priority = 30

        instruction_actions = ofproto_v1_3_parser.OFPInstructionActions(
            ofproto_v1_3.OFPIT_APPLY_ACTIONS,actions)
        
        instructions = [
            instruction_actions
            ]

        
        flow_mod_msg = ofproto_v1_3_parser.OFPFlowMod(
            self.switch_dp, # datapath
            20, # cookie
            0, # cookie_mask

            table_id,
                        
            ofproto_v1_3.OFPFC_ADD, # command
            0, # idle_timeout
            0, # hard_timeout

            priority, # priority

            ofproto_v1_3.OFP_NO_BUFFER, # buffer_id
            23, # out_port
            0, # out_group
            0, # flags
            
            match,
            instructions)
        flow_mod_msg.serialize()
        self.switch_dp.send_msg(flow_mod_msg)


    @set_ev_cls(ofp_event.EventOFPErrorMsg,
                [CONFIG_DISPATCHER, MAIN_DISPATCHER])
    def error_msg_handler(self, ev):
        msg = ev.msg
        print '\n\n'
        print (
            'OFPErrorMsg received during initialization: ' +
            ('type=0x%02x code=0x%02x  ' % (msg.type, msg.code)) +
            'QUITTING')
        print '\n\n'
        
