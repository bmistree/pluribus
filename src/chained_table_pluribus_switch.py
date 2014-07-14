import math
import itertools

from ryu.ofproto.ofproto_v1_3_parser import OFPInstructionGotoTable

from chained_table_principal import ChainedTablePrincipal

from port_util import set_logical_physical
from port_util import num_principals_from_num_logical_port_pairs
from pluribus_switch import PluribusSwitch, SwitchState
from conf import pluribus_logger,HEAD_TABLE_ID


class ChainedTablePluribusSwitch(PluribusSwitch):
    
    def __init__(self, *args, **kwargs):
        super(ChainedTablePluribusSwitch, self).__init__(
            ChainedTablePrincipal,*args, **kwargs)
    
        
    def _transition_from_uninitialized(self):
        '''
        When receive port stats, can start allocating virtual ports to
        principals and installing head table.  This method does that.

        Does four things:
          0) Transition into INSTALLING_HEAD_TABLES state
          1) Assigns each principal a set of early and late tables
          2) Tell each principal about virtual port numbers to send to
          other principals.
          3) Sets a head table that gotos the principal's
             first table.
        '''
        #### PART 0
        self.state = SwitchState.INSTALLING_HEAD_TABLES
        

        #### PART 1
        
        # check to ensure that have enough tables to support number of
        # principals.
        num_principals = len(self.principals)
        # +1 is for head table.  *2 is for early and late tables.
        necessary_num_tables = num_principals*2 + 1 

        if necessary_num_tables > self.switch_num_tables:
            pluribus_logger.error(
                ('Insufficient number of tables (%i) to support ' +
                 '%i principals') % (self.switch_num_tables,num_principals))
            assert False

        # FIXME: Check for off-by-one error
        available_tables = self.switch_num_tables -1
        # FIXME: by default using same number of early and late tables.
        num_early_tables =  int(math.floor(available_tables/2))
        early_tables_per_principal = int(math.floor(
            num_early_tables/num_principals))
        late_tables_per_principal = early_tables_per_principal

        # start at 1 to avoid head table
        assigning_early_table_index = 1
        for principal in self.principals:
            early_tables = range(
                assigning_early_table_index,early_tables_per_principal)

            late_table_index = assigning_early_table_index + num_early_tables
            late_tables = range(late_table_index,
                                late_table_index + late_tables_per_principal)
            
            # update next index to assign frmo
            assigning_early_table_index += num_early_tables

            # update tables for principals
            principal.add_table_ids(early_tables, late_tables)

        #### PART 2

        # find highest physical port number and add one to get first
        # virtual port number
        highest_port_number = -1
        for port_name_number in self.port_name_number_list:
            if port_name_number.port_number > highest_port_number:
                highest_port_number = port_name_number.port_number
        first_available_virtual_port_number = highest_port_number + 1
        
        # add all egress logical port numbers for each principal
        for principal in self.principals:
            principal.add_egress_logical_port_num_to_table_id(
                self.principals,first_available_virtual_port_number)

        #### PART 3: Set head table for each principal
        for principal in self.principals:
            self._send_head_table_flow_mod(principal)

        # ensure that all head table rules are installed
        self.send_barrier()


        
    def _send_head_table_flow_mod(self,principal):
        '''
        @param {ChainedTablesPrincipal} principal
        
        Sends a flow mod request to head table to install rules for
        principal.
        '''
        principal_first_physical_table = (
            principal.get_first_early_table_physical_id())
        
        for port_num in principal.physical_port_set:

            match = self.switch_dp.ofproto_parser.OFPMatch(
                in_port=port_num)
            instructions = [
                OFPInstructionGotoTable(principal_first_physical_table)]
            # priority is irrelevant because have disjoint matches
            priority = 10
            self.add_flow_mod(match,instructions,priority,HEAD_TABLE_ID)

        # note: do not send barrier here.  rely on caller to send
        # barrier.
