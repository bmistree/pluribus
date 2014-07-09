#!/usr/bin/env python
import signal
import sys
import os
import subprocess
import time
from cleanup import cleanup
import argparse

sys.path.append(
    os.path.join(
        os.path.dirname(os.path.abspath(__file__)),'..','src'))

from port_util import produce_loopback_port_a
from port_util import produce_loopback_port_b
from port_util import num_logical_port_pairs_from_num_principals

procs_to_kill = []

def start_switch(num_principals):
    '''
    @param {int} num_principals --- The number of principals that
    should share the switch we're starting.
    '''
    signal.signal(signal.SIGINT, signal_handler)
    output_file = open('/dev/null','w')
    
    print '\nStarting mininet\n'
    mn_cmd_vec = ['mn','--controller=remote','--switch', 'ovsk,protocols=OpenFlow13']
    procs_to_kill.append(
        subprocess.Popen(
            mn_cmd_vec, shell=False,
            stdout=output_file,stderr=output_file))

    time.sleep(3)
    
    print '\nTransitioning to OpenFlow v 1.3\n'
    version_cmd_vec = ['ovs-vsctl','set','bridge','s1','protocols=OpenFlow13']
    version_proc = subprocess.Popen(
        version_cmd_vec, shell=False,stdout=output_file,
        stderr=output_file)
    version_proc.wait()

    # Every principal has a logical port connecting to every other
    # principal.
    num_logical_port_pairs = num_logical_port_pairs_from_num_principals(
        num_principals)
    
    print '\nAdding ' + str(num_logical_port_pairs) + ' loopback port pairs\n'

    for i in range(0,num_logical_port_pairs):
        format_str_dict = {
            'port_a_name': produce_loopback_port_a(i),
            'port_b_name': produce_loopback_port_b(i)
            }
        
        loopback_port_cmd= (
            'ovs-vsctl ' + 
            '-- add-port s1 %(port_a_name)s ' + 
            '-- set interface %(port_a_name)s type=patch options:peer=%(port_b_name)s ' + 
            '-- add-port s1 %(port_b_name)s ' + 
            '-- set interface %(port_b_name)s type=patch options:peer=%(port_a_name)s')
        
        loopback_port_cmd = loopback_port_cmd % format_str_dict
        p = subprocess.Popen(loopback_port_cmd, shell=True)
        p.wait()

    print '\nSwitch ready and configured\n'
        
    while True:
        time.sleep(1)


def signal_handler(signal, frame):
    print '\n\nClosing\n\n'
    for proc in procs_to_kill:
        proc.kill()

    cleanup()
    time.sleep(1)
    sys.exit(0)
    
    
if __name__ == '__main__':

    description = 'Run this to start a single switch'
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        '-p','--num_principals',help='Number of principals to share switch between',
        default=2)
    # actually run parser and collect user-passed arguments
    args = parser.parse_args()
    start_switch(int(args.num_principals))
