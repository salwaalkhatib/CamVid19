from socket import AF_INET, socket, SOCK_STREAM,SOCK_DGRAM
from threading import Thread,Lock
import linecache
import sys
import cv2 as cv
import numpy as np


import time

class Client:
    buffer_size = 512
    host = '127.0.0.1'
    port = 8888
    address_chat = (host,port)
    #Variables for connecting to streaming server
    address_stream = ('127.0.0.1',8888)
    buf = 512
    width = 640
    height = 480
    code = b'start'
    num_of_chunks = width * height * 3 / buf

    def __init__(self,name):
        self.client_socket_chat = socket(AF_INET, SOCK_STREAM)
        self.client_socket_chat.connect(self.address_chat)
        self.client_socket_stream = socket(SOCK_DGRAM)
        self.client_socket_stream.connect(self.address_stream)
        self.messages = []
        receive_thread = Thread(target = self.receive_messages)
        receive_thread.start()
        self.send_message(name)
        
    
    
    def get_frame(self):
        chunks = []
        start = False
        while len(chunks) < self.num_of_chunks:
            chunk, _ = self.s.recvfrom(self.buf)
            if start:
                chunks.append(chunk)
            elif chunk.startswith(self.code):
                start = True

        byte_frame = b''.join(chunks)

        frame = np.frombuffer(
            byte_frame, dtype=np.uint8).reshape(self.height, self.width, 3)

        ret,jpeg = cv.imencode('.jpg',frame)
        return jpeg.tobytes()
    
    
    def receive_messages(self):
        while True:
            try:
                
                message = self.client_socket_chat.recv(self.buffer_size).decode("utf8")
                self.messages.append(message)
                
                    
                if message == "{quit}":
                    self.client_socket_chat.close()
                    break
            
            except Exception as e:
                self.PrintException()
                break
    def send_message(self,message):
        self.client_socket_chat.send(bytes(message,"utf8"))
        time.sleep(1.5)
        if message == "{quit}":
                self.client_socket_chat.close()
        
    def get_messages(self):
        messages_copy = self.messages[:]
        self.messages = []
        return messages_copy
    def disconnect(self):
        self.send_message("{quit}")
    def PrintException():
        exc_type, exc_obj, tb = sys.exc_info()
        f = tb.tb_frame
        lineno = tb.tb_lineno
        filename = f.f_code.co_filename
        linecache.checkcache(filename)
        line = linecache.getline(filename, lineno, f.f_globals)
        print ('EXCEPTION IN ({}, LINE {} "{}"): {}'.format(filename, lineno, line.strip(), exc_obj))

