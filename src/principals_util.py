import sets
import json

from conf import pluribus_logger


class Principal(object):
    STATIC_PRINCIPAL_IDENTIFIER = 0
    def __init__(self,physical_port_set,listening_ip_addr,
                 listening_port_addr):
        '''
        @param {ImmutableSet} --- Elements are ints (port numbers) of
        ports that this principal can physically control.
        '''
        self.physical_port_set = physical_port_set
        self.listening_ip_addr = listening_ip_addr
        self.listening_port_addr = listening_port_addr

        # gets initialized when switch calls set_physical_table_list
        # should be a list of integers... Each integer is a table id
        # for a table that the switch can use.  Integers should be in
        # ascending order.  Virtual table ids should be indices of
        # list.
        self.physical_table_list = None

        # logical port linked to is *ingress* logical port to this
        # switch.
        self.principal_ids_to_logical_ports = {}
        self.logical_port_nums_to_principals = {}
        
        self.id = Principal.STATIC_PRINCIPAL_IDENTIFIER
        Principal.STATIC_PRINCIPAL_IDENTIFIER += 1

        pluribus_logger.debug(
            ('Loaed principal with ports %(ports)s; ip addr ' +
            '%(listening_ip_addr)s and ports %(listening_port)i.') %
            {
                'ports': str(self.physical_port_set),
                'listening_ip_addr': str(self.listening_ip_addr),
                'listening_port': self.listening_port_addr
             })

    def connect(self):
        '''
        Create connection with principal.
        '''
        pluribus_logger.error(
            'FIXME: must finish connect method to principals')
        
    def add_logical_mapping(self,logical_port,partnered_principal):
        '''
        @param {PortNamePair} logical_port

        @param {Principal} partnered_principal
        '''
        self.principal_ids_to_logical_ports[partnered_principal.id] = (
            logical_port)
        self.logical_port_nums_to_principals[logical_port.port_number] = (
            partnered_principal)

    def get_ingress_logical_port_num_list(self):
        return list(self.logical_port_nums_to_principals.keys())
        
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
        
    def to_json_str(self):
        '''
        @returns {string} --- A serialized representation of this
        principal.  Note: ignores principal id, which is only used
        internally.
        '''
        to_serialize = {
            'physical_ports': list(self.physical_port_set),
            'listening_ip_addr': self.listening_ip_addr,
            'listening_port_addr': self.listening_port_addr
            }
        return json.dumps(to_serialize,indent=4)

def save_principals_to_json_file(principal_list,filename):
    '''
    @param {list} principal_list --- Each element is a principal
    '''
    principal_jsons = map(
        lambda principal: principal.to_json_str,
        principal_list)
    output_str = '[' + (',\n'.join(principal_jsons)) + ']'
    
    with open(filename,'w') as fd:
        fd.write(output_str)
    

def load_principals_from_json_file(filename):
    '''
    @return {list} --- Each element is a principal
    '''
    with open(filename,'r') as fd:
        file_contents = fd.read()
    json_list = json.loads(file_contents)

    return map(
        lambda json_dict: principal_from_json_dict(json_dict),
        json_list)
    
        
def principal_from_json(json_str):
    '''
    @param {String} json_str

    @returns {Principal}
    '''
    principal_dict = json.loads(json_str)
    return principal_from_json_dict(principal_dict)

def principal_from_json_dict(json_dict):
    '''
    @param {dict} json_dict --- @see Principal.to_json_str for format
    of dict.

    @returns {Principal}
    '''
    return Principal(
        sets.ImmutableSet(json_dict['physical_ports']),
        json_dict['listening_ip_addr'],
        int(json_dict['listening_port_addr']))
