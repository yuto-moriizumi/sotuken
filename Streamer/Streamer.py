import wave
from app.MixStream import MixStream
from app.WaveStream import WaveStream
from app.MicStreamBuilder import MicStreamBuilder
from app.AudioPropery import AudioProperty
import pyaudio
from app.GPS import GPS
from app.MixedSoundStreamServer import MixedSoundStreamServer

# バイト数 = サンプル幅(1フレームあたりのバイト数) x チャンネル数 x フレーム数
# サンプル幅は基本2らしい
# サンプル幅 = フォーマット 16bit なら 2バイト


def main():
    MAX_HOST = 16  # 最大でいくつのホストに接続を施行するか
    USE_WAV = True
    # pyaudio.paInt16
    # マイクが基本1chのことが多め
    # waveファイルのチャンネル数・レート数と揃えておくこと
    WAVE_FILENAME = "1ch44100Hz.wav"
    AUDIO_PROPERTY = AudioProperty(1, 16,  44100, 1024)

    gps = GPS()
    gps.start()
    # localhostを指定すると、自分から自分への接続は弾いてくれる（謎）
    # mss_server = MixedSoundStreamServer("localhost", 12345, gps)
    mss_server = MixedSoundStreamServer("192.168.0.8", 12345, gps)
    mss_server.start()
    mic_stream = MicStreamBuilder().build(AUDIO_PROPERTY.format_bit,
                                          AUDIO_PROPERTY.rate)
    # 音楽ファイル読み込み
    wave_stream = WaveStream(
        WAVE_FILENAME, AUDIO_PROPERTY.format_bit, True) if USE_WAV else None
    mix_stream = MixStream(wave_stream, mic_stream)

    from app.Host import Host
    print(f"format: {AUDIO_PROPERTY.format_bit}")
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
