import sets
import json

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

        self.id = Principal.STATIC_PRINCIPAL_IDENTIFIER
        Principal.STATIC_PRINCIPAL_IDENTIFIER += 1
        
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
    with open(fileame,'r') as fd:
        file_contents = fd.read()
    json_list = json.dumps(file_contents)

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
        json_dict['listening_port_addr'])
