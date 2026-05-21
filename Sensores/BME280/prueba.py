from machine import Pin, I2C
import time

# =========================
# CONFIGURACION I2C
# =========================

i2c = I2C(
    0,
    scl=Pin(22),
    sda=Pin(21),
    freq=100000
)

# =========================
# CLASE BME280
# =========================

class BME280:

    def __init__(self, i2c, address=0x76):

        self.i2c = i2c
        self.address = address

        self.dig_T1 = self.readU16LE(0x88)
        self.dig_T2 = self.readS16LE(0x8A)
        self.dig_T3 = self.readS16LE(0x8C)

        self.dig_P1 = self.readU16LE(0x8E)
        self.dig_P2 = self.readS16LE(0x90)
        self.dig_P3 = self.readS16LE(0x92)
        self.dig_P4 = self.readS16LE(0x94)
        self.dig_P5 = self.readS16LE(0x96)
        self.dig_P6 = self.readS16LE(0x98)
        self.dig_P7 = self.readS16LE(0x9A)
        self.dig_P8 = self.readS16LE(0x9C)
        self.dig_P9 = self.readS16LE(0x9E)

        self.dig_H1 = self.readU8(0xA1)
        self.dig_H2 = self.readS16LE(0xE1)
        self.dig_H3 = self.readU8(0xE3)

        e4 = self.readU8(0xE4)
        e5 = self.readU8(0xE5)
        e6 = self.readU8(0xE6)

        self.dig_H4 = (e4 << 4) | (e5 & 0x0F)
        self.dig_H5 = (e6 << 4) | (e5 >> 4)
        self.dig_H6 = self.readS8(0xE7)

        self.i2c.writeto_mem(self.address, 0xF2, b'\x01')
        self.i2c.writeto_mem(self.address, 0xF4, b'\x27')

        self.t_fine = 0

    def readU8(self, reg):
        return self.i2c.readfrom_mem(self.address, reg, 1)[0]

    def readS8(self, reg):
        result = self.readU8(reg)
        if result > 127:
            result -= 256
        return result

    def readU16LE(self, reg):
        data = self.i2c.readfrom_mem(self.address, reg, 2)
        return data[0] | (data[1] << 8)

    def readS16LE(self, reg):
        result = self.readU16LE(reg)
        if result > 32767:
            result -= 65536
        return result

    def read_raw_temp(self):
        data = self.i2c.readfrom_mem(self.address, 0xFA, 3)
        return ((data[0] << 16) | (data[1] << 8) | data[2]) >> 4

    def read_raw_pressure(self):
        data = self.i2c.readfrom_mem(self.address, 0xF7, 3)
        return ((data[0] << 16) | (data[1] << 8) | data[2]) >> 4

    def read_raw_humidity(self):
        data = self.i2c.readfrom_mem(self.address, 0xFD, 2)
        return (data[0] << 8) | data[1]

    def temperature(self):

        adc = self.read_raw_temp()

        var1 = (((adc >> 3) - (self.dig_T1 << 1)) * self.dig_T2) >> 11
        var2 = (((((adc >> 4) - self.dig_T1) *
                ((adc >> 4) - self.dig_T1)) >> 12) *
                self.dig_T3) >> 14

        self.t_fine = var1 + var2

        T = (self.t_fine * 5 + 128) >> 8

        return T / 100

    def pressure(self):

        self.temperature()

        adc = self.read_raw_pressure()

        var1 = self.t_fine - 128000
        var2 = var1 * var1 * self.dig_P6
        var2 = var2 + ((var1 * self.dig_P5) << 17)
        var2 = var2 + (self.dig_P4 << 35)

        var1 = ((var1 * var1 * self.dig_P3) >> 8) + \
               ((var1 * self.dig_P2) << 12)

        var1 = (((1 << 47) + var1) * self.dig_P1) >> 33

        if var1 == 0:
            return 0

        p = 1048576 - adc
        p = (((p << 31) - var2) * 3125) // var1

        var1 = (self.dig_P9 * (p >> 13) * (p >> 13)) >> 25
        var2 = (self.dig_P8 * p) >> 19

        p = ((p + var1 + var2) >> 8) + (self.dig_P7 << 4)

        return p / 25600

    def humidity(self):

        self.temperature()

        adc = self.read_raw_humidity()

        h = self.t_fine - 76800

        h = (((((adc << 14) - (self.dig_H4 << 20) -
               (self.dig_H5 * h)) + 16384) >> 15) *
             (((((((h * self.dig_H6) >> 10) *
             (((h * self.dig_H3) >> 11) + 32768)) >> 10) +
             2097152) * self.dig_H2 + 8192) >> 14))

        h = h - (((((h >> 15) * (h >> 15)) >> 7) *
             self.dig_H1) >> 4)

        h = max(0, min(h, 419430400))

        return (h >> 12) / 1024

# =========================
# INICIAR SENSOR
# =========================

print("Buscando BME280...")

devices = i2c.scan()

if 0x76 in devices:
    print("BME280 encontrado en 0x76")
elif 0x77 in devices:
    print("BME280 encontrado en 0x77")
else:
    print("No se encontro el BME280")
    raise Exception("Sensor no detectado")

bme = BME280(i2c=i2c, address=0x76)

# =========================
# LOOP PRINCIPAL
# =========================

while True:

    temp = bme.temperature()
    hum = bme.humidity()
    pres = bme.pressure()

    print("Temperatura:", temp, "C")
    print("Humedad:", hum, "%")
    print("Presion:", pres, "hPa")

    print("--------------------------")

    time.sleep(2)
