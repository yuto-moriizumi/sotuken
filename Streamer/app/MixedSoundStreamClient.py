from app.AudioPropery import AudioProperty
from app.WaveStream import WaveStream
from app.MicStream import MicStream
from .GPS import GPS
import numpy as np
import socket
from threading import Thread


DUMMY_BYTE_TYPE = np.float64


class MixedSoundStreamClient(Thread):
    USE_WAV = False

    def __init__(self, server_host, server_port, wav_filename, gps: GPS, mic_stream: MicStream, audio_property: AudioProperty):
        Thread.__init__(self)
        self.SERVER_HOST = server_host
        self.SERVER_PORT = int(server_port)
        self.WAV_FILENAME = wav_filename
        self.gps = gps
        self.daemon = True
        self.name = "MixedSoundStreamClient"
        self.mic_stream = mic_stream
        self.audio_property = audio_property

    def run(self):
        # 音楽ファイル読み込み
        wave_stream = WaveStream(
            self.WAV_FILENAME, True) if self.USE_WAV else None

        DUMMY_BITS_PER_NUMBER = 64
        # 何バイトのダミーバイトを先頭に含むか 2バイトで数字1つ送れる
        DUMMY_BYTES = 3*(DUMMY_BITS_PER_NUMBER//8)

        # サーバに接続
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.connect((self.SERVER_HOST, self.SERVER_PORT))
                # サーバにオーディオプロパティを送信
                data = "{},{},{},{},{}".format(
                    self.audio_property.format, self.audio_property.channels, self.audio_property.rate, self.audio_property.chunk, DUMMY_BYTES).encode('utf-8')
                print(f"send:{data}")
                sock.send(data)
                # メインループ
                while True:
                    # 音楽ファイルからデータ読み込み
                    if wave_stream != None:
                        wav_data = wave_stream.read(self.audio_property.chunk)
                    if self.mic_stream != None:  # マイクストリーム読み込み
                        mic_data = self.mic_stream.stream.read(
                            self.audio_property.chunk)
                    # サーバに音データを送信
                    # ダミーの数値データ 数字1つで2バイト
                    # 今回チャンクから4バイト引いているので 2つまで送れるはず
                    # さて、なぜか送信するのはself.audio_property.chunkの4倍量。サーバ側プログラムで対処。
                    # dummy = np.array(
                    #     [10*(i + 1) for i in range(DUMMY_BYTES//2)], np.int16)
                    dummy = np.array(
                        [self.gps.lat, self.gps.lon, self.gps.alt], DUMMY_BYTE_TYPE)
                    if wave_stream == None and self.mic_stream == None:  # どちらもない場合は空の音楽データを送信
                        data = self.mix_sound(
                            self.audio_property.chunk, b"", 1, self.audio_property.channels)
                    else:
                        if wave_stream != None and self.mic_stream == None:  # マイクがなく、wavがある場合はwavをそのまま送信
                            data = self.mix_sound(
                                self.audio_property.chunk, wav_data, 1, self.audio_property.channels)
                        # self.mic_stream.
                        if wave_stream == None and self.mic_stream != None:  # wavがなくマイクがある場合はマイクをそのまま送信
                            data = self.mix_sound(
                                self.audio_property.chunk, mic_data, 1, self.mic_stream.channel)
                        if wave_stream != None and self.mic_stream != None:  # どちらもある場合はミックスして送信
                            data = self.mix_sound(
                                self.audio_property.chunk, wav_data, 0.5, self.audio_property.channels, mic_data, 0.5, self.mic_stream.channel)
                        # print(f"dummy:{dummy} data:{data[0:8]}")

                    # data = np.append(dummy, data)
                    # if mic_stream == None:
                    #     print(
                    #         f"wav:{len(wav_data)}, data:{len(data.tobytes())}")
                    # else:
                    #     print(
                    #         f"wav:{len(wav_data)}, mic:{len(mic_data)}, data:{len(data.tobytes())}")
                    sock.send(dummy.tobytes()+data.tobytes())
            except TimeoutError:
                print(
                    f"Connection with {self.SERVER_HOST}:{self.SERVER_PORT} was timeout.")
            except ConnectionResetError:
                print(
                    f"Connection with {self.SERVER_HOST}:{self.SERVER_PORT} was reseted.")
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
        out_channels = max(channels1, channels2, self.audio_property.channels)

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
        output_data = np.zeros((2, self.audio_property.chunk))
        output_data[0] = data
        output_data[1] = data
        output_data = np.reshape(
            output_data.T, (self.audio_property.chunk * 2))
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
