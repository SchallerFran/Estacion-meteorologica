# Guía completa: conexión y uso del sensor BME280 con ESP32 en MicroPython

## Introducción

El sensor BME280 es un módulo ambiental fabricado por Bosch capaz de medir:

* Temperatura
* Humedad relativa
* Presión atmosférica

Es muy utilizado en proyectos de:

* estaciones meteorológicas
* IoT
* monitoreo ambiental
* domótica
* adquisición de datos climáticos

El BME280 puede comunicarse mediante:

* I2C
* SPI

En esta guía se utiliza comunicación I2C con un ESP32 y MicroPython.

---

# Materiales utilizados

* ESP32 clásico
* Sensor BME280
* Cables Dupont
* MicroPython instalado en el ESP32

Opcional:

* Conversor de nivel lógico

---

# Conceptos importantes aprendidos

## El ESP32 trabaja a 3.3V

Los pines GPIO del ESP32 funcionan con lógica de 3.3V.

Esto significa que:

* una señal de 5V puede dañarlo
* sensores de 3.3V son compatibles directamente

---

## El BME280 también trabaja a 3.3V

El chip original del BME280 funciona internamente a:

* 1.8V a 3.6V

Por eso normalmente NO es necesario utilizar un conversor de nivel lógico con un ESP32.

---

# ¿Para qué sirve un conversor de nivel lógico?

El conversor de nivel lógico se utiliza para conectar dispositivos que trabajan con diferentes voltajes.

Ejemplo:

| Dispositivo | Voltaje lógico |
| ----------- | -------------- |
| Arduino UNO | 5V             |
| ESP32       | 3.3V           |

En ese caso el conversor protege al ESP32.

Sin embargo:

| Dispositivo | Voltaje lógico |
| ----------- | -------------- |
| ESP32       | 3.3V           |
| BME280      | 3.3V           |

No hace falta conversión.

Incluso el conversor puede generar problemas en el bus I2C si está mal conectado.

---

# Pines I2C utilizados en el ESP32

Los pines más comunes para I2C en un ESP32 clásico son:

| Señal | GPIO   |
| ----- | ------ |
| SDA   | GPIO21 |
| SCL   | GPIO22 |

---

# Conexión correcta del BME280

## Conexión directa recomendada

| BME280 | ESP32  |
| ------ | ------ |
| VCC    | 3.3V   |
| GND    | GND    |
| SDA    | GPIO21 |
| SCL    | GPIO22 |

---

# Problemas encontrados durante la conexión

## El sensor no aparecía en el escaneo I2C

Inicialmente el ESP32 mostraba:

```text
No se encontraron dispositivos I2C
```

Esto puede ocurrir por:

* SDA y SCL invertidos
* alimentación incorrecta
* conversor de nivel mal conectado
* módulo defectuoso
* configuración SPI accidental

---

# Solución encontrada

Se eliminó el conversor de nivel lógico y se conectó el BME280 directamente al ESP32.

Luego el escaneo I2C detectó correctamente el sensor:

```text
Dispositivos encontrados:
Direccion hexadecimal: 0x76
Posible BME280/BMP280 en 0x76
```

---

# Qué significa la dirección 0x76

Los dispositivos I2C poseen una dirección hexadecimal única.

En el caso del BME280 las más comunes son:

| Dirección | Significado           |
| --------- | --------------------- |
| 0x76      | Dirección típica      |
| 0x77      | Dirección alternativa |

El escaneo confirmó que el sensor estaba funcionando correctamente.

---

# Código de prueba para escanear I2C

```python
from machine import Pin, I2C
import time

i2c = I2C(
    0,
    scl=Pin(22),
    sda=Pin(21),
    freq=100000
)

print("Escaneando dispositivos I2C...\n")

while True:
    dispositivos = i2c.scan()

    if dispositivos:
        print("Dispositivos encontrados:")

        for d in dispositivos:
            print("Direccion hexadecimal:", hex(d))

            if d == 0x76:
                print("Posible BME280/BMP280 en 0x76")

            elif d == 0x77:
                print("Posible BME280/BMP280 en 0x77")

    else:
        print("No se encontraron dispositivos I2C")

    print("-----------------------------")
    time.sleep(3)
```

---

# Código completo para leer temperatura, humedad y presión

```python
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
```

---

# Resultado esperado

El ESP32 debería mostrar datos similares a:

```text
Temperatura: 24.6 C
Humedad: 45.3 %
Presion: 948.7 hPa
```

---

# Aplicaciones posibles

Con este sensor funcionando se pueden desarrollar:

* estaciones meteorológicas
* monitoreo ambiental
* registro climático
* medición de confort térmico
* servidores web IoT
* dashboards en tiempo real
* almacenamiento en microSD
* envío de datos por WiFi
* integración con MQTT
* sistemas de alerta climática

---

# Conclusión

El BME280 es un sensor muy completo y sencillo de utilizar con ESP32.

Los puntos más importantes aprendidos fueron:

* el ESP32 utiliza lógica de 3.3V
* el BME280 normalmente también trabaja a 3.3V
* el conversor de nivel lógico no era necesario
* la comunicación I2C utiliza SDA y SCL
* el escaneo I2C permite detectar dispositivos conectados
* la dirección detectada fue 0x76
* MicroPython permite implementar rápidamente sistemas de monitoreo ambiental
