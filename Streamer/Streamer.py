import pyaudio
from app.MicStream import MicStream
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

    def __init__(self, ip, port, gps: GPS, mic_stream: MicStream):
        Thread.__init__(self)
        self.ip = ip
        self.port = port
        self.gps = gps
        self.mic_stream = mic_stream

    def run(self):
        while True:
            print(f"Trying to connect to {self.ip}:{self.port}")
            mss_client = MixedSoundStreamClient(
                self.ip, self.port, "1ch44100Hz.wav", self.gps, self.mic_stream)
            mss_client.run()
            time.sleep(self.TRY_CONNECT_INTERVAL_SECONDS)


if __name__ == '__main__':
    RATE = 44100
    CHUNK = 4096  # 1度の送信で音声情報を何バイト送るか (なぜか指定数値の4倍量が送られる)
    # → 512バイト/2バイト*8ビット→ 4倍量 になってると思われる
    FORMAT = pyaudio.paInt16
    MAX_HOST = 16  # 最大でいくつのホストに接続を施行するか
    gps = GPS()
    gps.start()
    # localhostを指定すると、自分から自分への接続は弾いてくれる（謎）
    mss_server = MixedSoundStreamServer("localhost", 12345, gps)
    mss_server.start()
    mic_stream = MicStream(FORMAT, RATE, CHUNK)
    for i in range(1, MAX_HOST):
        mss_client = Host(f"192.168.0.{i}", 12345, gps, mic_stream)
        mss_client.start()
    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("The streamer stopped due to KeyboardInterrupt.")
