#!/usr/bin/env python
import signal
import sys
import subprocess
import time
from cleanup import cleanup

procs_to_kill = []

def run():
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
    subprocess.Popen(
        version_cmd_vec, shell=False,stdout=output_file,
        stderr=output_file)

    time.sleep(1)

    print '\nAdding loopback ports\n'
    loopback_port_cmd= (
        'ovs-vsctl ' + 
        '-- add-port s1 patch0 ' + 
        '-- set interface patch0 type=patch options:peer=patch1 ' + 
        '-- add-port s1 patch1 ' + 
        '-- set interface patch1 type=patch options:peer=patch0')
    subprocess.Popen(loopback_port_cmd, shell=True)

    
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
    run()
