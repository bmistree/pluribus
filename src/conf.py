import json
import logging
import sys
import os

sys.path.append(
    os.path.join(
        os.path.dirname( os.path.abspath(__file__)),
        '..','parser'))
import extended_v3_parser



CONF_FILENAME = 'pluribus.conf'
HEAD_TABLE_ID = 0

pluribus_logger = logging.getLogger('pluribus')
formatter = logging.Formatter('PLURIBUS: %(levelname)-8s  %(message)s')
handler = logging.StreamHandler()
handler.setFormatter(formatter)
pluribus_logger.addHandler(handler)
pluribus_logger.propagate = False


# wait this many seconds after receiving a switch before sending a
# request about port statistics.  Allows openvswitch time to add
# logical ports.
PORT_STATS_DELAY_TIME = 10
CONF_PORT_STATS_DELAY_TIME = 'PORT_STATS_DELAY_TIME'

# None means that we should just use default principals
JSON_PRINCIPALS_TO_LOAD_FILENAME = None
CONF_JSON_PRINCIPALS_TO_LOAD_FILENAME = 'JSON_PRINCIPALS_TO_LOAD_FILENAME'


LOGGING_LEVEL = 'warn'
CONF_LOGGING_LEVEL = 'LOGGING_LEVEL'


def load_conf():
    conf_param_dict = {}
    try:
        with open(CONF_FILENAME,'r') as fd:
            conf_contents = fd.read()
            conf_param_dict = json.loads(conf_contents)
    except:
        pass

    if CONF_PORT_STATS_DELAY_TIME in conf_param_dict:
        global PORT_STATS_DELAY_TIME
        PORT_STATS_DELAY_TIME = int(
            conf_param_dict[CONF_PORT_STATS_DELAY_TIME])

    if CONF_JSON_PRINCIPALS_TO_LOAD_FILENAME in conf_param_dict:
        global JSON_PRINCIPALS_TO_LOAD_FILENAME
        JSON_PRINCIPALS_TO_LOAD_FILENAME = (
            conf_param_dict[CONF_JSON_PRINCIPALS_TO_LOAD_FILENAME])

    global LOGGING_LEVEL        
    if CONF_LOGGING_LEVEL in conf_param_dict:
        LOGGING_LEVEL = conf_param_dict[CONF_LOGGING_LEVEL]

    pluribus_logger.setLevel(LOGGING_LEVEL)

        

load_conf()
