package client;

public class Main
{
    public static void main (String[] args)
    {
        try
        {
            String ip_addr = args[0];
            int udp_port = Integer.parseInt(args[1]);

            Client client = new Client(ip_addr, udp_port);
            client.start();
        
            while (true)
            {
                Thread.sleep(1000);
            }
        }
        catch (Exception ex)
        {
            System.out.println("\nWeird exception\n");
        }
    }
}