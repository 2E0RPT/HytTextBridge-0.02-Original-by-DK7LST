#!/usr/bin/python3

# Repeater Firmware: A8.05.07.001

import socket
import _thread
import time
import signal
import sys
import substring

# IP-Adresse vom Repeater:
#LOCAL_IP = "127.0.0.1"
#RPT_IP = "127.0.0.1"
LOCAL_IP = "192.168.1.76"
RPT_IP = "192.168.1.204"

# UDP ports:
SMS_PORT_TS1 = 30007
SMS_PORT_TS2 = 30008

smsdata = "Nothing"
lastsms = 0

# Bei STRG+C beenden:
def signal_handler(signal, frame):
  print("Abort!")
  sys.exit(0)

class TextSlot:
  def __init__(self, name, RptIP, SMS_Port):
    # Portnummern merken:
    self.name = name
    self.RptIP = RptIP
    self.SMS_Port = SMS_Port

    # Constants:
    self.WakeCallPacket = bytes.fromhex('324200050000')
    self.IdleKeepAlivePacket = bytes.fromhex('324200020000')

    self.SMS_Seq = 0

    # Socket anlegen:
    self.SMS_Sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Socket an Ports binden:
    self.SMS_Sock.bind((LOCAL_IP, SMS_Port))
    _thread.start_new_thread(self.SMS_Rx_Thread, (name,))
    _thread.start_new_thread(self.TxIdleMsgThread, (name,))

  def getNextSMSSeq(self):
    if self.SMS_Seq < lastsms:
      self.SMS_Seq = lastsms
    self.SMS_Seq = (self.SMS_Seq + 1) & 0xFF
    return self.SMS_Seq

  def sendACK(self, seq):
    AckPacket = bytearray.fromhex('324200010100')
    AckPacket[5] = seq;
    self.SMS_Sock.sendto(AckPacket, (self.RptIP, self.SMS_Port))
    print("<<<ACK>>> - This never seems to happen.")

  def SMS_Rx_Thread(self, threadName):
    print(threadName, "SMS_Rx_Thread started")
    while True:
      data, addr = self.SMS_Sock.recvfrom(1024)
      global lastsms
      #print(threadName, "SMS_Rx_Thread: received message:", data)
      smsdata = data.replace(b"\x00",b"")
      smsdata = smsdata[19:len(smsdata)-2]
      if len(smsdata) > 0:
        if smsdata[0:2] == data[30:32]:
          smsdata = smsdata.replace(data[30:32],b"")
        #print(smsdata)
        #print(data)
        showdata = data.decode('utf8', errors="ignore")
        #print("SD: " + showdata)
        z = list(data)
        #print("List:")
        #print(z)
        smsno = data[21:24]
        sentno = int.from_bytes(smsno, "big")
        #print("SMS-Number:")
        #print(smsno)
        #print("Message-Number:")
        #print(sentno)
        smsfm = data[29:32]
        #print("SMS From:")
        #print(smsfm)
        sentfm = int.from_bytes(smsfm, "big")
        #print("Sent From: " + str(sentfm))
        smsto = data[25:28]
        sentto = int.from_bytes(smsto, "big")
        #print("Sent To: " + str(sentto))
        #print("REPEATER: ")
        #print(addr)
        #print(sentto)
        print(self)
        if sentno > lastsms:
          print("Repeater: ", end =" ")
          print(addr, end =" ")
          print(" Message-Number: ", end =" ")
          print(sentno, end =" ")
          print(" From: " + str(sentfm) + " To: " + str(sentto), end =" ")
          print("Message: ", end =" ")
          print(smsdata)
          lastsms = sentno
        #print("End of message processing.")
      #print(data.replace(b"\x00", b""))
      

  def TxIdleMsgThread(self, threadName):
    print(threadName, "TxIdleMsgThread started")
    self.SMS_Sock.sendto(self.WakeCallPacket, (self.RptIP, self.SMS_Port))
    while True:
      self.SMS_Sock.sendto(self.IdleKeepAlivePacket, (self.RptIP, self.SMS_Port))
      time.sleep(2)

  def sendText(self, SrcId, DstId, text):
    packet = bytearray.fromhex('3242000000040900a1000e300000040a0000000a000000')
    packet[5] = packet[14] = self.getNextSMSSeq()
    packet[10] = 12 + len(text) * 2
    packet[16] = (DstId >> 16) & 0xFF
    packet[17] = (DstId >> 8) & 0xFF
    packet[18] = DstId & 0xFF
    packet[20] = (SrcId >> 16) & 0xFF
    packet[21] = (SrcId >> 8) & 0xFF
    packet[22] = SrcId & 0xFF
    packet += bytes(text, "utf-16le")
    packet.append(0) #ChkSum
    packet.append(3)
    for i in range(0, 256):
      packet[len(packet) - 2] = i
      self.SMS_Sock.sendto(packet, (self.RptIP, self.SMS_Port))
      time.sleep(0.1)

print("HytTextBridge 0.01")
signal.signal(signal.SIGINT, signal_handler)

TextSlot1 = TextSlot("TS1", RPT_IP, SMS_PORT_TS1)
TextSlot2 = TextSlot("TS2", RPT_IP, SMS_PORT_TS2)

print("Waiting...")
time.sleep(1)
print("Ready...")
print("C) Crash radio to a powercycle lockout")
print("S) Send message")
print("X) eXit")
TextSlot1.sendText(200, 555555, "Test 1 Testing.")
TextSlot1.sendText(200, 555555, "Test 2 Testing.")
TextSlot1.sendText(200, 555555, "Test 3 Testing.")
#print("Sending other...")
time.sleep(400)

time.sleep(400)
time.sleep(400)
time.sleep(400)
time.sleep(400)
time.sleep(400)
time.sleep(400)
time.sleep(400)
time.sleep(400)
time.sleep(400)

print("...")
print("SMS_Data: " + smsdata)
print("...")
print("Exit!")

sys.exit(0)

