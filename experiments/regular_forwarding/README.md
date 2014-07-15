Start regular_ryu.py controller:

    ryu-manager regular_ryu.py

Start mininet with a remote controller:

    sudo mn --controller=remote

Add bridge from OpenFlow 1.0 to OpenFlow 1.3.

    sudo ovs-vsctl set bridge s1 protocols=OpenFlow13

Wait ~20 seconds for everything to be set up.  In mininet, open two
terminals, one in each host:

    mininet> h1 xterm &
    mininet> h2 xterm &

Start server in h1's xterm:

    java -jar <directory with server.jar in it>/server.jar

Start the client in h2's xterm, using saturating client

    python saturating_client.py
      <directory with client.jar in it>/client.jar 
      10.0.0.1 // this is h1's ip addr
      35610    // this is the port that server is listening on
      4        // num clients
