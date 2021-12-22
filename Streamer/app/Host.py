from app.StreamReader import StreamReader
from app.BytesStream import BytesStream
from app.AudioPropery import AudioProperty
import time
from app.SoundSendingClient import SoundSendingClient
from app.GPS import GPS
from threading import Thread
from app.MicStream import MicStream


class Host(Thread):
    """Manage sound streaming host and connection with it"""
    daemon = True
    TRY_CONNECT_INTERVAL_SECONDS = 10
    last_message = ""

    @property
    def name(self):
        return f"Host {self.ip}"

    def __init__(self, ip, port, gps: GPS, stream_reader: StreamReader, audio_property: AudioProperty):
        Thread.__init__(self)
        self.ip = ip
        self.port = port
        self.gps = gps
        self.stream_reader = stream_reader
        self.audio_property = audio_property

    def run(self):
        while True:
            self.last_message = f"trying to connect"
            # print(f"Trying to connect to {self.ip}:{self.port}")
            self.mss_client = SoundSendingClient(
                self.ip, self.port, self.gps, self.stream_reader, self.audio_property, self)
            self.mss_client.run()
            if not self.mss_client.retry_soon:
                time.sleep(self.TRY_CONNECT_INTERVAL_SECONDS)

    def updateMessage(self):
        self.last_message = self.mss_client.last_message
