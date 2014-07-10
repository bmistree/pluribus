import json

CONF_FILENAME = 'pluribus.conf'


# wait this many seconds after receiving a switch before sending a
# request about port statistics.  Allows openvswitch time to add
# logical ports.
PORT_STATS_DELAY_TIME = 10
CONF_PORT_STATS_DELAY_TIME = 'PORT_STATS_DELAY_TIME'

# None means that we should just use default principals
JSON_PRINCIPALS_TO_LOAD_FILENAME = None
CONF_JSON_PRINCIPALS_TO_LOAD_FILENAME = 'JSON_PRINCIPALS_TO_LOAD_FILENAME'


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

load_conf()
