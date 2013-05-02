#-------------------------------------------------------------------------------
# Name:        CGMiner - Tuner
# Purpose:     Find the optimum CGMiner settings for your GPU(s)
#
# Author:      Dale Tristram
#
# Created:     13/04/2013
# Copyright:   (c) Dale Tristram 2013
# Licence:     GPLv3
#-------------------------------------------------------------------------------
#!/usr/bin/env python

from CGMinerAPI import CGMinerAPI
import time
try:
   from queue import Queue
except ImportError:
   from Queue import Queue

import argparse, sys

class Logger:
   def __init__(self, device):
      self.file = open('CGTunerLog-GPU'+str(device)+'.log', 'a')
   def getTime(self):
      return time.strftime("%d-%m-%Y %H:%M:%S", time.localtime())

   def addRecord(self, record):
      line = '{0}: Core: {1}, Mem: {2}, MH: {3}, Ratio: {4:.2}, Temp: {5}\n'.format(self.getTime(), record['core'], record['mem'], record['MH'], float(record['core'])/float(record['mem']), record['temp'])
      self.file.write(line)
      self.file.flush()
      print(line)
   def closeLog(self):
      self.file.write('{0} -- Closing log --'.format(self.getTime()))
      self.file.close()
   def writeEntry(self, text):
      self.file.write('{0}: {1}\n'.format(self.getTime(), text))
      self.file.flush()
      print(text)
   def newLine(self):
      self.file.write('\n')
      self.file.flush()
      print('')

class CGTuner:
   def __init__(self, api, device = 0, coreIncrement = 10, memIncrement = 10, monitorTime = 30, maxTemp = 85, showTop=5):
      self.api = api
      self.coreIncrement = coreIncrement
      self.memIncrement = memIncrement
      self.monitorTime = monitorTime
      self.useRatio = False
      self.device = device
      self.HWE = api.getGPUInfo(device)['HWE']
      self.maxTemp = maxTemp
      self.results = []
      self.logger = Logger(device)
      self.showTop = showTop

   def setClockRanges(self, coreRange, memRange):
      self.coreRange = coreRange
      self.memRange = memRange

   def setRatioRange(self, ratioRange):
      self.ratioRange = ratioRange
      self.useRatio = True

   def handleBadClocks(self, error, devInfo):
      self.logger.writeEntry('{0} Core: {1}, Mem: {2}. Resetting clocks.'.format(error, devInfo['GPU Clock'], devInfo['Memory Clock']))
      newrec = {'device': self.device, 'core': devInfo['GPU Clock'], 'mem': devInfo['Memory Clock'], 'success': False, 'MH': devInfo['Temperature'], 'temp': devInfo['Temperature'], 'HWE' : devInfo['HWE']}
      self.api.setClock(self.device, self.coreRange[0])
      self.api.setMemClock(self.device, self.memRange[0])
      self.results.append(newrec)
      self.logger.addRecord(newrec)

   def monitor(self, core, mem):
      startTime = time.time()
      avgMH = Queue()
      while ((time.time() - startTime) < self.monitorTime):
         time.sleep(5)
         devInfo = self.api.getGPUInfo(self.device)
         if devInfo['Temperature'] >= self.maxTemp:        
            self.handleBadClocks('Temperature threshold reached.', devInfo)
            return True
         if devInfo['HWE'] > self.HWE:
            self.HWE = devInfo['HWE']
            self.handleBadClocks('Hardware errors found.', devInfo)
            #Make sure we give the GPU time to set the new clocks so we get the final HW error count
            time.sleep(2)
            devInfo = self.api.getGPUInfo(self.device)
            self.HWE = devInfo['HWE']
            return True

         avgMH.put(devInfo['MH'])
         if (avgMH.qsize() >= 3):
            avgMH.get()


      #MH added should be averaged
      totalMH = 0
      numMH = 0
      while (not avgMH.empty()):
         totalMH += avgMH.get()
         numMH += 1
      avg = totalMH/numMH
      newrec = {'device': self.device, 'core': core, 'mem': mem, 'success': True, 'MH': avg, 'temp': devInfo['Temperature']}
      self.results.append(newrec)
      self.logger.addRecord(newrec)
      return False

   def getTimeEstimate(self):
      numIncrements = 0
      if self.useRatio == False:
         numIncrements = (self.memRange[1]-self.memRange[0])/self.memIncrement * (self.coreRange[1]-self.coreRange[0])/self.coreIncrement
      else:
         for coreclock in range(self.coreRange[0], self.coreRange[1]+self.coreIncrement, self.coreIncrement):
            for memclock in range(self.memRange[0], self.memRange[1]+self.memIncrement, self.memIncrement):
               ratio = float(coreclock)/float(memclock)
               if ratio >= self.ratioRange[0] and ratio <= self.ratioRange[1]:
                  numIncrements += 1

      numMins = numIncrements * self.monitorTime / 60 + 1
      numHours = numMins / 60
      numMins = numMins - numHours * 60

      return '{0} hours and {1} minutes'.format(numHours, numMins)

   def start(self):
      try:
         GPUInfo = self.api.getGPUInfo(self.device)

         self.logger.writeEntry('-- Starting tuner --')
         self.logger.writeEntry('Core Range: {0} - {1} in steps of {2}, Mem Range: {3} - {4} in steps of {5}{6}'
            .format(self.coreRange[0], self.coreRange[1], self.coreIncrement, self.memRange[0], self.memRange[1], self.memIncrement,
               '' if self.useRatio == False else ', constrained to ratios: {0} - {1}'.format(self.ratioRange[0], self.ratioRange[1])))
         self.logger.writeEntry('Estimated time to completion: {0}'.format(self.getTimeEstimate()))
         self.logger.newLine()

         for newcore in range(self.coreRange[0], self.coreRange[1]+self.coreIncrement, self.coreIncrement):
            result = self.api.setClock(self.device, newcore)
            if (not result):
               self.logger.writeEntry('Failed to set new GPU core clock: {0}'.format(newcore))
               continue
            for newmem in range(self.memRange[0], self.memRange[1]+self.memIncrement, self.memIncrement):
               ratio = float(newcore)/float(newmem)
               if self.useRatio and (ratio < self.ratioRange[0] or ratio > self.ratioRange[1]):
                  continue
               result = self.api.setMemClock(self.device, newmem)
               if (result != True):
                  self.logger.writeEntry('Failed to set new GPU memory clock: {0}'.format(newmem))
               else:
                  overheat = self.monitor(newcore, newmem)
                  if overheat: 
                     break; #pointless upping memory more, its just going to get hotter

         self.report()
         self.api.setClock(self.device, GPUInfo['GPU Clock'])
         self.api.setMemClock(self.device, GPUInfo['Memory Clock'])
      except Exception as e:
         print('Exception occured: {0}'.format(e))
         exit(-2)



   def report(self):
      self.logger.writeEntry('-- Report on {0} results --'.format(len(self.results)))
      dud = {'MH': 0, 'core' : 0, 'mem' : 0, 'temp': 0}
      top = []
      for entry in self.results:
         if len(top) < self.showTop:
            top.append(entry)
         else:
            for i, item in enumerate(top):
               if entry['MH'] > item['MH']:
                  top[i] = entry
                  break

      rep = '\n'
      for i, item in enumerate(top):
         rep += '{0}: MH: {1}, Core: {2}, Mem: {3}, Core/Mem Ratio: {4:.2}, Temp: {5}\n'.format(i+1, top[i]['MH'],top[i]['core'], top[i]['mem'], float(top[i]['core'])/float(top[i]['mem']), top[i]['temp'])

      self.logger.writeEntry(rep)

