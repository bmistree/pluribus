import math

def set_logical_physical(port_name_number_list):
    '''
    @param {list} port_name_list --- Each element is a PortNameNumber
    object.

    For each element in list, sets whether the port is logical or
    physical.

    @returns {list} --- Each element is a PortNameNumber for a logical
    port.  This logical port's partner does not also appear in the
    list.  (Basic idea is that iterating through the list allows you
    to quickly get a unique logical port pair.
    '''
    to_return = []
    
    # first, identify all physical ports
    for port_name_number in port_name_number_list:
        if not is_loopback_port(port_name_number.port_name):
            port_name_number.set_physical()
    
    # Next, pair logical ports. Basic algorithm: principals are listed
    # in incremental order from 0.  Ie., princiapl 0, 1, 2, ...  As
    # soon as missing next highest principal id number, know that
    # we're out of principals and return.
    port_pair_num = 0
    while True:
        port_a_name = produce_loopback_port_a(port_pair_num)
        port_b_name = produce_loopback_port_b(port_pair_num)
        port_pair_num += 1 # go on to next principal number
        
        port_name_number_a = None
        port_name_number_b = None
        
        for port_name_number in port_name_number_list:
            if port_name_number.port_name == port_a_name:
                port_name_number_a = port_name_number
            if port_name_number.port_name == port_b_name:
                port_name_number_b = port_name_number

        # no more principals to match
        if (port_name_number_a is None) and (port_name_number_b is None):
            return to_return

        # check for unmatched logical port
        if (port_name_number_a is None) or (port_name_number_b is None):
            assert False

        port_name_number_a.set_logical(port_name_number_b)
        port_name_number_b.set_logical(port_name_number_a)
        to_return.append(port_name_number_a)


def num_logical_port_pairs_from_num_principals(num_principals):
    '''
    Every principal has a logical port connecting to every other
    principal.  Ie., we should have a pair of logical ports for each
    pair of principals.  Using n choose k (ie., num_principals choose
    2), gives formula at bottom.
    '''
    return num_principals*(num_principals-1) / 2        
            
def num_principals_from_num_logical_port_pairs(num_logical_port_pairs):
    '''
    Using quadratic formula to perform inverse of
    num_logical_port_pairs_from_num_principals.
    '''
    return (1 + math.sqrt(1 + 8 * num_logical_port_pairs)) / 2


class PortNameNumber(object):
    
    def __init__(self,port_name,port_number):
        self.port_name = port_name
        self.port_number = port_number
        self.is_physical = None
        # only set for logical ports.  will contain PortNameNumber
        # object
        self.partner = None
        
    def set_physical(self):
        self.is_physical = True
        
    def set_logical(self,partner_port_name_number):
        '''
        @param {PortNameNumber} partner_port_name_number --- Each
        logical port has a matching partner (one for ingress between
        each pair of principals).  partner_port_name_number is the
        partner logical port for this object.
        '''
        self.is_physical = False
        self.partner = partner_port_name_number
        
    def is_physical_has_been_set(self):
        return self.is_physical is not None
    
    
    
# loopback ports have the format:
#   LOOPBACK_PORT_NAME_PREFIX_<int>_0
#   LOOPBACK_PORT_NAME_PREFIX_<int>_1
#
# Where int goes from 0 to the number of logical port pairs in the
# system.
LOOPBACK_PORT_NAME_PREFIX = 'loopback_port_'

def produce_loopback_port_a(port_pair_number):
    '''
    @param {int} port_pair_number ---- See comment above
    LOOPBACK_PORT_NAME_PREFIX
    '''
    return LOOPBACK_PORT_NAME_PREFIX + str(port_pair_number) + '_a'

def produce_loopback_port_b(port_pair_number):
    '''
    @param {int} port_pair_number ---- See comment above
    LOOPBACK_PORT_NAME_PREFIX
    '''
    return LOOPBACK_PORT_NAME_PREFIX + str(port_pair_number) + '_b'

def is_loopback_port(port_name):
    if LOOPBACK_PORT_NAME_PREFIX in port_name:
        return True
    return False
