import pyaudio  # 録音機能を使うためのライブラリ

# オーディオデバイスの情報を取得、マイクのインデックス番号を入手する。
iAudio = pyaudio.PyAudio()
for x in range(0, iAudio.get_device_count()):
    print(iAudio.get_device_info_by_index(x))
