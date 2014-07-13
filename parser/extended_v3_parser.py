from ryu.ofproto import ofproto_v1_3 as ofproto
from ryu.ofproto.ofproto_v1_3_parser import _register_parser
from ryu.ofproto.ofproto_v1_3_parser import _set_msg_type, _set_stats_type
from ryu.ofproto.ofproto_parser import StringifyMixin, MsgBase, msg_pack_into, msg_str_attr
from ryu.controller.ofp_event import _create_ofp_msg_ev_class

from ryu.ofproto.ofproto_v1_3_parser import OFPFeaturesRequest as FeaturesRequestClass
from ryu.ofproto.ofproto_v1_3_parser import OFPSwitchFeatures as FeaturesReplyClass
from ryu.ofproto.ofproto_v1_3_parser import OFPGetConfigRequest as GetConfigRequestClass
from ryu.ofproto.ofproto_v1_3_parser import OFPSetConfig as SetConfigClass
from ryu.ofproto.ofproto_v1_3_parser import OFPMultipartRequest as MultipartRequestClass

from ryu.ofproto.ofproto_v1_3_parser import OFPDescStatsRequest as DescStatsRequestClass
from ryu.ofproto.ofproto_v1_3_parser import OFPDescStatsReply as DescStatsReplyClass
from ryu.ofproto.ofproto_v1_3_parser import OFPPortStatsRequest as PortStatsRequestClass
from ryu.ofproto.ofproto_v1_3_parser import OFPFlowMod as FlowModClass

from ryu.ofproto.ofproto_v1_3_parser import OFPMatch, OFPInstruction
import ryu.utils

from ryu.ofproto.ofproto_v1_3_parser import OFPDescStats, OFPPortStats
import struct

@_register_parser
@_set_msg_type(ofproto.OFPT_FEATURES_REQUEST)
class OFPFeaturesRequest(FeaturesRequestClass):
    '''
    Features request mesages are empty.  Only an openflow header.  No
    advanced parsing necessary.
    '''
    @classmethod
    def parser(cls, datapath, version, msg_type, msg_len, xid, buf):
        msg = super(OFPFeaturesRequest, cls).parser(
            datapath, version, msg_type,
            msg_len, xid, buf)
        return msg
_create_ofp_msg_ev_class(OFPFeaturesRequest)



@_set_msg_type(ofproto.OFPT_FEATURES_REPLY)
class OFPSwitchFeatures(FeaturesReplyClass):
    '''    
    Default switch features essentially has a blank serialize method.
    This is because ryu does not actually generate this message
    itself.  Adding these methods so that when serialize, it works
    correctly.
    
    '''
    def serialize(self):
        fmt = ofproto.OFP_HEADER_PACK_STR
        version = ofproto.OFP_VERSION
        msg_type = ofproto.OFPT_FEATURES_REPLY
        msg_len = ofproto.OFP_SWITCH_FEATURES_SIZE
        xid = 5
        
        buf = struct.pack(fmt, version, msg_type, msg_len, xid)
        buf += struct.pack(
            ofproto.OFP_SWITCH_FEATURES_PACK_STR,
            self.datapath_id,
            self.n_buffers,
            self.n_tables,
            self.auxiliary_id,
            self.capabilities,
            ofproto.OFP_HEADER_SIZE)
        self.buf = buf


@_register_parser
@_set_msg_type(ofproto.OFPT_GET_CONFIG_REQUEST)
class OFPGetConfigRequest(GetConfigRequestClass):
    @classmethod
    def parser(cls, datapath, version, msg_type, msg_len, xid, buf):
        msg = super(OPFGetConfigRequest, cls).parser(
            datapath, version, msg_type,
            msg_len, xid, buf)
        return msg

_create_ofp_msg_ev_class(OFPGetConfigRequest)


@_register_parser
@_set_msg_type(ofproto.OFPT_SET_CONFIG)
class OFPSetConfig(SetConfigClass):
    
    @classmethod
    def parser(cls, datapath, version, msg_type, msg_len, xid, buf):
        msg = super(OFPSetConfig, cls).parser(
            datapath, version, msg_type,
            msg_len, xid, buf)
        (msg.flags, msg.miss_send_len) = struct.unpack_from(
            ofproto.OFP_EXPERIMENTER_HEADER_PACK_STR, msg.buf,
            ofproto.OFP_HEADER_SIZE)
        
        return msg
    
