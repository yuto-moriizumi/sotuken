from pyproj import Transformer
import pyproj
lat = 35.679933
lon = 139.714465
lon2 = 139.814465

EPSG4612 = pyproj.Proj("EPSG:4326")
EPSG2451 = pyproj.Proj("EPSG:6676")
x, y = pyproj.transform(EPSG4612, EPSG2451, lon, lat, always_xy=True)

print("x = ", x)
print("y = ", y)

toSquare = Transformer.from_crs("epsg:4326", "epsg:6676")
y, x = toSquare.transform(lat, lon)
y2, x2 = toSquare.transform(lat, lon2)
print(x, y, x2, y2)
