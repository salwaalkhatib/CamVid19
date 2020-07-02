import socket
import numpy as np
import cv2 as cv




class ClientStream:
    addr = ("127.0.0.1", 9000)
    buf = 512
    width = 640
    height = 480
    code = b'start'
    num_of_chunks = width * height * 3 / buf
    
    def __init__(self):
         self.s = socket.socket(socket.SOCK_DGRAM)
         self.s.connect(self.addr)
    
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



