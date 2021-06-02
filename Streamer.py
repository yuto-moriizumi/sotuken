# wav, マイク, (gps:未実装)の配信クライアント
# wavファイルのみの配信と、wav+マイクの配信に対応

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
        CHUNK = 512  # 1度の送信で音声情報を何バイト送るか (なぜか指定数値の4倍量が送られる)

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
            while True:
                # 音楽ファイルからデータ読み込み
                wav_data = wav_file.readframes(CHUNK)
                if mic_stream != None:  # マイクストリーム読み込み
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
                if mic_stream == None:  # マイクがない場合はwavファイルをそのまま送信
                    data = self.mix_sound(
                        CHANNELS, CHUNK, wav_data, 1)
                else:  # マイクがある場合はミックスして送信
                    data = self.mix_sound(
                        CHANNELS, CHUNK, wav_data, 0.5, mic_data, 0.5)
                data = np.append(dummy, data)
                if mic_stream == None:
                    print(
                        f"wav:{len(wav_data)}, data:{len(data.tobytes())}")
                else:
                    print(
                        f"wav:{len(wav_data)}, mic:{len(mic_data)}, data:{len(data.tobytes())}")
                print(f"send:{data[0:8]}")
                sock.send(data.tobytes())

        # 終了処理
        mic_stream.stop_stream()
        mic_stream.close()
        audio.terminate()

    # 2つの音データを1つの音データにミックス 1つしか渡されない場合は単にデコードする
    def mix_sound(self,  channels, frames_per_buffer, data1, volume1, data2=None, volume2=0):
        print(volume1, volume2)
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


if __name__ == '__main__':
    mss_client = MixedSoundStreamClient("192.168.0.8", 12345, "sample.wav")
    mss_client.start()
    mss_client.join()
