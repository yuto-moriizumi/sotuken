# wav, マイク, (gps:未実装)の配信クライアント
# wavファイルのみの配信と、wav+マイクの配信に対応

from .GPS import GPS
import math
import numpy as np
import wave
import pyaudio
import socket
import threading


DUMMY_BYTE_TYPE = np.float64


class MixedSoundStreamClient(threading.Thread):
    USE_WAV = False
    CHUNK = 4096  # 1度の送信で音声情報を何バイト送るか (なぜか指定数値の4倍量が送られる)
    # → 512バイト/2バイト*8ビット→ 4倍量 になってると思われる
    CHANNELS = 2

    def __init__(self, server_host, server_port, wav_filename, gps: GPS):
        threading.Thread.__init__(self)
        self.SERVER_HOST = server_host
        self.SERVER_PORT = int(server_port)
        self.WAV_FILENAME = wav_filename
        self.gps = gps

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
                    if "USB" in device_name or "Voice" in device_name:  # 名前に USB または Voice を含むデバイスならストリームを作成
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
                    print(f"dymmy:{dummy} data:{data[0:8]}")

                # data = np.append(dummy, data)
                # if mic_stream == None:
                #     print(
                #         f"wav:{len(wav_data)}, data:{len(data.tobytes())}")
                # else:
                #     print(
                #         f"wav:{len(wav_data)}, mic:{len(mic_data)}, data:{len(data.tobytes())}")
                sock.send(dummy.tobytes()+data.tobytes())

        # 終了処理
        mic_stream.stop_stream()
        mic_stream.close()
        audio.terminate()

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


class MixedSoundStreamServer(threading.Thread):

    def __init__(self, server_host, server_port, gps: GPS):
        threading.Thread.__init__(self)
        self.SERVER_HOST = server_host
        self.SERVER_PORT = int(server_port)
        self.gps = gps

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
                # print(
                #     f"recv:{len(chunk)} bytes, dummy:{np.frombuffer(dummy, DUMMY_BYTE_TYPE)}")
                # print(np.frombuffer(chunk, np.int16)[:8])

                # 方向判定
                HIT_ANGLE = 45  # 中心から±何度までの誤差を許容するか
                HIT_RADIUS = 10
                target_lat = dummy[0]
                target_lon = dummy[0]
                my_corce = self.gps.course
                is_hit = self.hit_sector(
                    target_lon, target_lat, my_corce-HIT_ANGLE, my_corce+HIT_ANGLE, HIT_RADIUS)
                # print(
                #    f"is hit? {is_hit}")
                if is_hit:
                    stream.write(sound)  # 再生

    def hit_sector(self, target_x, target_y, start_angle, end_angle, radius):
        dx = target_x - self.gps.lon
        dy = target_y - self.gps.lat
        sx = math.cos(math.radians(start_angle))
        sy = math.sin(math.radians(start_angle))
        ex = math.cos(math.radians(end_angle))
        ey = math.sin(math.radians(end_angle))

        # 円の内外判定
        if dx ** 2 + dy ** 2 > radius ** 2:
            return False

        # 扇型の角度が180を超えているか
        if sx * ey - ex * sy > 0:
            # 開始角に対して左にあるか
            if sx * dy - dx * sy < 0:
                return False
            # 終了角に対して右にあるか
            if ex * dy - dx * ey > 0:
                return False
            # 扇型の内部にあることがわかった
            return True
        else:
            # 開始角に対して左にあるか
            if sx * dy - dx * sy >= 0:
                return True
            # 終了角に対して右にあるか
            if ex * dy - dx * ey <= 0:
                return True
            # 扇型の外部にあることがわかった
            return False
