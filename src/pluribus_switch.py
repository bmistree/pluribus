
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

if __name__ == '__main__':
    import time
    ps = PluribusSwitch()
    for i in range(0,50):
        time.sleep(5)
        print '%i of %i' % (i,50)
    
