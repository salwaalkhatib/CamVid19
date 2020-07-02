import socket
import numpy as np
import cv2 as cv
import threading


addr = ("127.0.0.1", 9000)
buf = 512
width = 640
height = 480
cap = cv.VideoCapture(0)
cap.set(3, width)
cap.set(4, height)
code = 'start'
code = ('start' + (buf - len(code)) * 'a').encode('utf-8')

def handle_client(c,a):
    print("Starting")
    while(cap.isOpened()):
        ret, frame = cap.read()
        if ret:
            c.sendto(code, addr)
            data = frame.tostring()
            for i in range(0, len(data), buf):
                c.sendto(data[i:i+buf], addr)
            # cv.imshow('send', frame)
            # if cv.waitKey(1) & 0xFF == ord('q'):
                # break
        else:
            break
    # s.close()
    # cap.release()
    # cv.destroyAllWindows()
    
if __name__ == '__main__':
    s = socket.socket(socket.SOCK_DGRAM)
    s.bind(('127.0.0.1',9000))
    s.listen(5)
    print("Waiting to connect...")
    while 1:
        c,a = s.accept()
        print("Connected!!")
        t = threading.Thread(target=handle_client,
                             args=(c,a))
        t.start()
    