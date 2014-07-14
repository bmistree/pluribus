import sets
import json

from conf import pluribus_logger
from principal_connection import PrincipalConnection
from extended_v3_parser import OFPDescStatsReply as PluribusDescStatsReply


class Principal(object):
    STATIC_PRINCIPAL_IDENTIFIER = 0
    def __init__(self,pluribus_switch,physical_port_set,listening_ip_addr,
                 listening_port_addr):
        '''
        @param {PluribusSwitch} pluribus_switch
        
        @param {ImmutableSet} physical_port_set --- Elements are ints
        (port numbers) of ports that this principal can physically
        control.

        @param {String} listening_ip_addr --- The IP address that a
        principal is listening on.

        @param {int} listening_port_addr --- The port address that a
        principal is listening for TCP connections on.
        '''
        self.pluribus_switch = pluribus_switch
        self.physical_port_set = physical_port_set
        self.listening_ip_addr = listening_ip_addr
        self.listening_port_addr = listening_port_addr

        self.id = Principal.STATIC_PRINCIPAL_IDENTIFIER
        Principal.STATIC_PRINCIPAL_IDENTIFIER += 1

        pluribus_logger.debug(
            ('Loaded principal with ports %(ports)s; ip addr ' +
            '%(listening_ip_addr)s and ports %(listening_port)i.') %
            {
                'ports': str(self.physical_port_set),
                'listening_ip_addr': str(self.listening_ip_addr),
                'listening_port': self.listening_port_addr
             })
        
        self.num_buffers = None
        

    def set_num_buffers(self, num_buffers):
        '''
        @param {int} num_buffers --- Number of buffers this principal
        can use.
        '''
        self.num_buffers = num_buffers
                
    def connect(self):
        '''
        Create connection with principal.
        '''
        pluribus_logger.info(
            'Connecting to principal at %s:%i' %
            (self.listening_ip_addr,self.listening_port_addr))
        
        self.connection = PrincipalConnection(
            self.listening_ip_addr,self.listening_port_addr,self)
        
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
    
    #### Requests from principal to switch
    def handle_features_request(self,msg):
        '''
        @param {extended_v3_parser.OFPFeaturesRequest} msg
        '''
        # should be overridden
        assert False

    def handle_desc_stats_request(self,msg):
        '''
        @param {OFPDescStatsRequest} msg

        Sends back an OFPDescStatsReply
        '''
        msg = PluribusDescStatsReply(
            msg.xid,self.connection.datapath)
        msg.serialize()
        self.connection.datapath.send_msg(msg)

    def handle_flow_mod(self,msg):
        '''
        @param {extended_v3_parser.OFPFlowMod} msg

        Rewrites the flow mod to only apply to target tables.
        Rewrites rules not to goto incorrect tables.
        Rewrites rules to use different ports.
        '''
        # should be overridden
        assert False
        
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
    

def load_principals_from_json_file(cls,filename,pluribus_switch):
    '''
    @param {string} filename
    @param {PluribusSwitch} pluribus_switch
    
    @return {list} --- Each element is a principal
    '''
    with open(filename,'r') as fd:
        file_contents = fd.read()
    json_list = json.loads(file_contents)

    return map(
        lambda json_dict:
            principal_from_json_dict(cls,json_dict,pluribus_switch),
        json_list)
    
        
def principal_from_json(cls,json_str,pluribus_switch):
    '''
    @param {String} json_str

    @returns {Principal}
    '''
    principal_dict = json.loads(json_str)
    return principal_from_json_dict(cls,principal_dict,pluribus_switch)

def principal_from_json_dict(cls,json_dict,pluribus_switch):
    '''
    @param {dict} json_dict --- @see Principal.to_json_str for format
    of dict.

    @param {PluribusSwitch} pluribus_switch 
    
    @returns {Principal}
    '''
    return cls(
        pluribus_switch,
        sets.ImmutableSet(json_dict['physical_ports']),
        json_dict['listening_ip_addr'],
        int(json_dict['listening_port_addr']))
