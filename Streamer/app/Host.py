from app.BytesStream import BytesStream
from app.AudioPropery import AudioProperty
import time
from app.MixedSoundStreamClient import MixedSoundStreamClient
from app.GPS import GPS
from threading import Thread
from app.MicStream import MicStream


class Host(Thread):
    """Manage sound streaming host and connection with it"""
    daemon = True
    TRY_CONNECT_INTERVAL_SECONDS = 10

    @property
    def name(self):
        return f"Host {self.ip}"

    def __init__(self, ip, port, gps: GPS, input_stream: BytesStream, audio_property: AudioProperty):
        Thread.__init__(self)
        self.ip = ip
        self.port = port
        self.gps = gps
        self.stream = input_stream
        self.audio_property = audio_property

    def run(self):
        while True:
            print(f"Trying to connect to {self.ip}:{self.port}")
            mss_client = MixedSoundStreamClient(
                self.ip, self.port, self.gps, self.stream, self.audio_property)
            mss_client.run()
            time.sleep(self.TRY_CONNECT_INTERVAL_SECONDS)
