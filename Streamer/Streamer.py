from threading import Thread
from app.GPS import GPS
from app.MixedSoundStreamServer import MixedSoundStreamServer
from app.MixedSoundStreamClient import MixedSoundStreamClient
import time


class Host(Thread):
    """Manage sound streaming host and connection with it"""
    daemon = True
    TRY_CONNECT_INTERVAL_SECONDS = 10

    @property
    def name(self):
        return f"Host {self.ip}"

    def __init__(self, ip, port=12345):
        Thread.__init__(self)
        self.ip = ip
        self.port = port

    def run(self, gps):
        while True:
            print(f"Trying to connect to {self.ip}:{self.port}")
            mss_client = MixedSoundStreamClient(
                self.ip, self.port, "1ch44100Hz.wav", gps)
            mss_client.start()
            mss_client.join()
            time.sleep(self.TRY_CONNECT_INTERVAL_SECONDS)


if __name__ == '__main__':
    gps = GPS()
    gps.start()
    mss_server = MixedSoundStreamServer("localhost", 12345, gps)
    mss_server.start()
    mss_client = Host("192.168.0.4", 12345)
    mss_client.run(gps)
    mss_client.join()
