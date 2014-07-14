import math
import itertools

from ryu.ofproto.ofproto_v1_3_parser import OFPInstructionGotoTable

from logical_port_principal import LogicalPortPrincipal
from port_util import set_logical_physical
from port_util import num_principals_from_num_logical_port_pairs
from pluribus_switch import PluribusSwitch, SwitchState
from conf import pluribus_logger,HEAD_TABLE_ID


class LogicalPortPluribusSwitch(PluribusSwitch):
    
    def __init__(self, *args, **kwargs):
        super(LogicalPortPluribusSwitch, self).__init__(
            LogicalPortPrincipal,*args, **kwargs)
        self.logical_port_pair_halves = None
        self.num_principals_can_support = None
    
    def _init_recv_port_stats_response_config(self,ev):
        '''
        As part of initialization, determine which ports are logical
        and which ports are physical.
        '''
        # call parent class
        super(LogicalPortPluribusSwitch,
              self)._init_recv_port_stats_response_config(ev)
        self.logical_port_pair_halves = (
            set_logical_physical(self.port_name_number_list))

        num_logical_port_pairs = len(self.logical_port_pair_halves)
        self.num_principals_can_support = (
            num_principals_from_num_logical_port_pairs(num_logical_port_pairs))

        if self.num_principals_can_support < len(self.principals):
            pluribus_logger.error (
                '\nError: not enough logical ports.  ' +
                ('Can only support %i principals, not %i.' %
                 (self.num_principals_can_support, len(self.principals))))
            assert False
        
        self._debug_print_ports()
        
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
        pluribus_logger.info(
            'Transitioning from uninitialized ' +
            '(allocating logical ports and installing head table)')

        
        #### PART 0: State transition
        #### DEBUG
        if self.state != SwitchState.UNINITIALIZED:
            pluribus_logger.error(
                'Unexpected state transition from uninitialized')
            assert False
        #### END DEBUG
        
        self.state = SwitchState.INSTALLING_HEAD_TABLES
        

        #### PART 1: Generating physical table mappings
        
        # FIXME: currently allocating an equal number of tables
        # between all principals.  No fundamental reason not to
        # support unequal allocations.
        
        # subtracting 1 from numerator to account for head table.
        num_tables_per_principal = int(math.floor(
            (self.switch_num_tables -1) / len(self.principals)))

        for i in range(0, len(self.principals)):
            principal = self.principals[i]
            beginning_table_id = 1 + i*num_tables_per_principal
            ending_table_id = 1 + (i+1)*num_tables_per_principal
            
            principal.set_physical_table_list(
                range(beginning_table_id,ending_table_id))
            
            # FIXME: set real number of buffers on principal
            pluribus_logger.error(
                'FIXME: Assigning hardcoded number of ' +
                'buffers between switches')
            principal.set_num_buffers(5)

            
        #### PART 2: Assign logical ports
        logical_port_index = 0
        for i in range(0, len(self.principals)):
            principal_a = self.principals[i]
            for j in range(i+1,len(self.principals)):
                principal_b = self.principals[j]
                
                logical_port_a = (
                    self.logical_port_pair_halves[logical_port_index])
                logical_port_b = logical_port_a.get_partner()
                logical_port_index += 1

                principal_a.add_logical_mapping(logical_port_a,principal_b)
                principal_b.add_logical_mapping(logical_port_b,principal_a)


        #### PART 3: Set head table for each principal
        for principal in self.principals:
            self._send_head_table_flow_mod(principal)

        # ensure that all head table rules are installed
        self.send_barrier()

        
    def _send_head_table_flow_mod(self,principal):
        '''
        @param {Principal} principal
        
        Sends a flow mod request to head table to install rules for
        principal.
        '''
        ingress_logical_port_num_list = (
            principal.get_ingress_logical_port_num_list())
        physical_port_num_list = list(principal.physical_port_set)

        principal_first_physical_table = principal.get_first_physical_table()
        
        for port_num in itertools.chain(ingress_logical_port_num_list,
                                        physical_port_num_list):

            match = self.switch_dp.ofproto_parser.OFPMatch(
                in_port=port_num)
            instructions = [
                OFPInstructionGotoTable(principal_first_physical_table)]
            # priority is irrelevant because have disjoint matches
            priority = 10
            self.add_flow_mod(match,instructions,priority,HEAD_TABLE_ID)

        # note: do not send barrier here.  rely on caller to send
        # barrier.

            
    #### UTILITY CODE
    
    def _debug_print_ports(self):
        '''
        Helper method to ensure that got expected number of ports, etc.
        '''
        port_log_msg = (
            ('Total num ports: %i.  ' %
             len(self.port_name_number_list)) +
            ('Num logical port pairs: %i.  ' %
             len(self.logical_port_pair_halves)) +
            ('Num principals can support: %i.' %
             self.num_principals_can_support))
        pluribus_logger.info(port_log_msg)
            
