import serial
import time
s = serial.Serial('/dev/serial0', 9600, timeout=10)
while True:
    print(s.readline())
    time.sleep(0.5)
