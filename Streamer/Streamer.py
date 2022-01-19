from logging import DEBUG, NOTSET, CRITICAL
from logging import StreamHandler, FileHandler, Formatter
from ENV import DISABLE_HIT_JUDGE, MAX_HOST, DEBUG as DEBUG_MODE, DEVICE_TYPE, NETWORK_ADDRESS, HOST_ADDRESS_START, MAX_X, MIN_X, MAX_Y, MIN_Y
import logging
from datetime import datetime
import os
import time
from app.StreamPlayer import StreamPlayer
from app.StreamReader import StreamReader
import socket
from app.MixStream import MixStream
from app.WaveStream import WaveStream
from app.MicStreamBuilder import MicStreamBuilder
from app.AudioPropery import AudioProperty
from app.GPS import GPS


# バイト数 = サンプル幅(1フレームあたりのバイト数) x チャンネル数 x フレーム数
# サンプル幅は基本2らしい
# サンプル幅 = フォーマット 16bit なら 2バイト


def getMyIp():
    host_addr = ""
    for i in range(HOST_ADDRESS_START, HOST_ADDRESS_START+MAX_HOST):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.bind((NETWORK_ADDRESS+str(i), 12345))
                sock.listen(5)
                host_addr = NETWORK_ADDRESS+str(i)
                sock.close()
            break
        except Exception:
            continue
    return host_addr


def logger_setup():
    # ストリームハンドラの設定
    stream_handler = StreamHandler()
    stream_handler.setLevel(CRITICAL)
    stream_handler.setFormatter(Formatter("%(message)s"))

    # 保存先の有無チェック
    if not os.path.isdir('./logs'):
        os.makedirs('./logs', exist_ok=True)

    # ファイルハンドラの設定
    file_handler = FileHandler(
        f"./logs/log{datetime.now():%Y%m%d%H%M%S}.log", encoding="utf-8")

    file_handler.setLevel(DEBUG)
    file_handler.setFormatter(
        Formatter(
            "%(asctime)s@ %(name)s [%(levelname)s] %(funcName)s: %(message)s")
    )

    # ルートロガーの設定
    logging.basicConfig(level=NOTSET, handlers=[
                        stream_handler, file_handler])


def main():
    # カレントディレクトリ設定
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    # ロガー設定
    logger_setup()
    logger = logging.getLogger(__name__)

    try:
        # マイクが基本1chのことが多め
        # waveファイルのチャンネル数・レート数と揃えておくこと
        WAVE_FILENAME = "1ch44100Hz.wav"
        # WAVE_FILENAME = "onepoint24_2ch48000Hz.wav"
        AUDIO_PROPERTY = AudioProperty(1, 16,  44100, 8192)

        gps = GPS(False)
        gps.start()
        # gps.lat = 34.713548
        # gps.lon = 137.767386

        host_addr = getMyIp()

        flag = None
        if DEVICE_TYPE in ["FLAG"]:
            from app.Flag import Flag
            flag = Flag()
            flag.start()

        magnetic = None
        mss_server = None
        if DEVICE_TYPE in ["DEBUG", "MINOR"]:
            # デバッグデバイスまたはマイノリティデバイスである場合は、通信によって送られてきた音声を再生

            # 地磁気センサスレッドを開設
            from app.Magnetic import Magnetic
            magnetic = Magnetic(MAX_X, MIN_X, MAX_Y, MIN_Y)
            magnetic.start()

            # 送信されてくるストリームを待ち受け, 再生する(他人から自分へ)
            from app.SoundListeningServer import SoundListeningServer
            mss_server = SoundListeningServer(
                host_addr, 12345, gps, magnetic, DISABLE_HIT_JUDGE)
            mss_server.start()

        if DEVICE_TYPE in ["DEBUG", "MAJOR", "MINOR"]:
            # フラッグデバイス以外はマイクストリームを開設
            while True:
                mic_stream = MicStreamBuilder().build(AUDIO_PROPERTY.format_bit,
                                                      AUDIO_PROPERTY.rate, AUDIO_PROPERTY.frames)
                if mic_stream is None:
                    logger.error("Creating micstream has failed. retrying...")
                else:
                    break
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
            stream, gps, AUDIO_PROPERTY, DEBUG_MODE, magnetic)
        stream_reader.start()

        # マイクストリーム(または音楽、混合ストリーム)を受け持ち, 再生する(自分から自分へ)
        if DEVICE_TYPE in ["DEBUG", "MAJOR"]:
            stream_player = StreamPlayer(
                stream, AUDIO_PROPERTY.rate, AUDIO_PROPERTY.frames)
            stream_player.start()

        hosts = []

        for i in range(HOST_ADDRESS_START, HOST_ADDRESS_START+MAX_HOST):
            addr = NETWORK_ADDRESS + str(i)
            if addr == host_addr:  # 自分自身への接続を避ける
                continue
            mss_client = Host(addr, 12345,
                              gps, stream_reader, AUDIO_PROPERTY)
            hosts.append(mss_client)
            mss_client.start()

        print_len = len(hosts)+2
        if flag != None:
            print_len += 1
        if magnetic != None:
            print_len += 1
        if mss_server != None:
            print_len += 1
        while True:
            for host in hosts:
                print(host.ip+"\t"+host.last_message)
            print(f"GPS {gps.last_message}")
            if flag != None:
                print(f"flag {flag.last_message}")
            if magnetic != None:
                print(f"magnetic {magnetic.last_message}")
            final_print_len = print_len
            if mss_server != None:
                sock_list = mss_server.getSocketList()
                final_print_len = print_len+len(sock_list)
                print(f"mss_server {mss_server.last_message}")
                for addr in sock_list:
                    print(f"recv {addr} {mss_server.recieves[addr]}")
            time.sleep(1)
            print(f"\033[{final_print_len}A\033[2J")
            pass
    except KeyboardInterrupt:
        logger.info("The streamer stopped due to KeyboardInterrupt.")
    except Exception:
        logger.exception("Unhandled expecption has occured!")


if __name__ == '__main__':
    main()
