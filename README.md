# CGMinerTuner version 0.2

This program will basically try find the sweet spot for your GPU.
It works by recording the hash rate at all the valid clocks within ranges you specify, and displaying the top results. 

## Configuring CGMiner

Before you can use CGMinerTuner, you need to enable the CGMiner's API interface.
To do this, you just need to append --api-listen --api-allow W:127.0.0.1 to your CGMiner command line options.
Replace 127.0.0.1 with your IP if you are connecting to CGMiner remotely.

## Usage:

python CGMinerTuner.py [-h] [-i HOST] [-p PORT] [-d DEVICE] -c CORERANGE -m
                       MEMRANGE [-r RATIORANGE] [--coreinc COREINC]
                       [--meminc MEMINC] [-w WAITTIME] [-t MAXTEMP]
                       [--showtop SHOWTOP]

optional arguments:
  -h, --help            show this help message and exit
  -i HOST, --host HOST  CGMiner host address. Defaults to localhost.
  -p PORT, --port PORT  CGMiner API port. Defaults to 4028.
  -d DEVICE, --device DEVICE
                        OpenCL device number to test. Defaults to 0.
  -c CORERANGE, --corerange CORERANGE
                        Set the GPU core clock range to test. Format is range:
                        <minval>-<maxval>.
  -m MEMRANGE, --memrange MEMRANGE
                        Set the GPU memory clock range to test. Format is
                        range: <minval>-<maxval>.
  -r RATIORANGE, --ratiorange RATIORANGE
                        Set the desired GPU core clock to GPU memory clock
                        ratio range to use. This can dramatically reduce the
                        search space. Format: <minratio>-<maxratio>. Disabled
                        by default.
  --coreinc COREINC     Set the GPU core clock increment amount. Defaults to
                        10.
  --meminc MEMINC       Set the GPU memory clock increment amount. Defaults to
                        10.
  -w WAITTIME, --waittime WAITTIME
                        Time (s) to wait for new clocks to settle before
                        reading the new hashrate. Defaults to 30 seconds.
  -t MAXTEMP, --maxtemp MAXTEMP
                        Cut-off temp at which clocks will be set to minimum.
                        Defaults to 80 degrees celcius.
  --showtop SHOWTOP     Specify the number of top results to show. Defaults to
                        5.

The results are also stored in a log file within the same directory.

## Example Usage

The following will search for the best core and memory clock for the second GPU in host 192.168.0.4 between core clocks of 800 to 1100 and memory clocks 1100-1500.
It will also only test core and memory combinations that fall within the ratio of 0.5 to 0.7, prevent testing from letting the GPU exceed 82 degrees, and show the top 10 results.

python CGMinerTuner.py -h 192.168.0.4 -d 1 -c 800-1100 -m 1100-1500 -r 0.5-0.7 -t 82 --showtop 10

If you found the script useful, please consider making a donation :)
BTC: 1CM1zDcfUpg81fCJxacq2nNsZCE3G96FLH
LTC: Lej4FBr9k3HM49GJix922xyJCm1whqHmfU
FTC: 72KjWoZKM3C8S8xaujTNwcFjFbq48XNfpg