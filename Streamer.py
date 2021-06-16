# wav, マイク, (gps:未実装)の配信クライアント
# wavファイルのみの配信と、wav+マイクの配信に対応

import numpy as np
import wave
import pyaudio
import socket
import threading
import micropyGPS
import threading
from copy import deepcopy

DUMMY_BYTE_TYPE = np.float64


class MixedSoundStreamClient(threading.Thread):
    USE_WAV = False

    def __init__(self, server_host, server_port, wav_filename):
        threading.Thread.__init__(self)
        self.SERVER_HOST = server_host
        self.SERVER_PORT = int(server_port)
        self.WAV_FILENAME = wav_filename

    def run(self):
        gps = None
        try:
            import serial
            # GPSモジュール初期化
            gps = micropyGPS.MicropyGPS(9, 'dd')  # MicroGPSオブジェクトを生成する。
            # 引数はタイムゾーンの時差と出力フォーマット
            gpsthread = threading.Thread(
                target=self.rungps, args=[gps])  # 上の関数を実行するスレッドを生成
            gpsthread.daemon = True
            gpsthread.start()  # スレッドを起動
        except ImportError:
            print(
                "[WARN] Serial module import error occured. GPS reader function disabled.")

        audio = pyaudio.PyAudio()

        # 音楽ファイル読み込み
        wav_file = None
        if self.USE_WAV:
            wav_file = wave.open(self.WAV_FILENAME, 'rb')

        # オーディオプロパティ
        # TODO: プロパティをwavではなくマイクのみで設定したい(マイクがwavファイルに合わせられない時がある)
        FORMAT = pyaudio.paInt16
        CHANNELS = wav_file.getnchannels() if wav_file != None else 1
        RATE = wav_file.getframerate() if wav_file != None else 22050
        DUMMY_BITS_PER_NUMBER = 64
        # 何バイトのダミーバイトを先頭に含むか 2バイトで数字1つ送れる
        DUMMY_BYTES = 3*(DUMMY_BITS_PER_NUMBER//8)
        CHUNK = 1024  # 1度の送信で音声情報を何バイト送るか (なぜか指定数値の4倍量が送られる)
        # → 512バイト/2バイト*8ビット→ 4倍量 になってると思われる

        # マイクの入力ストリーム生成
        # デバイスを0番から順番に試す
        mic_stream = None
        print('Streamer initiated, creating mic stream')
        for i in range(audio.get_device_count()):
            try:
                device_info = audio.get_device_info_by_index(i)
                device_name: str = device_info["name"]
                if "USB" in device_name or "Voice" in device_name:  # 名前に USB または Voice を含むデバイスならストリームを作成
                    mic_stream = audio.open(format=FORMAT,
                                            channels=CHANNELS,
                                            rate=RATE,
                                            input=True,
                                            frames_per_buffer=CHUNK, input_device_index=i)
                    print(
                        f"mic stream created with {device_info}")
                    break
            except:
                pass
        if mic_stream == None:
            print("[WARN] creating mic_stream failed")

        # サーバに接続
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((self.SERVER_HOST, self.SERVER_PORT))

            # サーバにオーディオプロパティを送信
            data = "{},{},{},{},{}".format(
                FORMAT, CHANNELS, RATE, CHUNK, DUMMY_BYTES).encode('utf-8')
            print(f"send:{data}")
            sock.send(data)

            # メインループ
            # 緯度、経度、海抜の初期化
            lat = -1
            lon = -1
            alt = -1
            course = -1
            while True:
                # 音楽ファイルからデータ読み込み
                if wav_file != None:
                    wav_data = wav_file.readframes(CHUNK)
                    # 音楽ファイルリピート再生処理
                    if wav_data == b'':
                        wav_file.rewind()
                        wav_data = wav_file.readframes(CHUNK)
                if mic_stream != None:  # マイクストリーム読み込み
                    mic_data = mic_stream.read(CHUNK)
                # サーバに音データを送信
                # ダミーの数値データ 数字1つで2バイト
                # 今回チャンクから4バイト引いているので 2つまで送れるはず
                # さて、なぜか送信するのはCHUNKの4倍量。サーバ側プログラムで対処。
                # dummy = np.array(
                #     [10*(i + 1) for i in range(DUMMY_BYTES//2)], np.int16)
                dummy = np.array(
                    [lat, lon, alt], DUMMY_BYTE_TYPE)
                if wav_file == None and mic_stream == None:  # どちらもない場合は空の音楽データを送信
                    data = self.mix_sound(
                        CHANNELS, CHUNK, b"", 1)
                else:
                    if wav_file != None and mic_stream == None:  # マイクがなく、wavがある場合はwavをそのまま送信
                        data = self.mix_sound(
                            CHANNELS, CHUNK, wav_data, 1)
                    if wav_file == None and mic_stream != None:  # wavがなくマイクがある場合はマイクをそのまま送信
                        data = self.mix_sound(
                            CHANNELS, CHUNK, mic_data, 1)
                    if wav_file != None and mic_stream != None:  # どちらもある場合はミックスして送信
                        data = self.mix_sound(
                            CHANNELS, CHUNK, wav_data, 0.5, mic_data, 0.5)
                    print(f"dymmy:{dummy} data:{data[0:8]}")

                # data = np.append(dummy, data)
                # if mic_stream == None:
                #     print(
                #         f"wav:{len(wav_data)}, data:{len(data.tobytes())}")
                # else:
                #     print(
                #         f"wav:{len(wav_data)}, mic:{len(mic_data)}, data:{len(data.tobytes())}")
                sock.send(dummy.tobytes()+data.tobytes())

                if gps != None and gps.clean_sentences > 20:  # ちゃんとしたデーターがある程度たまったら出力する
                    h = gps.timestamp[0] if gps.timestamp[0] < 24 else gps.timestamp[0] - 24
                    # print('時刻:%2d:%02d:%04.1f' %
                    #       (h, gps.timestamp[1], gps.timestamp[2]))
                    lat = gps.latitude[0]
                    lon = gps.longitude[0]
                    alt = gps.altitude
                    course = gps.course
                    print('緯度:%2.8f, 経度:%2.8f, 海抜: %f, 方位: %f' %
                          (lat, lon, alt, course))
                    # print(f"利用衛星番号:{gps.satellites_used}")
                    # print('衛星番号: (仰角, 方位角, SN比)')
                    # print(gps.satellite_data)
                    # for k, v in deepcopy(gps.satellite_data.items()):
                    #     print('%d: %s' % (k, v))
                    # print('')

        # 終了処理
        mic_stream.stop_stream()
        mic_stream.close()
        audio.terminate()

    # 2つの音データを1つの音データにミックス 1つしか渡されない場合は単にデコードする
    def mix_sound(self,  channels, frames_per_buffer, data1, volume1, data2=None, volume2=0):
        # 音量チェック
        if volume1 + volume2 > 1.0:
            return None
        # デコード
        decoded_data1: np.ndarray = np.frombuffer(data1, np.int16).copy()
        if data2 != None:
            decoded_data2: np.ndarray = np.frombuffer(data2, np.int16).copy()
        # データサイズの不足分を0埋め
        decoded_data1.resize(channels * frames_per_buffer, refcheck=False)
        if data2 != None:
            decoded_data2.resize(channels * frames_per_buffer, refcheck=False)
        # 音量調整 & エンコード
        if data2 != None:
            return (decoded_data1 * volume1 + decoded_data2 * volume2).astype(np.int16)
        return (decoded_data1 * volume1).astype(np.int16)

    def rungps(self, gps):  # GPSモジュールを読み、GPSオブジェクトを更新する
        import serial
        s = None
        try:
            s = serial.Serial('/dev/serial0', 9600, timeout=10)
        except AttributeError:
            print(
                "[WARN] module serial has no Serial constructor. GPS funtion disabled.")
            return
        while True:
            try:
                sentence = s.readline().decode('utf-8')  # GPSデーターを読み、文字列に変換する
                if sentence[0] != '$':  # 先頭が'$'でなければ捨てる
                    continue
                for x in sentence:  # 読んだ文字列を解析してGPSオブジェクトにデーターを追加、更新する
                    gps.update(x)
            except UnicodeDecodeError as e:
                pass


class MixedSoundStreamServer(threading.Thread):

    def __init__(self, server_host, server_port):
        threading.Thread.__init__(self)
        self.SERVER_HOST = server_host
        self.SERVER_PORT = int(server_port)

    def run(self):
        print("Sound Stream Listener started")
        # サーバーソケット生成
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_sock:
            server_sock.bind((self.SERVER_HOST, self.SERVER_PORT))
            server_sock.listen(4)

            # クライアントと接続
            while True:
                client_sock, addr = server_sock.accept()
                hbuf, sbuf = socket.getnameinfo(
                    addr, socket.NI_NUMERICHOST | socket.NI_NUMERICSERV)
                print("accept:{}:{}".format(hbuf, sbuf))
                t = threading.Thread(target=self.recv, args=[client_sock])
                t.start()

    def recv(self, client_sock):
        with client_sock:
            # クライアントからオーディオプロパティを受信
            settings_list = client_sock.recv(
                256).decode('utf-8').split(",")
            FORMAT = int(settings_list[0])
            CHANNELS = int(settings_list[1])
            RATE = int(settings_list[2])
            CHUNK = int(settings_list[3])
            DUMMY_BYTES = int(settings_list[4])

            # オーディオ出力ストリーム生成
            audio = pyaudio.PyAudio()
            stream = audio.open(format=FORMAT,
                                channels=CHANNELS,
                                rate=RATE,
                                output=True,
                                frames_per_buffer=CHUNK)

            print(settings_list)

            # メインループ
            data = b""
            while True:
                # クライアントから音データを受信
                # なぜかクライアントがCHUNKの4倍量を送ってくるので合わせる。
                data += (client_sock.recv(CHUNK*4+DUMMY_BYTES))

                # 切断処理
                if not data:
                    break
                if len(data) < CHUNK*4+DUMMY_BYTES:  # データが必要量に達していなければなにもしない
                    continue
                chunk = data[:CHUNK*4+DUMMY_BYTES]  # 使用チャンク分だけ取り出す
                data = data[CHUNK*4+DUMMY_BYTES:]  # 今回使わないデータだけ残す
                dummy = chunk[0:DUMMY_BYTES]
                sound = chunk[DUMMY_BYTES:]
                print(
                    f"recv:{len(chunk)} bytes, dummy:{np.frombuffer(dummy, DUMMY_BYTE_TYPE)}")
                print(np.frombuffer(chunk, np.int16)[:8])
                stream.write(sound)  # 再生


if __name__ == '__main__':
    mss_server = MixedSoundStreamServer("192.168.0.8", 12345)
    mss_server.daemon = True
    mss_server.start()
    # mss_server.join()
    mss_client = MixedSoundStreamClient("192.168.0.8", 12345, "1ch44100Hz.wav")
    mss_client.daemon = True
    mss_client.start()
    mss_client.join()
