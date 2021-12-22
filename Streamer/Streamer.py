import os
import time
from app.StreamPlayer import StreamPlayer
from app.Flag import Flag
from app.StreamReader import StreamReader
import socket
import numpy as np
from app.MixStream import MixStream
from app.WaveStream import WaveStream
from app.MicStreamBuilder import MicStreamBuilder
from app.AudioPropery import AudioProperty
from app.GPS import GPS
from app.ENV import MAX_HOST, DEBUG, DEVICE_TYPE

# バイト数 = サンプル幅(1フレームあたりのバイト数) x チャンネル数 x フレーム数
# サンプル幅は基本2らしい
# サンプル幅 = フォーマット 16bit なら 2バイト


def getMyIp():
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
    return host_addr


def main():
    # マイクが基本1chのことが多め
    # waveファイルのチャンネル数・レート数と揃えておくこと
    WAVE_FILENAME = "1ch44100Hz.wav"
    # WAVE_FILENAME = "onepoint24_2ch48000Hz.wav"
    AUDIO_PROPERTY = AudioProperty(1, 16,  44100, 8192)

    # カレントディレクトリ設定
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    gps = GPS(False)
    gps.start()
    #gps.lat = 34.713548
    #gps.lon = 137.767386

    host_addr = getMyIp()

    if DEVICE_TYPE in ["FLAG"]:
        flag = Flag()
        flag.start()

    if DEVICE_TYPE in ["DEBUG", "MINOR"]:
        # デバッグデバイスまたはマイノリティデバイスである場合は、通信によって送られてきた音声を再生

        # 地磁気センサスレッドを開設
        from app.Magnetic import Magnetic
        magnetic = Magnetic()
        magnetic.start()

        # 送信されてくるストリームを待ち受け, 再生する(他人から自分へ)
        from app.SoundListeningServer import SoundListeningServer
        mss_server = SoundListeningServer(host_addr, 12345, gps, magnetic)
        mss_server.start()

    if DEVICE_TYPE in ["DEBUG", "MAJOR", "MINOR"]:
        # フラッグデバイス以外はマイクストリームを開設
        mic_stream = MicStreamBuilder().build(AUDIO_PROPERTY.format_bit,
                                              AUDIO_PROPERTY.rate, AUDIO_PROPERTY.frames)
        mic_stream.volume = 1

    if DEVICE_TYPE in ["DEBUG", "FLAG"]:
        # デバッグモードまたはフラッグデバイスの場合はwaveストリームを開設
        wave_stream = WaveStream(
            WAVE_FILENAME, AUDIO_PROPERTY.format_bit, True)
        wave_stream.volume = 0.5

    if DEVICE_TYPE in ["DEBUG"]:
        # デバッグモードの場合はmixストリームを開設
        mix_stream = MixStream(wave_stream, mic_stream)

    from app.Host import Host
    print(f"format: {AUDIO_PROPERTY.format_bit}")

    if DEVICE_TYPE == "DEBUG":
        stream = mix_stream
    if DEVICE_TYPE in ["MAJOR", "MINOR"]:
        stream = mic_stream
    elif DEVICE_TYPE == "FLAG":
        stream = wave_stream

    # マイクストリーム(または音楽、混合ストリーム)を受け持ち, 各ソケットに分配(自分から他人へ)
    stream_reader = StreamReader(
        stream, gps, AUDIO_PROPERTY.frames, AUDIO_PROPERTY.rate, DEBUG)
    stream_reader.start()

    # マイクストリーム(または音楽、混合ストリーム)を受け持ち, 再生する(自分から自分へ)
    if DEVICE_TYPE in ["DEBUG", "MAJOR"]:
        stream_player = StreamPlayer(
            stream, AUDIO_PROPERTY.rate, AUDIO_PROPERTY.frames)
        stream_player.start()

    hosts = []

    for i in range(1, MAX_HOST+1):
        addr = f"192.168.0.{i}"
        if addr == host_addr:  # 自分自身への接続を避ける
            continue
        mss_client = Host(addr, 12345,
                          gps, stream_reader, AUDIO_PROPERTY)
        hosts.append(mss_client)
        mss_client.start()

    print_len = len(hosts)+2
    if flag != None:
        print_len += 1

    try:
        while True:
            for host in hosts:
                print(host.ip+"\t"+host.last_message)
            print(f"GPS {gps.last_message}")
            if flag != None:
                print(f"flag {flag.last_message}")
            time.sleep(0.5)
            print(f"\033[{print_len}A\033[2J")
            pass
    except KeyboardInterrupt:
        print("The streamer stopped due to KeyboardInterrupt.")


if __name__ == '__main__':
    main()
