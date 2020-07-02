import sys
import socket
import struct
import random
import threading


def parseMsg(msg):					#Parsing the Message received from client
	header = msg[0:8]
	data = msg[8:]	
	sequenceNum = struct.unpack('=I',header[0:4])		
	checksum = struct.unpack('=H',header[4:6])
	identifier = struct.unpack('=H',header[6:])
	dataDecoded = data.decode('UTF-8')	
	return sequenceNum, checksum, identifier, dataDecoded
	
def formAckPackets(seqAcked, type):
	seqNum 		 = struct.pack('=I', seqAcked)	#SEQUENCE NUMBER BEING ACKED	
	if type == 0:
		zero16 	 = struct.pack('=H', 0)
	else:
		zero16 	 = struct.pack('=H', 1)
	ackIndicator = struct.pack('=H',43690)		#ACK INDICATOR - 1010101010101010[INT 43690]
	ackPacket = seqNum+zero16+ackIndicator
	return ackPacket

def verifyChecksum(data, checksum):
	sum = 0
	
	for i in range(0, len(data), 2):
		if i+1 < len(data):
			data16 = ord(data[i]) + (ord(data[i+1]) << 8)		#To take 16 bits at a time
			interSum = sum + data16
			sum = (interSum & 0xffff) + (interSum >> 16)		#To ensure 16 bits
	currChk = sum & 0xffff 
	result = currChk & checksum
	
	if result == 0:
		return True
	else:
		return False
	
def main():
	#port filename probability
	
	port = int(5777)		#PORT ON WHICH SERVER WILL ACCEPT UDP PACKETS
	filename = 'receive.txt' 		#NAME OF THE NEW FILE CREATED
	prob = float(0.8)	   #PACKET DROP PROBABILITY
	buffer = {}			
	flag = True
	maxSeqNum = 0
	
	soc  = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)	
	host = '127.0.0.1'
	soc.bind((host,port)) 
	
	while True:	
		while flag or len(buffer) < maxSeqNum:
			receivedMsg, sender_addr = soc.recvfrom(1024)			#Receive packets sent by client
			sequenceNum, checksum, identifier, data = parseMsg(receivedMsg) 
			if random.uniform(0,1) > prob:							#PACKET MAY BE DROPPED BASED ON RANDOM VALUE
				chksumVerification = verifyChecksum(data, int(checksum[0]))
				if chksumVerification == True:
					if data != '00000end11111' and int(sequenceNum[0]) not in buffer:					#If not the END Packet
							buffer[int(sequenceNum[0])] = data						
					elif data == '00000end11111':
						flag = False
						maxSeqNum = int(sequenceNum[0])
					#print('ACKED:'+str(sequenceNum[0]))
					ackPacket = formAckPackets(int(sequenceNum[0]),0)		#Generating ACK Packet
					soc.sendto(ackPacket,sender_addr)					#Sending ACK
						
			else:
				print('PACKET LOSS, SEQUENCE NUMBER = '+str(sequenceNum[0]))	#Packet dropped if randomValue <= probability
		
		ackPacket = formAckPackets(maxSeqNum+1,1)
		soc.sendto(ackPacket,sender_addr)
		#print('Termination Initiated')
		fileHandler = open(filename,'a')
		for i in range(0, maxSeqNum):
			fileHandler.write(buffer[i])
		fileHandler.close()
		print('File Received Successfully at the Server')
		flag = True
		buffer = {}
	
	
if __name__ == '__main__':
	print("Connecting..")
	main()