package server;

public class Main
{
    public static void main(String[] args)
    {
        try
        {
            Counter counter = new Counter();
            counter.start();
        
            // create several servers that share the same counter.
            Server s1 = new Server(35610,counter);
            s1.start();

            while (true)
            {
                Thread.sleep(1000);

            }
        }
        catch (Exception ex)
        {
            System.out.println("\nSomething weird here\n");
            assert(false);
            return;
        }
    }
}