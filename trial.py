import socket
import time

while True:

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect(('192.168.20.10', 8501))
        s.sendall(b'RD DM6010\r')
        ret = s.recv(5)[2:5]
        print(ret)
        if ret == b'100':
            s.sendall(b''.join([b'WR DM6510', b' ', b'200', b'\r']))
        elif ret == b'200':
            s.sendall(b''.join([b'WR DM6510', b' ', b'100', b'\r']))
    time.sleep(0.5)
