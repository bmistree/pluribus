import pickle

from principals_util import Principal
from conf import pluribus_logger
from extended_v3_parser import OFPSwitchFeatures as PluribusSwitchFeatures

from ryu.ofproto import ofproto_v1_3
from translation_exceptions import InvalidTableWriteException
from translation_exceptions import InvalidGotoTableException
from translation_exceptions import InvalidOutputAction
from translation_exceptions import InvalidPacketInPortMatch

class ChainedTablePrincipal(Principal):

    def __init__(self,pluribus_switch,physical_port_set,listening_ip_addr,
                 listening_port_addr):
        '''
        @see __init__ of Principal
        '''
        super(ChainedTablePrincipal,self).__init__(
            pluribus_switch,physical_port_set,listening_ip_addr,
            listening_port_addr)
        
        # gets initialized when switch calls set_physical_table_list
        # should be a list of integers... Each integer is a table id
        # for a table that the switch can use.  Integers should be in
        # ascending order.  Virtual table ids should be indices of
        # list.
        self.physical_table_list = None

        # When initialized, each is a list.  Indices are virtual table
        # ids.  Values are physical table ids.
        self.early_table_ids = None
        self.late_table_ids = None

        self.egress_logical_port_num_to_table_id = {}
        

    def add_table_ids(self,early_table_ids, late_table_ids):
        self.early_table_ids = early_table_ids
        self.late_table_ids = late_table_ids

    def add_egress_logical_port_num_to_table_id(
        self,principals_list,virtual_port_start_id):
        '''
        @param {list} principals_list --- Each element is a
        ChainedTablePrincipal object.

        @param {int} virtual_port_start_id --- Assign a virtual port
        for each port between principals.  Start with this index.
        '''        
        for principal in principals_list:
            # don't create a loopback port to myself.
            if principal.id == self.id:
                continue

            first_late_tbl_phys_id = (
                principal.get_first_late_table_physical_id())
            self.egress_logical_port_num_to_table_id[
                virtual_port_start_id] = first_late_tbl_phys_id
            virtual_port_start_id += 1
            
    def get_first_late_table_physical_id(self):
        return self.late_table_ids[0]
    
    def get_first_early_table_physical_id(self):
        return self.early_table_ids[0]

    
    #### Requests from principal to switch
    def handle_features_request(self,msg):
        '''
        @param {extended_v3_parser.OFPFeaturesRequest} msg
        '''
        pluribus_logger.debug('Responding to features request')
        num_tables = len(self.early_table_ids)

        # FIXME: hardcoding features and capabilities for now
        capabilities = 71
        auxiliary_id = 0
        
        switch_features_msg = PluribusSwitchFeatures(
            self.connection.datapath,
            self.connection.datapath.id,
            self.num_buffers,
            num_tables,
            auxiliary_id,
            capabilities)
        
        self.connection.datapath.send_msg(
            switch_features_msg)

        
    def handle_flow_mod(self,msg):
        '''
        @param {extended_v3_parser.OFPFlowMod} msg

        '''
        # FIXME: must handle flow mod request for chained tables
        pluribus_logger.error(
            'FIXME: still handling flow mod request for chained tables')

        # FIXME: catch potential exceptions from generating packets
        # and return appropriate error codes.
        early_table_flow_mod_msg,late_table_flow_mod_msg = (
            produce_early_late_flow_mods(self,msg))

        if early_table_flow_mod_msg is not None:
            self.pluribus_switch.send_msg(early_table_flow_mod_msg)
        if late_table_flow_mod_msg is not None:
            self.pluribus_switch.send_msg(late_table_flow_mod_msg)
        
        

def produce_early_late_flow_mods(chained_principal,msg):
    '''
    @param {ChainedTablePrincipal} chained_principal
    @param {extended_v3_parser.OFPFlowMod} msg

    @returns {2-tuple} (a,b):

       a {extended_v3_parser.OFPFlowMod or None}: Flow mod for early
       table.
       
       b {extended_v3_parser.OFPFlowMod or None}: Flow mod for late
       table.

    PART 0:
        First check if we need to duplicate message --- one for
        early tables and one for late tables.  We will need to
        duplicate if:
            * Match does not include a physical port
            * Match does not include a logical port

    PART 1:
        More to do
    '''
    early_table_flow_mod_msg = None
    late_table_flow_mod_msg = None


    #### PART 0:
    match_in_port = msg.match.get('in_port')

    if (match_in_port is None) or (match_in_port == ofproto_v1_3.OFPP_ANY):
        # means installing an entry that does not match on a
        # particular port.  Install in both early and late.
        early_table_flow_mod_msg = msg
        late_table_flow_mod_msg = duplicate_flow_mod(msg)
    elif match_in_port in chained_principal.physical_port_set:
        # means that we only need to install rule in early table
        early_table_flow_mod_msg = msg
    elif match_in_port in chained_principal.egress_logical_port_num_to_table_id:
        # means that we only need to install rule in late table
        late_table_flow_mod_msg = msg
        # Overwrite to not match on any ingress port.
        
        # FIXME: super-ugly way to remove in_port
        match = late_table_flow_mod_msg.match
        for field_tuple_index in range(0,len(match._fields2)):
            field_tuple = match._fields2[field_tuple_index]
            if field_tuple[0] == 'in_port':
                match._fields2[field_tuple_index] = ('in_port',ofproto_v1_3.OFPP_ANY)
                break

        # NOTE: the below doesn't work.  I assume that the library
        # assumes that we won't double-add in-ports.
        # late_table_flow_mod_msg.match.set_in_port(ofproto_v1_3.OFPP_ANY)
    else:
        raise InvalidPacketInPortMatch()


    #### PART 1:
    pluribus_logger.error('Must finish producing early and late flow tables')
    
    return early_table_flow_mod_msg, late_table_flow_mod_msg
        

def duplicate_flow_mod(flow_mod_msg):
    return pickle.loads(pickle.dumps(flow_mod_msg))
