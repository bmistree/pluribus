from principals_util import Principal
from conf import pluribus_logger

from ryu.ofproto import ofproto_v1_3 as ofproto
from ryu.ofproto.ofproto_v1_3_parser import OFPInstructionActions
from ryu.ofproto.ofproto_v1_3_parser import OFPActionOutput

from extended_v3_parser import OFPSwitchFeatures as PluribusSwitchFeatures

from translation_exceptions import InvalidTableWriteException
from translation_exceptions import InvalidGotoTableException
from translation_exceptions import InvalidOutputAction


class LogicalPortPrincipal(Principal):

    def __init__(self,pluribus_switch,physical_port_set,listening_ip_addr,
                 listening_port_addr):
        '''
        @see __init__ of Principal
        '''
        super(LogicalPortPrincipal,self).__init__(
            pluribus_switch,physical_port_set,listening_ip_addr,
            listening_port_addr)
        
        # gets initialized when switch calls set_physical_table_list
        # should be a list of integers... Each integer is a table id
        # for a table that the switch can use.  Integers should be in
        # ascending order.  Virtual table ids should be indices of
        # list.
        self.physical_table_list = None
        
        self.principal_ids_to_logical_ports = {}
        # logical port linked to is *ingress* logical port to this
        # switch.
        self.ingress_logical_port_nums_to_principals = {}
        self.egress_logical_port_nums_to_principals = {}
        
        
    def add_logical_mapping(self,logical_port,partnered_principal):
        '''
        @param {PortNamePair} logical_port

        @param {Principal} partnered_principal
        '''
        partner_port = logical_port.partner
        
        self.principal_ids_to_logical_ports[partnered_principal.id] = (
            logical_port)
        self.ingress_logical_port_nums_to_principals[logical_port.port_number] = (
            partnered_principal)
        self.egress_logical_port_nums_to_principals[partner_port.port_number] = (
            partnered_principal)
        
    def get_ingress_logical_port_num_list(self):
        return list(
            self.ingress_logical_port_nums_to_principals.keys())
        
    def set_physical_table_list(self,physical_table_list):
        '''
        @param {list} physical_table_list --- Each element is an
        integer physical table id.
        '''
        self.physical_table_list = physical_table_list
        
    def get_first_physical_table(self):
        '''
        @returns {int} --- The first physical table the principal has
        control over.

        Note: must be called after set_physical_table_list
        '''
        return self.physical_table_list[0]

    #### Requests from principal to switch
    def handle_features_request(self,msg):
        '''
        @param {extended_v3_parser.OFPFeaturesRequest} msg
        '''
        pluribus_logger.debug('Responding to features request')
        num_tables = len(self.physical_table_list)

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

        Rewrites the flow mod to only apply to target tables.
        Rewrites rules not to goto incorrect tables.
        Rewrites rules to use different ports.
        '''
        # FIXME: still need to catch exceptions and write back errors.
        flow_mod_rewrite_table_ids(msg,self.physical_table_list)
        flow_mod_rewrite_gotos(msg,self.physical_table_list)
        flow_mod_rewrite_action_ports(
            msg,self.physical_port_set,
            self.egress_logical_port_nums_to_principals)

        pluribus_logger.info('Forwarding translated flow mod to switch')
        self.pluribus_switch.send_msg(msg)




def flow_mod_rewrite_table_ids(flow_mod,table_id_list):
    '''
    @param {list} table_id_list --- Each element is an integer.
    Index of table_id_list is the virtual table id; value is
    physical table id.

    A couple of notes.  For ofp delete alls, need to translate
    into many messages sending to each individual table.

    @throws {InvalidTableWriteException} --- If trying to write to
    a table that isn't a valid virtual id, then need to send an
    error back.
    '''
    if flow_mod.table_id == ofproto.OFPTT_ALL:
        # FIXME: delete messages can apply to all tables, need to
        # translate into multiple deletes.
        pluribus_logger.error(
            'Still need to re-write messages targetting all tables')
        return

    if flow_mod.table_id >= len(table_id_list):
        raise InvalidTableWriteException()

    old_table_id = flow_mod.table_id
    new_table_id = table_id_list[old_table_id]
    pluribus_logger.info(
        'For flowmod, rewriting old table %i to new table %i.' %
        (old_table_id,new_table_id))

    flow_mod.table_id = new_table_id

def flow_mod_rewrite_gotos(flow_mod,table_id_list):
    '''
    @param {list} table_id_list --- Each element is an integer.
    Index of table_id_list is the virtual table id; value is
    physical table id.

    Look through listed actions and translate gotos

    @throws {InvalidGotoTableException} --- If trying to goto a
    table that this principal does not control, then throw an
    exception.
    '''
    for instruction in flow_mod.instructions:
        if isinstance(instruction,OFPInstructionGotoTable):

            if instruction.table_id >= len(table_id_list):
                raise InvalidGotoTableException()

            old_table_id = instruction.table_id
            new_table_id = table_id_list[old_table_id]

            pluribus_logger.info(
                'For instruction, rewrite old table %i to new table %i.' %
                (old_table_id,new_table_id))
            instruction.table_id = new_table_id

def flow_mod_rewrite_action_ports(
    flow_mod,physical_port_set,egress_logical_port_nums_to_princiapls):
    '''
    @param {ImmuatableSet} physical_port_set --- The physical
    ports that this message can address.

    @param {dict} egress_logical_port_nums_to_principals --- Keys
    are logical egress port numbers of this switch.  Values are
    principals.

    @throws {InvalidOutputAction} --- If trying to forward out a
    port that are not allowed to.

    When receive a flow mod with an action, check that the action
    forwards out of a port in physical_port_set or that sends to a
    logical port in egress set.

    '''
    for instruction in flow_mod.instructions:
        if isinstance(instruction, OFPInstructionActions):
            instruction_actions = instruction
            for action in instruction_actions.actions:
                if isinstance(action, OFPActionOutput):
                    output_port = action.port

                    if output_port not in egress_logical_port_nums_to_principals:
                        if output_port not in physical_port_set:
                            raise InvalidOutputAction()

        
