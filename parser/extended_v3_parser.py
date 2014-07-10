from ryu.ofproto import ofproto_v1_3 as ofproto
from ryu.ofproto.ofproto_v1_3_parser import _register_parser
from ryu.ofproto.ofproto_v1_3_parser import _set_msg_type
from ryu.ofproto.ofproto_parser import StringifyMixin, MsgBase, msg_pack_into, msg_str_attr


@_register_parser
@_set_msg_type(ofproto.OFPT_FEATURES_REQUEST)
class OFPFeaturesRequest(MsgBase):
    '''
    
    '''
    def __init__(self, datapath, elements=[]):
        super(OFPFeaturesRequest, self).__init__(datapath)
        self.elements = elements
        print '\n\nInstantiated features request parser\n\n'

    @classmethod
    def parser(cls, datapath, version, msg_type, msg_len, xid, buf):
        print '\n\nParsing message in extended features request\n\n'
        msg = super(OFPFeaturesRequest, cls).parser(
            datapath, version, msg_type,
            msg_len, xid, buf)

