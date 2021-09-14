from .GPS import GPS
import numpy as np
import wave
import pyaudio
import socket
from threading import Thread


DUMMY_BYTE_TYPE = np.float64


class MixedSoundStreamClient(Thread):
    USE_WAV = False
    CHUNK = 4096  # 1度の送信で音声情報を何バイト送るか (なぜか指定数値の4倍量が送られる)
    # → 512バイト/2バイト*8ビット→ 4倍量 になってると思われる
    CHANNELS = 2

    def __init__(self, server_host, server_port, wav_filename, gps: GPS):
        Thread.__init__(self)
        self.SERVER_HOST = server_host
        self.SERVER_PORT = int(server_port)
        self.WAV_FILENAME = wav_filename
        self.gps = gps
        self.daemon = True
        self.name = "MixedSoundStreamClient"

    def run(self):
        audio = pyaudio.PyAudio()

        # 音楽ファイル読み込み
        wav_file = None
        if self.USE_WAV:
            wav_file = wave.open(self.WAV_FILENAME, 'rb')

        # オーディオプロパティ
        # TODO: プロパティをwavではなくマイクのみで設定したい(マイクがwavファイルに合わせられない時がある)
        FORMAT = pyaudio.paInt16
        if wav_file != None:
            self.CHANNELS = wav_file.getnchannels()
        RATE = wav_file.getframerate() if wav_file != None else 44100
        DUMMY_BITS_PER_NUMBER = 64
        # 何バイトのダミーバイトを先頭に含むか 2バイトで数字1つ送れる
        DUMMY_BYTES = 3*(DUMMY_BITS_PER_NUMBER//8)

        # マイクの入力ストリーム生成
        # デバイスを0番から順番に試す
        mic_stream = None
        print('Streamer initiated, creating mic stream')
        # 予定出力チャンネルでのストリーム開設を目指すが、失敗したらチャンネル数を1減らす
        mic_channels = 2
        for channels in range(self.CHANNELS, 0, -1):
            for i in range(audio.get_device_count()):
                try:
                    device_info = audio.get_device_info_by_index(i)
                    device_name: str = device_info["name"]
                    if "USB" in device_name:  # 名前に USB を含むデバイスならストリームを作成
                        mic_stream = audio.open(format=FORMAT,
                                                channels=channels,
                                                rate=RATE,
                                                input=True,
                                                frames_per_buffer=self.CHUNK, input_device_index=i)
                        print(
                            f"mic stream created with {device_info}")
                        mic_channels = channels
                        break
                except:
                    pass
        if mic_stream == None:
            print("[WARN] creating mic_stream failed")

        # サーバに接続
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.connect((self.SERVER_HOST, self.SERVER_PORT))
                # サーバにオーディオプロパティを送信
                data = "{},{},{},{},{}".format(
                    FORMAT, self.CHANNELS, RATE, self.CHUNK, DUMMY_BYTES).encode('utf-8')
                print(f"send:{data}")
                sock.send(data)

                # メインループ
                while True:
                    # 音楽ファイルからデータ読み込み
                    if wav_file != None:
                        wav_data = wav_file.readframes(self.CHUNK)
                        # 音楽ファイルリピート再生処理
                        if wav_data == b'':
                            wav_file.rewind()
                            wav_data = wav_file.readframes(self.CHUNK)
                    if mic_stream != None:  # マイクストリーム読み込み
                        mic_data = mic_stream.read(self.CHUNK)
                    # サーバに音データを送信
                    # ダミーの数値データ 数字1つで2バイト
                    # 今回チャンクから4バイト引いているので 2つまで送れるはず
                    # さて、なぜか送信するのはself.CHUNKの4倍量。サーバ側プログラムで対処。
                    # dummy = np.array(
                    #     [10*(i + 1) for i in range(DUMMY_BYTES//2)], np.int16)
                    dummy = np.array(
                        [self.gps.lat, self.gps.lon, self.gps.alt], DUMMY_BYTE_TYPE)
                    if wav_file == None and mic_stream == None:  # どちらもない場合は空の音楽データを送信
                        data = self.mix_sound(
                            self.CHUNK, b"", 1, self.CHANNELS)
                    else:
                        if wav_file != None and mic_stream == None:  # マイクがなく、wavがある場合はwavをそのまま送信
                            data = self.mix_sound(
                                self.CHUNK, wav_data, 1, self.CHANNELS)
                        if wav_file == None and mic_stream != None:  # wavがなくマイクがある場合はマイクをそのまま送信
                            data = self.mix_sound(
                                self.CHUNK, mic_data, 1, mic_channels)
                        if wav_file != None and mic_stream != None:  # どちらもある場合はミックスして送信
                            data = self.mix_sound(
                                self.CHUNK, wav_data, 0.5, self.CHANNELS, mic_data, 0.5, mic_channels)
                        # print(f"dummy:{dummy} data:{data[0:8]}")

                    # data = np.append(dummy, data)
                    # if mic_stream == None:
                    #     print(
                    #         f"wav:{len(wav_data)}, data:{len(data.tobytes())}")
                    # else:
                    #     print(
                    #         f"wav:{len(wav_data)}, mic:{len(mic_data)}, data:{len(data.tobytes())}")
                    sock.send(dummy.tobytes()+data.tobytes())
            except ConnectionRefusedError:
                print(
                    f"Connection with {self.SERVER_HOST}:{self.SERVER_PORT} was refused.")
            except ConnectionAbortedError:
                print(
                    f"Connection with {self.SERVER_HOST}:{self.SERVER_PORT} aborted.")

    # 2つの音データを1つの音データにミックス 1つしか渡されない場合は単にデコードする

    def mix_sound(self, frames_per_buffer, data1, volume1, channels1, data2=None, volume2=0, channels2=1):
        # 音量チェック
        if volume1 + volume2 > 1.0:
            return None
        # 出力チャンネル数の決定
        out_channels = max(channels1, channels2, self.CHANNELS)

        # デコード
        decoded_data1: np.ndarray = np.frombuffer(data1, np.int16).copy()
        # データサイズの不足分を0埋め
        decoded_data1.resize(channels1 * frames_per_buffer, refcheck=False)
        if channels1 < out_channels:
            decoded_data1 = self.mono2stereo(decoded_data1)
        if data2 != None:
            decoded_data2: np.ndarray = np.frombuffer(data2, np.int16).copy()
            decoded_data2.resize(channels2 * frames_per_buffer, refcheck=False)
            if channels2 < out_channels:
                decoded_data2 = self.mono2stereo(decoded_data2)
            return (decoded_data1 * volume1 + decoded_data2 * volume2).astype(np.int16)
        return (decoded_data1 * volume1).astype(np.int16)

    def mono2stereo(self, data: np.ndarray):
        output_data = np.zeros((2, self.CHUNK))
        output_data[0] = data
        output_data[1] = data
        output_data = np.reshape(output_data.T, (self.CHUNK * 2))
        return output_data.astype(np.int16)

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