_create_ofp_msg_ev_class(OFPSetConfig)


@_register_parser
@_set_stats_type(ofproto.OFPMP_DESC, OFPDescStats)
@_set_msg_type(ofproto.OFPT_MULTIPART_REQUEST)
class OFPDescStatsRequest(DescStatsRequestClass):
    @classmethod
    def parser(cls, datapath, version, msg_type, msg_len, xid, buf):
        msg = super(OFPDescStatsRequest, cls).parser(
            datapath, version, msg_type,
            msg_len, xid, buf)
        
        (msg.type,msg.flags) = struct.unpack_from(
            ofproto.OFP_MULTIPART_REQUEST_PACK_STR,
            msg.buf,ofproto.OFP_HEADER_SIZE)

        return msg

_create_ofp_msg_ev_class(OFPDescStatsRequest)


class OFPDescStatsReply(DescStatsReplyClass):
    '''    
    Default switch features essentially has a blank serialize method.
    This is because ryu does not actually generate this message
    itself.  Adding these methods so that when serialize, it works
    correctly.
    '''
    def __init__(self,request_xid,datapath,type_=None,**kwargs):
        self.request_xid = request_xid
        super(OFPDescStatsReply,self).__init__(datapath,type_,**kwargs)
    
    def serialize(self):
        # generate ofp header last

        # multipart reply struct
        self.buf = struct.pack(
            '!HH4x', # network order, short uint, short uint, 4B
                     # padding
            ofproto.OFPMP_DESC,
            0 # no flags???
            )

        # FIXME: responding with hard-coded description statistics
        
        # body of reply contains desc_stats struct
        mfr_desc = 'mfr_desc'.ljust(256)
        hw_desc = 'hw_desc'.ljust(256)
        sw_desc = 'sw_desc'.ljust(256)
        serial_num = 'serial_num'.ljust(32)
        dp_desc = 'dp_desc'.ljust(256)

        self.buf += (mfr_desc +
                     hw_desc +
                     sw_desc +
                     serial_num +
                     dp_desc)

        # now that know length, generate the ofp header at top of packet
        self.buf =  struct.pack(
            ofproto.OFP_HEADER_PACK_STR,
            ofproto.OFP_VERSION,
            ofproto.OFPT_MULTIPART_REPLY,
            len(self.buf) + ofproto.OFP_HEADER_SIZE,
            int(self.request_xid)) + self.buf


@_register_parser
@_set_msg_type(ofproto.OFPT_FLOW_MOD)
class OFPFlowMod(FlowModClass):
    @classmethod
    def parser(cls, datapath, version, msg_type, msg_len, xid, buf):
        msg = super(OFPFlowMod, cls).parser(
            datapath, version, msg_type,
            msg_len, xid, buf)
        
        (msg.cookie, msg.cookie_mask,
         msg.table_id, msg.command,
         msg.idle_timeout, msg.hard_timeout,
         msg.priority, msg.buffer_id,
         msg.out_port, msg.out_group, msg.flags) = struct.unpack_from(
            ofproto.OFP_FLOW_MOD_PACK_STR0,
            msg.buf,ofproto.OFP_HEADER_SIZE)

        #### DECODE MATCHES ####
        # how far from the top of the message the match is located.
        match_offset = (ofproto.OFP_FLOW_MOD_SIZE -
                  ofproto.OFP_MATCH_SIZE)

        msg.match = OFPMatch.parser(msg.buf,match_offset)

        ##### PARSING INSTRUCTIONS
        match_length = ryu.utils.round_up(msg.match.length, 8)
        instructions_offset = match_offset + match_length
        inst_length = msg_len - instructions_offset
        
        instructions = []
        while inst_length > 0:
            inst = OFPInstruction.parser(msg.buf, instructions_offset)
            instructions.append(inst)
            instructions_offset += inst.len
            inst_length -= inst.len

        return msg
    
_create_ofp_msg_ev_class(OFPFlowMod)
