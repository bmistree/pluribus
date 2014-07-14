from principals_util import Principal
from conf import pluribus_logger

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
        # FIXME: must handle feature request for chained tables
        pluribus_logger.error(
            'FIXME: must handle feature request for chained tables')

    def handle_desc_stats_request(self,msg):
        '''
        @param {OFPDescStatsRequest} msg

        Sends back an OFPDescStatsReply
        '''
        # FIXME: must handle desc stats request for chained tables
        pluribus_logger.error(
            'FIXME: must handle desc stats request for chained tables')


    def handle_flow_mod(self,msg):
        '''
        @param {extended_v3_parser.OFPFlowMod} msg
        '''
        # FIXME: must handle flow mod request for chained tables
        pluribus_logger.error(
            'FIXME: must handle flow mod request for chained tables')
        

