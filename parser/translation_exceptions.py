
class InvalidTableWriteException (Exception):
    '''
    Flowmod was supposed to be inserted into a table that is invalid
    for this principal.
    '''


class InvalidGotoTableException (Exception):
    '''
    Flowmod instruction tries to goto an invalid table.
    '''

class InvalidOutputAction (Exception):
    '''
    Flowmod instruction tries to write out of an incorrect port.
    '''

#### Exceptions unique to chained table approach
class InvalidPacketInPortMatch(Exception):
    '''
    Flowmod instruction tries to match to an invalid port.
    '''
