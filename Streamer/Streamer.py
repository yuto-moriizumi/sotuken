from app.GPS import GPS
from app.MixedSoundStreamServer import MixedSoundStreamServer
from app.MixedSoundStreamClient import MixedSoundStreamClient

if __name__ == '__main__':
    gps = GPS()
    gps.daemon = True
    gps.start()
    mss_server = MixedSoundStreamServer("192.168.0.8", 12345, gps)
    mss_server.daemon = True
    mss_server.start()
    mss_client = MixedSoundStreamClient(
        "192.168.0.4", 12345, "1ch44100Hz.wav", gps)
    mss_client.daemon = True
    mss_client.start()
    mss_client.join()
