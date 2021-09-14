from app.GPS import GPS
from app.MixedSoundStreamServer import MixedSoundStreamServer
from app.MixedSoundStreamClient import MixedSoundStreamClient

if __name__ == '__main__':
    gps = GPS()
    gps.start()
    mss_server = MixedSoundStreamServer("localhost", 12345, gps)
    mss_server.start()
    mss_client = MixedSoundStreamClient(
        "192.168.0.4", 12345, "1ch44100Hz.wav", gps)
    mss_client.start()
    mss_client.join()
