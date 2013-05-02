#-------------------------------------------------------------------------------
# Name:        CGMinerAPI
# Purpose:     Provide an API to the CGMiner program
#
# Author:      Dale Tristram
#
# Created:     13/04/2013
# Copyright:   (c) Dale Tristram 2013
# Licence:     GPLv3
#-------------------------------------------------------------------------------
#!/usr/bin/env python

import socket
from time import sleep

class CGMinerAPI:

   def __init__(self, IP='127.0.0.1', port=4028):
      self.IP = IP
      self.port = port
      self.retryAttempts = 1
      self.BUFFSIZE = 8192
      self.numGPUs = -1
   
   def testConnection(self):
      sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      try:
         sock.connect((self.IP, self.port))
      except socket.error:
         return False
      socket.close()
      return True

   def parseResult(self, result):
      sections = []

      strsecs = result.split('|')
      if (len(strsecs) > 0):
         del strsecs[-1]
      for strsec in strsecs:
         params = strsec.split(',')
         #if (len(params) > 0):
         #   del params[-1]
         secparams = {}
         for param in params:
            keyval = param.split('=')
            if (len(keyval) < 2): continue
            secparams[keyval[0]] = keyval[1]
         sections.append(secparams)
      return sections

   def sendCommand(self, cmd):
      sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      connected = False
      attempts = 0
      while (connected != True and attempts < self.retryAttempts):
         try:
            sock.connect((self.IP, self.port))
            connected = True
         except socket.error:
            attempts += 1
      if (not connected):
         return False

      sock.send(bytearray(cmd, 'utf-8'))
      result = ''
      chunk = sock.recv(self.BUFFSIZE)
      while (len(chunk) != 0):
         result = result + str(chunk)
         chunk = sock.recv(self.BUFFSIZE)

      return result

   def sendQuery(self, cmd, value='', device = ''):
      query = cmd
      if not device == '':
         query += '|' + str(device)
         if not value == '':
            query += ','+str(value)
      elif not value == '':
         query += '|' + str(value)
      result = self.sendCommand(query)
      if result == False:
         raise Exception('Communication with CGMiner failed.')
      else: return self.parseResult(result)

   def setClock(self, device, newclock):
      try:
         result = self.sendQuery('gpuengine', newclock, device)
         sleep(3)
         actualclock = self.getGPUInfo(device)['GPU Clock']
         if (newclock == actualclock):
            return True
         return False
      except:
         raise

   def setMemClock(self, device, newclock):
      try:
         result = self.sendQuery('gpumem', newclock, device)
         sleep(3)
         actualclock = self.getGPUInfo(device)['Memory Clock']
         if (newclock == actualclock):
            return True
         return False
      except:
         raise

   def setFan(self, device, value):
      try:
         if value > 100 or value < 0:
            return False
         result = self.sendQuery('gpufan', value, device)
         print(result)
         sleep(1)
         actualFan = self.getGPUInfo(device)['Fan Percent']
         if not actualFan == value:
            return False
         return True
      except:
         raise


   def getGPUInfo(self, device):
      try:      
         sections = self.sendQuery('gpu', '', device)
         deviceInfo = {}
         if (len(sections) < 2):
            return deviceInfo
         section = sections[1]
         deviceInfo['Temperature'] = float(section['Temperature'])
         deviceInfo['GPU Clock'] = int(section['GPU Clock'])
         deviceInfo['Memory Clock'] = int(section['Memory Clock'])
         deviceInfo['GPU Voltage'] = float(section['GPU Voltage'])
         deviceInfo['Fan Percent'] = int(section['Fan Percent'])
         deviceInfo['Status'] = 1 if section['Status'] == 'Alive' else 0
         deviceInfo['HWE'] = int(section['Hardware Errors'])
         deviceInfo['id'] = int(section['GPU'])
         deviceInfo['Intensity'] = int(section['Intensity'])
         deviceInfo['Powertune'] = int(section['Powertune'])
         deviceInfo['MH'] = float(section['MHS 5s'] if 'MHS 5s' in section else section['MHS 1s'])
         deviceInfo['Utility'] = float(section['Utility'])

         return deviceInfo
      except:
         raise

   def getNumGPUs(self):
      if self.numGPUs != -1:
         return self.numGPUs
      try:
         devices = self.sendQuery('gpucount')
         if (len(devices) > 1):
            self.numGPUs = int(devices[1]['Count'])
            return self.numGPUs
      except Exception, e:
         raise e
