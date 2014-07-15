#!/usr/bin/env python

import sys
import signal
import subprocess
import time

all_procs = []

def run(jar_name, ip_addr, port_number,num_clients):
    global all_procs
    signal.signal(signal.SIGINT, signal_handler)
    
    cmd_vec = ['java','-jar',jar_name,ip_addr, port_number]
    for i in range(0,num_clients):
        all_procs.append(subprocess.Popen(cmd_vec,shell=False))
            
    while True:
        time.sleep(1)

def signal_handler(signal, frame):
    print '\n\nClosing\n\n'
    for proc in all_procs:
        proc.kill()

    time.sleep(1)
    sys.exit(0)
    
        
if __name__ == '__main__':
    jar_name = sys.argv[1]
    ip_addr = sys.argv[2]
    port_number = sys.argv[3]
    num_clients = sys.argv[4]
    run(jar_name, ip_addr, port_number, num_clients)
