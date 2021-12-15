from threading import Thread
import time
import RPi.GPIO as GPIO


class Flag(Thread):
    """フラッグスレッド"""
    name = "Flag"
    daemon = True

    SWITCH_PIN = 4
    LED_RED_PIN = 23
    LED_YELLOW_PIN = 24

    state = 1  # 赤チームが確保で2,ニュートラル1,黄チームで0

    def __init__(self):
        Thread.__init__(self)

    def run(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.SWITCH_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.LED_RED_PIN, GPIO.OUT)
        GPIO.setup(self.LED_YELLOW_PIN, GPIO.OUT)

        last = 0
        wait = False

        while True:
            inp = GPIO.input(self.SWITCH_PIN)
            if inp != last and last == 1:
                self.state = (self.state+1) % 3
                wait = True
            last = inp

            if self.state == 2:
                GPIO.output(self.LED_RED_PIN, GPIO.HIGH)
                GPIO.output(self.LED_YELLOW_PIN, GPIO.LOW)
            elif self.state == 1:
                GPIO.output(self.LED_RED_PIN, GPIO.LOW)
                GPIO.output(self.LED_YELLOW_PIN, GPIO.LOW)
            elif self.state == 0:
                GPIO.output(self.LED_RED_PIN, GPIO.LOW)
                GPIO.output(self.LED_YELLOW_PIN, GPIO.HIGH)

            if wait:  # チャタリング防止のために待機
                wait = False
                time.sleep(0.1)