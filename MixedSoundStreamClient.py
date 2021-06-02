import numpy as np
import wave
import pyaudio
import socket
import threading


class MixedSoundStreamClient(threading.Thread):
    def __init__(self, server_host, server_port, wav_filename):
        threading.Thread.__init__(self)
        self.SERVER_HOST = server_host
        self.SERVER_PORT = int(server_port)
        self.WAV_FILENAME = wav_filename

    def run(self):
        audio = pyaudio.PyAudio()

        # 音楽ファイル読み込み
        wav_file = wave.open(self.WAV_FILENAME, 'rb')

        # オーディオプロパティ
        FORMAT = pyaudio.paInt16
        CHANNELS = wav_file.getnchannels()
        RATE = wav_file.getframerate()
        DUMMY_BYTES = 2  # 何バイトのダミーバイトを先頭に含むか
        CHUNK = 1024  # 1度の送信で音声情報を何バイト送るか

        # マイクの入力ストリーム生成
        mic_stream = None
        index = 2
        while True:
            try:
                mic_stream = audio.open(format=FORMAT,
                                        channels=CHANNELS,
                                        rate=RATE,
                                        input=True,
                                        frames_per_buffer=CHUNK, input_device_index=index)  # ここのインデックスはsearchMic.pyで調べる
                print(f"mic stream created with {index}")
                break
            except:
                index += 1

        # サーバに接続
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((self.SERVER_HOST, self.SERVER_PORT))

            # サーバにオーディオプロパティを送信
            data = "{},{},{},{},{}".format(
                FORMAT, CHANNELS, RATE, CHUNK, DUMMY_BYTES).encode('utf-8')
            print(f"send:{data}")
            sock.send(data)

            # メインループ
            while True:
                # 音楽ファイルとマイクからデータ読み込み
                wav_data = wav_file.readframes(CHUNK)
                mic_data = mic_stream.read(CHUNK)

                # 音楽ファイルリピート再生処理
                if wav_data == b'':
                    wav_file.rewind()
                    wav_data = wav_file.readframes(CHUNK)

                # サーバに音データを送信
                # ダミーの数値データ 数字1つで2バイト
                # 今回チャンクから4バイト引いているので 2つまで送れるはず
                # さて、なぜか送信するのはCHUNKの4倍量。サーバ側プログラムで対処。
                dummy = np.array(
                    [10*(i + 1) for i in range(DUMMY_BYTES//2)], np.int16)
                data = self.mix_sound(
                    wav_data, mic_data, CHANNELS, CHUNK, 0.5, 0.5)
                data = np.append(dummy, data)
                print(
                    f"wav:{len(wav_data)}, mic:{len(mic_data)}, data:{len(data.tobytes())}")
                print(f"send:{data[0:8]}")
                sock.send(data.tobytes())

        # 終了処理
        mic_stream.stop_stream()
        mic_stream.close()

        audio.terminate()

    # 2つの音データを1つの音データにミックス
    def mix_sound(self, data1, data2, channels, frames_per_buffer, volume1, volume2):
        # 音量チェック
        if volume1 + volume2 > 1.0:
            return None
        # デコード
        decoded_data1 = np.frombuffer(data1, np.int16).copy()
        decoded_data2 = np.frombuffer(data2, np.int16).copy()
        # データサイズの不足分を0埋め
        decoded_data1.resize(channels * frames_per_buffer, refcheck=False)
        decoded_data2.resize(channels * frames_per_buffer, refcheck=False)
        # 音量調整 & エンコード
        return (decoded_data1 * volume1 + decoded_data2 * volume2).astype(np.int16)


if __name__ == '__main__':
    mss_client = MixedSoundStreamClient("192.168.0.8", 12345, "sample.wav")
    mss_client.start()
    mss_client.join()
