import socket
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect(('192.168.19.100',8501))
    s.sendall(b'RD DM6101\r')
    print(s.recv(10))