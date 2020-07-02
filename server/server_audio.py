import socket

import threading
import pyaudio

ip = '127.0.0.1'
port = 5858
addr = (ip,port)
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 1024
audio = pyaudio.PyAudio()
stream = audio.open(format=FORMAT, channels=CHANNELS,
                        rate=RATE, input=True,input_device_index=1,
                        frames_per_buffer=CHUNK)





def handle_client(c,a):
    print("Starting")
    i = 0
    while(True):
        i = i+1
        data =stream.read(CHUNK)
        if data:         
            c.sendto(data,addr)
        else:
            print("broke")
            break

    
if __name__ == '__main__':
    s = socket.socket(socket.SOCK_DGRAM)
    s.bind(('127.0.0.1',port))
    s.listen(10)
    print("Waiting to connect...")
    while 1:
        c,a = s.accept()
        print("Connected!!")
        t = threading.Thread(target=handle_client,
                             args=(c,a))
        t.start()
    