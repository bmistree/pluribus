import pickle

from principals_util import Principal
from conf import pluribus_logger
from extended_v3_parser import OFPSwitchFeatures as PluribusSwitchFeatures

from ryu.ofproto import ofproto_v1_3
from ryu.ofproto.ofproto_v1_3_parser import OFPInstructionGotoTable
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
        For output actions, check that output to a valid port.  For
        physical outputs, leave action the same.  For virtual outputs,
        jump to appropriate table or cause packet in at controller.

    PART 2:
        Do translation for goto actions.
        
    '''

    # FIXME: must add and zero metadata for explicit matches on
    # virtual ports... should probably use unique virtual port ids
    # amongst principals.
    pluribus_logger.error(
        '\nFIXME: for rules that only target a virtual port, ' +
        'must add metadata during goto and replace match ' +
        'with match on metadata.  Then, in rule, zero metadata.\n')
    
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
    if early_table_flow_mod_msg is not None:
        rewrite_port_output_actions(
            chained_principal,early_table_flow_mod_msg,True)
    if late_table_flow_mod_msg is not None:
        rewrite_port_output_actions(
            chained_principal,late_table_flow_mod_msg,False)

    pluribus_logger.error('Must finish producing early and late flow tables')
    return early_table_flow_mod_msg, late_table_flow_mod_msg
        

def rewrite_port_output_actions(
    chained_principal,flow_mod_msg,is_early_table):
    '''
    @param {ChainedTablePrincipal} chained_principal
    @param {extended_v3_parser.OFPFlowMod} flow_mod_msg
    @param {boolean} is_early_table

    For any physical port that chained_principal is allowed to write
    directly to, just forward out message.

    For output actions, check that output to a valid port.  For
    physical outputs, leave action the same.  For virtual outputs,
    jump to appropriate table or cause packet in msg.
    '''
    
    goto_instr_to_add = None
    for instruction in flow_mod_msg.instructions:
        if isinstance(instruction, OFPInstructionActions):
            instruction_actions = instruction

            action_indices_to_remove = []
            for action_index in range(0,len(instruction_actions.actions)):
                action = instruction_actions.actions[action_index]

                if isinstance(action, OFPActionOutput):
                    output_port = action.port

                    if output_port not in physical_port_set:
                        if output_port not in egress_logical_port_nums_to_principals:
                            raise InvalidOutputAction()
                        else:
                            # forwarding to a logical port
                            if is_early_table:
                                # substitute action with goto to
                                # different table.
                                action_indices_to_remove.append(action_index)
                                
                                receiver_principal = (
                                    egress_logical_port_nums_to_principals[output_port])
                                
                                goto_table_id = (
                                    receiver_principal.get_first_late_table_physical_id())
                                goto_instr_to_add = OFPInstructionGotoTable(goto_table_id)
                            else:
                                # FIXME: still need to handle case
                                # where virtual port is supposed to
                                # forward out of virtual port
                                pluribus_logger.error(
                                    '\nFIXME: still must handle case of ' +
                                    'virtual port\'s forwarding out of ' +
                                    'virtual port...ends up requiring ' +
                                    'going back to controller.\n')


            # now remove all actions that had been forwarding to
            # logical ports.  Note: remove in backwards order to
            # maintain indices when deleting.
            for action_index in reverse(action_indices_to_remove):
                del instruction_actions.actions[action_index]
                
    # append goto action if necessary
    if goto_instr_to_add is not None:
        flow_mod_msg.instructions.append(goto_instr_to_add)

def duplicate_flow_mod(flow_mod_msg):
    return pickle.loads(pickle.dumps(flow_mod_msg))
