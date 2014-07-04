#!/usr/bin/env python
import signal
import sys
import subprocess
import time

procs_to_kill = []

def run():
    signal.signal(signal.SIGINT, signal_handler)
    
    print '\nStarting mininet\n'
    mn_cmd_vec = ['mn','--controller=remote']
    procs_to_kill.append(subprocess.Popen(mn_cmd_vec, shell=False))
    
    time.sleep(3)
    
    print '\nTransitioning to OpenFlow v 1.3\n'
    version_cmd_vec = ['ovs-vsctl','set','bridge','s1','protocols=OpenFlow13']
    subprocess.Popen(version_cmd_vec, shell=False)

    while True:
        time.sleep(1)


def signal_handler(signal, frame):
    print '\n\nClosing\n\n'
    for proc in procs_to_kill:
        proc.kill()
    time.sleep(1)
    sys.exit(0)
    
    
if __name__ == '__main__':
    run()
