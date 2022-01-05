import logging
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
    last_message = "NEUTRAL"

    def __init__(self):
        Thread.__init__(self)

    def run(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.SWITCH_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.LED_RED_PIN, GPIO.OUT)
        GPIO.setup(self.LED_YELLOW_PIN, GPIO.OUT)

        last = 0
        wait = False

        # 起動表示
        for _ in range(3):
            GPIO.output(self.LED_RED_PIN, GPIO.HIGH)
            GPIO.output(self.LED_YELLOW_PIN, GPIO.HIGH)
            time.sleep(0.5)
            GPIO.output(self.LED_RED_PIN, GPIO.LOW)
            GPIO.output(self.LED_YELLOW_PIN, GPIO.LOW)
            time.sleep(0.5)

        logger = logging.getLogger(__name__)

        while True:
            inp = GPIO.input(self.SWITCH_PIN)
            if inp != last and last == 1:
                self.state = (self.state+1) % 3
                if self.state == 2:
                    self.last_message = "RED"
                if self.state == 1:
                    self.last_message = "NEUTRAL"
                if self.state == 0:
                    self.last_message = "YELLOW"
                logger.info(self.last_message)
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


if __name__ == '__main__':
    Flag().run()
