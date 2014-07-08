#!/usr/bin/env python

import subprocess

def cleanup():
    cmd_vec = ['ovs-vsctl','del-br','s1']
    p = subprocess.Popen(cmd_vec,shell=False)
    p.wait()

if __name__ == '__main__':
    cleanup()