def parseRange(val, type=int):
   indx = val.find('-')
   badformat = False
   if indx != -1:
      minval = type(val[:indx])
      maxval = type(val[indx+1:])
      if (minval < maxval):
         return (minval,maxval)
      else:
         badformat = True
   else:
      badformat = True

   if badformat:
    return (-1,-1)


def main():
   parser = argparse.ArgumentParser()
   parser.add_argument('-i', '--host', default='127.0.0.1', help='CGMiner host address. Defaults to localhost.')
   parser.add_argument('-p', '--port', type=int, default=4028, help='CGMiner API port. Defaults to 4028.')
   parser.add_argument('-d', '--device', type=int, default=0, help='OpenCL device number to test. Defaults to 0.')
   parser.add_argument('-c', '--corerange', required=True, help='Set the GPU core clock range to test. Format is range: <minval>-<maxval>.')
   parser.add_argument('-m', '--memrange', required=True, help='Set the GPU memory clock range to test. Format is range: <minval>-<maxval>.')
   parser.add_argument('-r', '--ratiorange', help='Set the desired GPU core clock to GPU memory clock ratio range to use. This can dramatically reduce the search space. Format: <minratio>-<maxratio>. Disabled by default.')
   parser.add_argument('--coreinc', type=int, default=10, help='Set the GPU core clock increment amount. Defaults to 10.')
   parser.add_argument('--meminc', type=int, default=10, help='Set the GPU memory clock increment amount. Defaults to 10.')
   parser.add_argument('-w', '--waittime', type=int, default=30, help='Time (s) to wait for new clocks to settle before reading the new hashrate. Defaults to 30 seconds.')
   parser.add_argument('-t', '--maxtemp', type=float, default=80, help='Cut-off temp at which clocks will be set to minimum. Defaults to 80 degrees celcius.')
   parser.add_argument('--showtop', type=int, default=5, help='Specify the number of top results to show. Defaults to 5.')

   args = parser.parse_args()
   CoreRange = parseRange(args.corerange)
   MemRange = parseRange(args.memrange)
   RatioRange = False
   if CoreRange[0] == -1 or MemRange[0] == -1:
      print("Incorrect core or memory range format.")
      print(parser.format_help())
      sys.exit(2)

   if args.ratiorange:
      RatioRange = parseRange(args.ratiorange, float)
      if RatioRange[0] == -1:
         print("Incorrect ratio range range format.")
         print(parser.format_help())
         sys.exit(2)     


   api = CGMinerAPI(args.host, args.port)
   tuner = CGTuner(api, args.device, args.coreinc, args.meminc, args.waittime, args.maxtemp, args.showtop)
   tuner.setClockRanges(CoreRange,MemRange)
   if RatioRange != False:
      tuner.setRatioRange(RatioRange)
   tuner.start()


if __name__ == '__main__':
   main()
