from ryu.ofproto import ofproto_v1_3 as ofproto
from ryu.ofproto.ofproto_v1_3_parser import _register_parser
from ryu.ofproto.ofproto_v1_3_parser import _set_msg_type
from ryu.ofproto.ofproto_parser import StringifyMixin, MsgBase, msg_pack_into, msg_str_attr
from ryu.controller.ofp_event import _create_ofp_msg_ev_class

from ryu.ofproto.ofproto_v1_3_parser import OFPFeaturesRequest as FeaturesRequestClass
from ryu.ofproto.ofproto_v1_3_parser import OFPSwitchFeatures as FeaturesReplyClass
from ryu.ofproto.ofproto_v1_3_parser import OFPGetConfigRequest as GetConfigRequestClass
from ryu.ofproto.ofproto_v1_3_parser import OFPSetConfig as SetConfigClass
from ryu.ofproto.ofproto_v1_3_parser import OFPMultipartRequest as MultipartRequestClass

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
        print '\n\nTrying to parse\n\n'
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
        print '\n\nTrying to parse config request\n\n'
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
        print '\n\nTrying to parse set config request\n\n'
        msg = super(OFPSetConfig, cls).parser(
            datapath, version, msg_type,
            msg_len, xid, buf)
        (msg.flags, msg.miss_send_len) = struct.unpack_from(
            ofproto.OFP_EXPERIMENTER_HEADER_PACK_STR, msg.buf,
            ofproto.OFP_HEADER_SIZE)
        
        return msg
    
_create_ofp_msg_ev_class(OFPSetConfig)


@_register_parser
@_set_msg_type(ofproto.OFPT_MULTIPART_REQUEST)
class OFPMultipartRequest(MultipartRequestClass):

    # setting defaults on initializers so that calling super parser
    # works correctly.
    def __init__(self,datapath=None,flags=None):
        super(OFPMultipartRequest,self).__init__(datapath,flags)
    
    @classmethod
    def parser(cls, datapath, version, msg_type, msg_len, xid, buf):
        print '\n\nTrying to parse multipart request \n\n'
        msg = super(MultipartRequestClass, cls).parser(
            datapath, version, msg_type,
            msg_len, xid, buf)
        print '\nparsed multipart request\n'
        
        (msg.type,msg.flags) = struct.unpack_from(
            ofproto.OFP_MULTIPART_REQUEST_PACK_STR,
            msg.buf,ofproto.OFP_HEADER_SIZE)
        return msg
        
_create_ofp_msg_ev_class(OFPMultipartRequest)
