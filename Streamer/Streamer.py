from app.StreamReader import StreamReader
import socket
import numpy as np
from app.MixStream import MixStream
from app.WaveStream import WaveStream
from app.MicStreamBuilder import MicStreamBuilder
from app.AudioPropery import AudioProperty
from app.GPS import GPS
from app.SoundListeningServer import SoundListeningServer

# バイト数 = サンプル幅(1フレームあたりのバイト数) x チャンネル数 x フレーム数
# サンプル幅は基本2らしい
# サンプル幅 = フォーマット 16bit なら 2バイト


def main():
    MAX_HOST = 16  # 最大でいくつのホストに接続を施行するか
    USE_WAV = True
    DEBUG = False
    # pyaudio.paInt16
    # マイクが基本1chのことが多め
    # waveファイルのチャンネル数・レート数と揃えておくこと
    WAVE_FILENAME = "1ch44100Hz.wav"
    # WAVE_FILENAME = "onepoint24_2ch48000Hz.wav"
    AUDIO_PROPERTY = AudioProperty(1, 16,  44100, 8192)

    gps = GPS()
    gps.start()
    # localhostを指定すると、自分から自分への接続は弾いてくれる（謎）

    host_addr = ""
    for i in range(1, MAX_HOST):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.bind((f"192.168.0.{i}", 12345))
                sock.listen(5)
                host_addr = f"192.168.0.{i}"
                sock.close()
            break
        except Exception:
            continue

    mss_server = SoundListeningServer(host_addr, 12345, gps)
    mss_server.start()

    mic_stream = MicStreamBuilder().build(AUDIO_PROPERTY.format_bit,
                                          AUDIO_PROPERTY.rate, AUDIO_PROPERTY.frames)
    mic_stream.volume = 1

    # 音楽ファイル読み込み
    if USE_WAV:
        wave_stream = WaveStream(
            WAVE_FILENAME, AUDIO_PROPERTY.format_bit, True)
        wave_stream.volume = 0.5

    mix_stream = MixStream(wave_stream, mic_stream)

    from app.Host import Host
    print(f"format: {AUDIO_PROPERTY.format_bit}")

    stream_reader = StreamReader(
        mix_stream, gps, AUDIO_PROPERTY.frames, AUDIO_PROPERTY.rate, DEBUG)
    stream_reader.start()

    for i in range(1, MAX_HOST):
        addr = f"192.168.0.{i}"
        if addr == host_addr:  # 自分自身への接続を避ける
            continue
        mss_client = Host(addr, 12345,
                          gps, stream_reader, AUDIO_PROPERTY)
        mss_client.start()
    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("The streamer stopped due to KeyboardInterrupt.")


if __name__ == '__main__':
    main()
