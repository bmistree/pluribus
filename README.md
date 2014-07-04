Pluribus
=============

Install
------------
Set up dependencies:

    pip install ryu
    sudo apt-get install mininet 


Deploy
-------------
To start ryu:

    ryu-manager <pluribus app python file>
    
To run mininet with OpenFlow v 1.3, start mininet regularly.  For each
switch that mininet starts, create a bridge:

  sudo ovs-vsctl set bridge s1 protocols=OpenFlow13

where adds a bridge for switch 1.  (Add s2 if have two switches, etc.)
