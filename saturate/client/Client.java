package client;

import java.io.IOException;
import java.net.DatagramSocket;
import java.net.DatagramPacket;
import java.net.InetAddress;

public class Client extends Thread
{
    private final DatagramSocket socket;
    private final InetAddress server_ip_addr;
    private final int server_udp_port;
    
    public Client(String ip_addr, int udp_port) throws IOException
    {
        super();
        setDaemon(true);
        socket = new DatagramSocket();
        server_ip_addr = InetAddress.getByName(ip_addr);
        server_udp_port = udp_port;
    }

    @Override
    public void run()
    {
        try
        {
            byte[] send_data = new byte[1];
            DatagramPacket packet = new DatagramPacket(
                send_data, send_data.length, server_ip_addr, server_udp_port);
                    
            while (true)
                socket.send(packet);
        }
        catch (Exception ex)
        {
            System.out.println("\nWeird exception\n");
            System.exit(-1);
        }
    }
}