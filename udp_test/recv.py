import socket

HOST_NAME = ''
PORT = 8080
# ipv4を使うので、AF_INET
# udp通信を使いたいので、SOCK_DGRAM
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# ブロードキャストするときは255.255.255.255と指定せずに空文字
sock.bind((HOST_NAME, PORT))

try:
    while True:
        # データを待ち受け

        rcv_data, addr = sock.recvfrom(1024)
        print(f"receive data : [{rcv_data}]  from {addr[0]}:{addr[1]}")
except KeyboardInterrupt:
    print("program stopped due to keyboard interrupt")

sock.close()
