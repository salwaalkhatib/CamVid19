#!/usr/bin/env python

import pyaudio
import socket
import sys
import math
class ClientAudio:
    
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100
    CHUNK = 1024
    def __init__(self):
        self.s = socket.socket(socket.SOCK_DGRAM)
        self.s.connect(('127.0.0.1',5858))
        self.audio = pyaudio.PyAudio()
        self.stream = self.audio.open(format=self.FORMAT, channels=self.CHANNELS, rate=self.RATE, output=True, frames_per_buffer=self.CHUNK)
    

    def get_audio(self):
        data = self.s.recv(self.CHUNK)
        return data

'''s.close()
        stream.close()
        audio.terminate()'''