from ryu.ofproto import ofproto_v1_3 as ofproto
from ryu.ofproto.ofproto_v1_3_parser import _register_parser
from ryu.ofproto.ofproto_v1_3_parser import _set_msg_type
from ryu.ofproto.ofproto_parser import StringifyMixin, MsgBase, msg_pack_into, msg_str_attr
from ryu.controller.ofp_event import _create_ofp_msg_ev_class

from ryu.ofproto.ofproto_v1_3_parser import OFPFeaturesRequest as FeaturesRequestClass
from ryu.ofproto.ofproto_v1_3_parser import OFPSwitchFeatures as FeaturesReplyClass


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



@_register_parser
@_set_msg_type(ofproto.OFPT_FEATURES_REPLY)
class OFPSwitchFeatures(FeaturesReplyClass):
    '''    
    Default switch features essentially has a blank serialize method.
    This is because ryu does not actually generate this message
    itself.  Adding these methods so that when serialize, it works
    correctly.
    
    '''
    def serialize(self):
        print '\n\nMust override seriaize for OFPSwitchFeatures\n\n'
        # buf = bytearray()
        # msg_pack_into(ofproto.OFP_EXPERIMENTER_MULTIPART_HEADER_PACK_STR,
        #               buf, 0,
        #               self.experimenter, self.exp_type)
        # return buf + self.data
        return None


