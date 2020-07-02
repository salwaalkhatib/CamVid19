from flask import Flask, render_template, url_for, request, session, redirect,jsonify,Response
import sys
import socket
import struct
import random
import threading
from threading import Thread
import time




sendingLock = threading.Lock()
window = {}
closeFlag = True
maxSeqNum = -1

#Thread that reads the file continuously
class fileReader(threading.Thread):
	def __init__(self, cmdInput, cSock, receiver):
		threading.Thread.__init__(self)
		self.host = '127.0.0.1'				#SERVER IP ADDRESS
		self.port = int(5777)		#SERVER PORT
		self.file = 'send.txt'				#FILE TO TRANSMIT
		self.n    = int(5)		#WINDOW SIZE
		self.MSS  = int(128)		#MAXIMUM SEGMENT SIZE
		self.sock = cSock
		self.r = receiver
		self.packetsLost = []
        
		self.start()		

	def computeChecksum(self, data):
		sum = 0
		for i in range(0, len(data), 2):
			if i+1 < len(data):
				data16 = ord(data[i]) + (ord(data[i+1]) << 8)		#To take 16 bits at a time
				interSum = sum + data16
				sum = (interSum & 0xffff) + (interSum >> 16)		#'&' to ensure 16 bits are returned
		return ~sum & 0xffff										#'&' to ensure 16 bits are returned
				
	def formPacket(self, data, seq):

		seqNum = struct.pack('=I',seq)
		checksum = struct.pack('=H',self.computeChecksum(data))		#Computes the checksum of data
		dataIndicator = struct.pack('=H',21845)
		packet = seqNum+checksum+dataIndicator+bytes(data,'UTF-8')
		return packet
		
	def run(self):
		self.rdt_send()	
		
	def retransmitter(self, host, port):
		global window
		global sendingLock
		
		
    
      
    
		sendingLock.acquire()
        
		for pac in window:
			if window[pac][2] == 0 and time.time() - window[pac][1] > 0.2:
				print('TIMEOUT, SEQUENCE NUMBER = '+str(pac))
				self.packetsLost.append('Packet Lost, SEQUENCE NUMBER = '+str(pac))
				window[pac] = (window[pac][0], time.time(), 0)
				self.sock.sendto(window[pac][0],(host, port))

		sendingLock.release()
		
	
	def rdt_send(self):
		global window
		global maxSeqNum

		fileHandle = open(self.file,'rb')
		currSeq = 0
		sendMsg = ''
		
		b = True
		while b:
			b = fileHandle.read(1)
			sendMsg += str(b,'UTF-8')
			if len(sendMsg) == self.MSS or (not b):		
				while len(window) >= self.n:
					#pass
					self.retransmitter(self.host,self.port)
				sendingLock.acquire()
				packet = self.formPacket(sendMsg, currSeq)				#Packets are created here
				window[currSeq] = (packet, time.time(), 0)
				self.sock.sendto(packet,(self.host, self.port))
				sendingLock.release()
				currSeq += 1
				sendMsg = ''
						
		sendMsg = '00000end11111'
		sendingLock.acquire()
		packet = self.formPacket(sendMsg, currSeq)				#Packets are created here
		window[currSeq] = (packet, time.time(), 0)
		self.sock.sendto(packet,(self.host, self.port))
		sendingLock.release()
		#sender(self.sock, self.host, self.port, sendMsg,currSeq)		#Thread spawned to send the end packet
		maxSeqNum = currSeq
		while len(window) > 0:
			self.retransmitter(self.host,self.port)
		fileHandle.close()



		
#Thread Class to receive the ACK Packets from the Server
class receiver(threading.Thread):
	def __init__(self, cmdInput, cSock):		
		threading.Thread.__init__(self)
		self.host = '127.0.0.1'
		self.port = 5777
		self.file = 'receive.txt'
		self.n    = int(10)
		self.MSS  = int(128)
		self.sockAddr = cSock
		self.start()
	def main():
            cliSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)	
            cliPort = 4455
            cliSocket.bind(('127.0.0.1',cliPort)) 
            
            startTime = time.time()
            ackReceiver = receiver(sys.argv[1:], cliSocket)					#Thread that receives ACKs from the Server
            fileHandler = fileReader(sys.argv[1:],cliSocket, ackReceiver) 	#Thread that reads the file and sending of packets
            fileHandler.join() 			#Main thread waits till the sender finishes
            ackReceiver.join()			#Main thread waits till the ACK receiver finishes
            endTime = time.time()
            lost_count = len(fileHandler.packetsLost)
            fileHandler.packetsLost.append("Probability of packet drop is: 0.8")
            fileHandler.packetsLost.append("The total number of packets is: "+str(maxSeqNum))
            fileHandler.packetsLost.append("The total number of re-transmitted packets is: "+str(lost_count))
            fileHandler.packetsLost.append('Total Time Taken:'+str(endTime-startTime))

            if cliSocket:
                cliSocket.close()
            
            return fileHandler.packetsLost
            

	def parseMsg(self, msg):
		sequenceNum = struct.unpack('=I', msg[0:4])			#Sequence Number Acked by the server
		zero16 = struct.unpack('=H', msg[4:6])				#16 bit field with all 0's
		identifier = struct.unpack('=H', msg[6:])			#16 bit field to identify the ACK packets
		return sequenceNum, zero16, identifier
		
	def run(self):
		print('Receiver Spawned')
		global sendingLock	
		global window
		global closeFlag

		closeFlag = True
		try:
			while closeFlag == True or len(window) > 0:			
				ackReceived, server_addr = self.sockAddr.recvfrom(2048)			#Receives the ACK packets 
				sequenceNum , zero16, identifier = self.parseMsg(ackReceived)
				if int(zero16[0]) > 0:
					print('Receiver Terminated')
					break
				#16 bit identifier field to identify the ACK packets - 1010101010101010 [in int 43690]		
				if int(identifier[0]) == 43690 and int(sequenceNum[0]) in window:
				#if int(identifier[0]) == 43690:
					#print('ACKED :'+str(sequenceNum[0]))
					sendingLock.acquire()
					setTime = window[int(sequenceNum[0])][1]
					window[int(sequenceNum[0])] = (window[int(sequenceNum[0])][0],setTime, 1)					
					del window[int(sequenceNum[0])]
					sendingLock.release()
				#print('Packet of Seq No.'+str(sequenceNum[0])+' Acked')
				
		except:
			print('Server closed its connection - Receiver')
			self.sockAddr.close()