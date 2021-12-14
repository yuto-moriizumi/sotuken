###############################################################################
# GY-271/QMC5883L
# (C) 2021, JarutEx
# Ref: https://github.com/e-Gizmo/QMC5883L-GY-271-Compass-module
###############################################################################
import machine as mc
import sys
import math
from time import sleep  # import sleep

pinSDA = mc.Pin(4)
pinSCL = mc.Pin(5)
QMC5883L_ADDR = 0x0D
i2c = mc.I2C(freq=2000000, scl=pinSCL, sda=pinSDA)
devices = i2c.scan()
if not (QMC5883L_ADDR in devices):
    print("Not found GY-271 (QMC5883L)!")
    sys.exit(1)

# Register Location
RegCTRL1 = 0x09  # Control Register--> MSB(OSR:2,RNG:2,ODR:2,MODE:2)LSB
# Control Register2--> MSB(Soft_RS:1,Rol_PNT:1,none:5,INT_ENB:1)LSB
RegCTRL2 = 0x0A
RegFBR = 0x0B  # SET/RESET Period Register--> MSB(FBR:8)LSB
RegXLo = 0x00
RegXHi = 0x01
RegYLo = 0x02
RegYHi = 0x03
RegZLo = 0x04
RegZHi = 0x05

# Cpntrol Register Value
Mode_Standby = 0b00000000
Mode_Continuous = 0b00000001
ODR_10Hz = 0b00000000
ODR_50Hz = 0b00000100
ODR_100Hz = 0b00001000
ODR_200Hz = 0b00001100
RNG_2G = 0b00000000
RNG_8G = 0b00010000
OSR_512 = 0b00000000
OSR_256 = 0b01000000
OSR_128 = 0b10000000
OSR_64 = 0b11000000

declinationAngle = 0.0404
pi = 3.14159265359

# Init
ctrl1 = bytearray([Mode_Continuous | ODR_200Hz | RNG_8G | OSR_512])
i2c.writeto_mem(QMC5883L_ADDR, RegCTRL1, ctrl1)
i2c.writeto_mem(QMC5883L_ADDR, RegFBR, b'\x01')

# Read
buffer = i2c.readfrom_mem(QMC5883L_ADDR, RegXLo, 6)
xLo = buffer[0]
xHi = buffer[1] << 8
yLo = buffer[2]
yHi = buffer[3] << 8
zLo = buffer[4]
zHi = buffer[5] << 8
x = xLo+xHi
y = yLo+yHi
z = zLo+zHi

# Convert
heading = math.atan2(y, x)
heading = heading + declinationAngle
# Due to declination check for >360 degree
if(heading > 2*pi):
    heading = heading - 2*pi
# check for sign
if(heading < 0):
    heading = heading + 2*pi

# convert into angle
headingAngle = (heading * 180/pi)

# Show result
print("3-axis : x={}/{},{} y={}/{},{} z={}/{},{}".format(x,
      xHi, xLo, y, yHi, yLo, z, zHi, zLo))
print("Heading Angle = {}°".format(headingAngle))
