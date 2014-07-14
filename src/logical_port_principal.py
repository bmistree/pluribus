from principals_util import Principal
from conf import pluribus_logger

from extended_v3_parser import OFPSwitchFeatures as PluribusSwitchFeatures

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
        self.egress_logical_port_nums_to_principals[parnter_port.port_number] = (
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
        msg.rewrite_table_ids(self.physical_table_list)
        msg.rewrite_gotos(self.physical_table_list)
        msg.rewrite_action_ports(
            self.physical_port_set,
            self.egress_logical_port_nums_to_principals)

        pluribus_logger.info('Forwarding translated flow mod to switch')
        self.pluribus_switch.send_msg(msg)

