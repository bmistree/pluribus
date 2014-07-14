package server;

import java.util.concurrent.atomic.AtomicInteger;

/**
   Every polling period, announce throughput of packets received over
   that period.
 */

public class Counter extends Thread
{
    public final AtomicInteger counter = new AtomicInteger(0);
    private int previous_counter = 0;
    private static final int POLLING_PERIOD_SECONDS = 10; // poll every 10s
    private static final int SECONDS_TO_MS_MULTIPLIER = 1000;

    
    @Override
    public void run()
    {
        while (true)
        {
            try
            {
                Thread.sleep(
                    POLLING_PERIOD_SECONDS*SECONDS_TO_MS_MULTIPLIER);
            }
            catch (InterruptedException ie)
            {
                System.out.println("\n\nSomething weird and wrong\n\n");
                assert(false);
                break;
            }
            int current_value = counter.get();
            int num_received_in_period = current_value - previous_counter;

            double throughput = calc_throughput(num_received_in_period);
            previous_counter = current_value;

            // report info
            System.out.println(Double.toString(throughput) + " packets per second");
        }
    }

    /**
       @returns Packets per second.
     */
    private double calc_throughput(int num_received_in_period)
    {
        return ((double)num_received_in_period)/
            ((double) POLLING_PERIOD_SECONDS);
    }
}