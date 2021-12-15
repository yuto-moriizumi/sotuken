import RPi.GPIO as GPIO
import time

PIN = 17

GPIO.setmode(GPIO.BCM)
GPIO.setup(PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

MODE = 0
last = 0

while True:
    inp = GPIO.input(PIN)
    if inp != last and last == 1:
        print("ボタンが離された")
        MODE = 1-MODE
        time.sleep(0.1)
    last = inp
    print(MODE)
