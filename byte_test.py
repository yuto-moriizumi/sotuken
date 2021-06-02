import numpy as np

b = np.array([1], np.int16)
print(b, b.tobytes())
b = np.array([-1], np.int16)
print(b, b.tobytes())
b = np.array([-2], np.int16)
print(b, b.tobytes())


b = np.array([1, 2, 3], np.int16)
# 16ビット=2バイト
print(b, b.tobytes())
chunk = b.tobytes()[2:4]
print(chunk)  # 先頭2バイトを取り出す
print(int.from_bytes(chunk, "little"))
