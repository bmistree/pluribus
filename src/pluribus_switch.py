import threading
import time


from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, CONFIG_DISPATCHER
from ryu.controller.handler import HANDSHAKE_DISPATCHER
from ryu.controller.handler import set_ev_cls, set_ev_handler
from ryu.ofproto.ofproto_v1_3_parser import OFPEchoRequest, OFPEchoReply
from ryu.ofproto.ofproto_v1_3_parser import OFPPortDescStatsRequest
from ryu.ofproto import ofproto_v1_3
from ryu.controller import dpset
import ryu.utils


import conf
from conf import PORT_STATS_DELAY_TIME,JSON_PRINCIPALS_TO_LOAD_FILENAME
from conf import pluribus_logger

from principals_util import load_principals_from_json_file

from port_util import PortNameNumber


class SwitchState(object):
    # have no details about swtich
    UNINITIALIZED = 0,

    # When get all ports, send flow mods to set up head table and send
    # barrier.  While waiting on barrier response, in
    # INSTALLING_HEAD_TABLES state.  On successful completion of
    # barrier message, transition into RUNNING and connect to
    # principals.
    INSTALLING_HEAD_TABLES = 1,
    

    # In running state, can accept commands from principals'
    # controllers.
    RUNNING = 2


class PluribusSwitch(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    _CONTEXTS = {'dpset': dpset.DPSet}
    
    def __init__(self, principals_cls, *args, **kwargs):
        '''
        @param {Principals class object} principals_cls --- Class to
        generate principals.
        '''
        super(PluribusSwitch, self).__init__(*args, **kwargs)

        self.principals = []
        if JSON_PRINCIPALS_TO_LOAD_FILENAME is not None:
            self.principals = load_principals_from_json_file(
                principals_cls,JSON_PRINCIPALS_TO_LOAD_FILENAME,self)
            
        self.state = SwitchState.UNINITIALIZED
        # all of these fields get loaded before transitioning int run state.
        self.switch_dp = None
        self.switch_num_tables = None

        self.port_name_number_list = None

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
            echo_msg = OFPEchoRequest(self.switch_dp)
            self.switch_dp.send_msg(echo_msg)
        else:
            # not yet initialized
            assert False
            
    def send_port_stats_request(self):
        '''
        Request port stats
        '''
        port_desc_stats_msg = OFPPortDescStatsRequest(self.switch_dp)
        self.switch_dp.send_msg(port_desc_stats_msg)
            
    def send_barrier(self):
        self.switch_dp.send_barrier()
        
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

        self.send_msg(flow_mod_msg)

    def send_msg(self,msg_to_send):
        '''
        @param {Subclass of MsgBase} msg_to_send
        '''
        self.switch_dp.send_msg(msg_to_send)        

    @set_ev_cls(ofp_event.EventOFPBarrierReply, MAIN_DISPATCHER)                
    def recv_barrier_response(self,ev):
        if self.state == SwitchState.INSTALLING_HEAD_TABLES:
            self._transition_from_installing_head_tables()
        else:
            # actually process barrier response
            pluribus_logger.error(
                'Received barrier response when running.  Must finish.')
            
    @set_ev_cls(ofp_event.EventOFPPortDescStatsReply, [MAIN_DISPATCHER])
    def recv_port_stats_response(self,ev):
        if self.state != SwitchState.RUNNING:
            self._init_recv_port_stats_response_config(ev)
        else:
            # actually process port stats responses for 
            pluribus_logger.error(
                'Received port stats when running.  Must finish.')


    @set_ev_cls(ofp_event.EventOFPErrorMsg,
                [CONFIG_DISPATCHER, MAIN_DISPATCHER])
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

        
    @set_ev_cls(ofp_event.EventOFPEchoReply,[MAIN_DISPATCHER])
    def recv_echo_response(self, ev):
        pass
    
            
    ##### Switch initialization code ####
    
    def _init_recv_port_stats_response_config(self,ev):
        '''
        As part of initialization, determine which ports are logical
        and which ports are physical.
        '''
        self.port_name_number_list = []
        for p in ev.msg.body:
            self.port_name_number_list.append(
                PortNameNumber(p.name,p.port_no))        

        if self.state == SwitchState.UNINITIALIZED:
            self._transition_from_uninitialized()
        #### DEBUG
        else:
            pluribus_logger.error(
                'Unexpected state transition when receiving response')
            assert False
        #### END DEBUG

    def _transition_from_installing_head_tables(self):
        '''
        Should connect to principals and transition into running
        state.
        '''
        pluribus_logger.info('Transitioning into running state')
        self.state = SwitchState.RUNNING

        for principal in self.principals:
            principal.connect()


    def _transition_from_uninitialized(self):
        '''
        When receive port stats, can start allocating virtual ports to
        principals and installing head table.  This method does that.

        Does four things:
          0) Transition into INSTALLING_HEAD_TABLES state
          1) Assigns each principal a set of physical tables.
          2) Assigns each principal a set of logical ports.
          3) Sets a head table that gotos the principal's
             first table.
        
        '''
        # should be overridden by subclasses
        assert False
            
            
    @set_ev_cls(ofp_event.EventOFPSwitchFeatures,[CONFIG_DISPATCHER])
    def _recv_switch_features_response(self,ev):
        msg = ev.msg
        self.switch_num_tables = msg.n_tables
        self.switch_dp = msg.datapath

        pluribus_logger.info(
            'Received switch features.  Num tables %i' %
            msg.n_tables)

        if self.state == SwitchState.UNINITIALIZED:
             self._delayed_port_stats_request_outer(PORT_STATS_DELAY_TIME)
        #### DEBUG
        else:
            pluribus_logger.error('Unexpected state transition')
            assert False
        #### END DEBUG

    def _delayed_port_stats_request_outer(self,seconds_to_delay):
        '''
        @param {int} seconds_to_delay
        
        Wait seconds_to_delay before sending a port stats request.
        '''
        t = threading.Thread(
            target=self._delayed_port_stats_request_inner,
            args=(seconds_to_delay,))
        t.start()

    def _delayed_port_stats_request_inner(self,seconds_to_delay):
        time.sleep(seconds_to_delay)
        self.send_port_stats_request()
        
