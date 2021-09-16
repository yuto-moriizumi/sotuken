from app.MixStream import MixStream
from app.WaveStream import WaveStream
from app.MicStreamBuilder import MicStreamBuilder
from app.AudioPropery import AudioProperty
import pyaudio
from app.GPS import GPS
from app.MixedSoundStreamServer import MixedSoundStreamServer


def main():
    MAX_HOST = 16  # 最大でいくつのホストに接続を施行するか
    USE_WAV = True
    WAVE_FILENAME = "1ch44100Hz.wav"
    AUDIO_PROPERTY = AudioProperty(pyaudio.paInt16, 2, 44100, 4096)

    gps = GPS()
    gps.start()
    # localhostを指定すると、自分から自分への接続は弾いてくれる（謎）
    # mss_server = MixedSoundStreamServer("localhost", 12345, gps)
    mss_server = MixedSoundStreamServer("192.168.0.8", 12345, gps)
    mss_server.start()
    mic_stream = MicStreamBuilder().build(AUDIO_PROPERTY.format_type,
                                          AUDIO_PROPERTY.rate, AUDIO_PROPERTY.chunk)
    # 音楽ファイル読み込み
    wave_stream = WaveStream(
        WAVE_FILENAME, AUDIO_PROPERTY.format_type, True) if USE_WAV else None
    print("mic", mic_stream)
    print("wave", wave_stream)
    mix_stream = MixStream(wave_stream, mic_stream)

    from app.Host import Host
    for i in range(1, MAX_HOST):
        mss_client = Host(f"192.168.0.{i}", 12345,
                          gps, mix_stream, AUDIO_PROPERTY)
        mss_client.start()
    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("The streamer stopped due to KeyboardInterrupt.")


if __name__ == '__main__':
    main()
