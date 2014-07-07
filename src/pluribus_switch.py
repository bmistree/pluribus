import threading
import time

from ryu.base import app_manager
from ryu.controller import mac_to_port
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.controller import conf_switch
from ryu.controller import dpset


class PluribusSwitch(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    _CONTEXTS = {'dpset': dpset.DPSet}
    
    def __init__(self, *args, **kwargs):
        super(PluribusSwitch, self).__init__(*args, **kwargs)
        self.switch_dp = None

    def try_install(self):
        time.sleep(5)
        
        if self.switch_dp is None:
            print 'No attached switch'
            return
        
        match = self.switch_dp.ofproto_parser.OFPMatch(
            in_phy_port=1)
        priority = self.switch_dp.ofproto.OFP_DEFAULT_PRIORITY
        # should just be a drop??
        actions = []
        table_id = 1
        self.add_flow_mod(match,instructions,priority,table_id)
        
        
    def add_flow_mod(self,match,instructions,priority,table_id):
        flow_mod = self.switch_dp.ofproto_parser.OFPFlowMod(
            # default
            datapath=self.switch_dp, cookie=0,
            cookie_mask=0,

            table_id=table_id,
                        
            command=self.switch_dp.ofproto.OFPFC_ADD,
            idle_timeout=0, hard_timeout=0,

            priority=priority,

            buffer_id = self.switch_dp.ofproto.OFP_NO_BUFFER,
            out_port=0,out_group=0,flags=0,
            
            match = match,
            instructions=instructions)
        
        
    @set_ev_cls(conf_switch.EventConfSwitchSet)
    def conf_switch_set_handler(self, ev):
        print '\n\nGot envent set\n\n'

    @set_ev_cls(conf_switch.EventConfSwitchDel)
    def conf_switch_del_handler(self, ev):
        print '\n\nGot envent del\n\n'

    @set_ev_cls(conf_switch.EventConfSwitchDel)
    def conf_switch_del_handler(self, ev):
        print '\n\nGot envent del\n\n'

    @set_ev_cls(conf_switch.EventConfSwitchDel)
    def dp_switch_del_handler(self, ev):
        print '\n\nGot envent del\n\n'

    @set_ev_cls(dpset.EventDP, dpset.DPSET_EV_DISPATCHER)
    def dp_evt (self,ev):
        if ev.dp.state == MAIN_DISPATCHER:
            print 'Got new switch'
            self.switch_dp = ev.dp
            print self.switch_dp.ofproto
            t = threading.Thread(target=self.try_install)
            t.start()


            
    # def get_switch_features(self):
    #     '''Gets number of available tables.
    #     '''
    #     m = dp.ofproto_parser.OFPFeaturesRequest(dp)
    #     dp.send_msg(m)
            
        
    # def add_flow(self, datapath, in_port, dst, actions,table):
    #     ofproto = datapath.ofproto

    #     match = datapath.ofproto_parser.OFPMatch(
    #         in_port=in_port, dl_dst=haddr_to_bin(dst))

    #     mod = datapath.ofproto_parser.OFPFlowMod(
    #         datapath=datapath, match=match, cookie=0,
    #         command=ofproto.OFPFC_ADD, idle_timeout=0, hard_timeout=0,
    #         priority=ofproto.OFP_DEFAULT_PRIORITY,
    #         flags=ofproto.OFPFF_SEND_FLOW_REM, actions=actions)
    #     datapath.send_msg(mod)
