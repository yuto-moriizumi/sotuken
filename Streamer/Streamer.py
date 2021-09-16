from app.MicStreamBuilder import MicStreamBuilder
from app.AudioPropery import AudioProperty
import pyaudio
from app.MicStream import MicStream
from app.GPS import GPS
from app.MixedSoundStreamServer import MixedSoundStreamServer


def main():
    audio_property = AudioProperty(pyaudio.paInt16, 2, 44100, 4096)
    MAX_HOST = 16  # 最大でいくつのホストに接続を施行するか
    gps = GPS()
    gps.start()
    # localhostを指定すると、自分から自分への接続は弾いてくれる（謎）
    # mss_server = MixedSoundStreamServer("localhost", 12345, gps)
    mss_server = MixedSoundStreamServer("192.168.0.8", 12345, gps)
    mss_server.start()
    mic_stream = MicStreamBuilder().build(audio_property.format,
                                          audio_property.rate, audio_property.chunk)
    from app.Host import Host
    for i in range(1, MAX_HOST):
        mss_client = Host(f"192.168.0.{i}", 12345,
                          gps, mic_stream, audio_property)
        mss_client.start()
    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("The streamer stopped due to KeyboardInterrupt.")


if __name__ == '__main__':
    main()
