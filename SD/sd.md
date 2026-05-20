# Guía: Módulo MicroSD con ESP32 en MicroPython

## Lo que aprendimos en este proceso

Durante la configuración encontramos varios problemas típicos que vale la pena documentar para no repetirlos:

- El **pin GPIO 5** tiene conflictos en el boot del ESP32 y no funciona como CS para la SD
- El **SPI por hardware** puede dar problemas con algunos módulos; SoftSPI es más compatible
- La SD puede estar formateada en **GPT** (no compatible con MicroPython) aunque Windows diga que es FAT32
- La solución al formato GPT es usar **SD Card Formatter**, no el formateador de Windows

---

## Materiales necesarios

- ESP32 (cualquier variante con pines accesibles)
- Módulo MicroSD (6 pines)
- Tarjeta MicroSD (recomendado: 32GB o menos)
- Cables dupont
- PC con Thonny IDE instalado

---

## Conexión de pines

### Tabla de conexiones

| Módulo MicroSD | ESP32 GPIO | Descripción |
|:--------------:|:----------:|:-----------:|
| 3V3 (o VCC)    | 3.3V       | Alimentación |
| GND            | GND        | Tierra |
| CS             | **GPIO 4** | Chip Select ⚠️ |
| MOSI           | GPIO 23    | Datos hacia la SD |
| MISO           | GPIO 19    | Datos desde la SD |
| SCK            | GPIO 18    | Reloj SPI |

> ⚠️ **Importante:** usar **GPIO 4** para CS, no GPIO 5. El GPIO 5 tiene un comportamiento especial durante el arranque del ESP32 que interfiere con la comunicación SPI y genera el error `timeout waiting for v2 card`.

### Diagrama de conexión

```
        ESP32                Módulo MicroSD
       ┌──────┐             ┌─────────────┐
  3.3V │      │────────────▶│ 3V3         │
   GND │      │────────────▶│ GND         │
GPIO 4 │      │────────────▶│ CS          │
GPIO23 │      │────────────▶│ MOSI        │
GPIO19 │      │◀────────────│ MISO        │
GPIO18 │      │────────────▶│ SCK         │
       └──────┘             └─────────────┘
```

> Si tu módulo tiene el pin marcado como **VCC** en lugar de **3V3**, conectalo a **VIN (5V)** del ESP32, no a 3.3V.

---

## Preparar la tarjeta MicroSD

### Formato requerido: FAT32 sin GPT

MicroPython solo soporta FAT32 con tabla de particiones MBR simple. El formateador de Windows puede dejar la tarjeta con partición GPT aunque muestre "FAT32", lo que genera el error `ENODEV` al intentar montar.

### Formatear correctamente con SD Card Formatter

1. Descargá **SD Memory Card Formatter** desde [sdcard.org/downloads/formatter](https://www.sdcard.org/downloads/formatter/) (gratuito, Windows y Mac)
2. Insertá la tarjeta en la PC
3. Seleccioná la tarjeta en el programa
4. Elegí **"Overwrite Format"**
5. Clic en **Format**

> ❌ **No uses** el formateador de Windows ni la opción "Formato rápido/lento": ninguna elimina la tabla GPT.

---

## Instalar el driver sdcard.py

MicroPython no incluye el driver de SD. Hay que subir un archivo extra a la ESP32.

### Pasos con Thonny

1. Descargá [`sdcard.py`](https://raw.githubusercontent.com/micropython/micropython-lib/master/micropython/drivers/storage/sdcard/sdcard.py) desde el repositorio oficial de MicroPython
2. Abrí Thonny y conectá la ESP32
3. En Thonny: **Archivo → Abrir** → seleccioná el `sdcard.py` descargado
4. Luego: **Archivo → Guardar como** → elegí **"MicroPython device"**
5. Guardalo como `sdcard.py`

### Verificar que se subió correctamente

Ejecutá esto en la consola de Thonny:

```python
import os
print(os.listdir())  # debe aparecer 'sdcard.py'
```

---

## Código completo

```python
import machine, sdcard, os, time

# ─── Montar la SD ────────────────────────────────────────────────
# Se usa SoftSPI porque es más compatible que el SPI por hardware
# Se usa GPIO 4 como CS porque GPIO 5 tiene conflictos en el boot

spi = machine.SoftSPI(
    baudrate=100000,
    polarity=0,
    phase=0,
    sck=machine.Pin(18),
    mosi=machine.Pin(23),
    miso=machine.Pin(19)
)

cs = machine.Pin(4, machine.Pin.OUT)
cs.value(1)

sd = sdcard.SDCard(spi, cs)
os.mount(os.VfsFat(sd), "/sd")
print("SD montada ✓")

# ─── Funciones de utilidad ───────────────────────────────────────

def escribir(ruta, contenido):
    """Crea o sobreescribe un archivo."""
    with open(ruta, "w") as f:
        f.write(contenido)
    print("Escrito:", ruta)

def agregar(ruta, contenido):
    """Agrega una línea sin borrar el contenido existente."""
    with open(ruta, "a") as f:
        f.write(contenido)

def leer(ruta):
    """Lee e imprime el contenido de un archivo."""
    with open(ruta, "r") as f:
        print(f.read())

def listar():
    """Lista todos los archivos en la SD."""
    for item in os.listdir("/sd"):
        stat = os.stat("/sd/" + item)
        print(" ", item, "-", stat[6], "bytes")

# ─── Demo de escritura y lectura ─────────────────────────────────

escribir("/sd/log.txt", "=== Inicio del registro ===\n")

for i in range(5):
    linea = "Muestra {}: tiempo={}ms\n".format(i + 1, time.ticks_ms())
    agregar("/sd/log.txt", linea)
    time.sleep(0.5)

leer("/sd/log.txt")
listar()

# ─── Datalogger continuo ─────────────────────────────────────────
# Lee el ADC del GPIO 34 y guarda un registro cada 10 segundos
# Reemplazá adc.read() por tu sensor real si es necesario

print("\nDatalogger iniciado (Ctrl+C para detener)...")
adc = machine.ADC(machine.Pin(34))
adc.atten(machine.ADC.ATTN_11DB)

while True:
    try:
        valor = adc.read()
        linea = "t={}ms | adc={}\n".format(time.ticks_ms(), valor)
        agregar("/sd/log.txt", linea)
        print("Guardado:", linea.strip())
        time.sleep(10)
    except KeyboardInterrupt:
        print("Detenido.")
        os.umount("/sd")
        print("SD desmontada correctamente ✓")
        break
```

---

## Errores comunes y soluciones

| Error | Causa | Solución |
|-------|-------|----------|
| `timeout waiting for v2 card` | Cableado incorrecto o CS en GPIO 5 | Revisá cables, usá GPIO 4 para CS |
| `ENODEV` al montar | Formato GPT o tarjeta no FAT32 | Formatear con SD Card Formatter |
| `ENODEV` después de formatear | SPI por hardware con conflictos | Usar `SoftSPI` en lugar de `SPI` |
| `SDCard object has no attribute X` | Versión vieja de sdcard.py | Descargar versión actualizada del repo oficial |
| `'int' object isn't callable` | Acceso incorrecto a `sd.sectors` | Usar `sd.sectors` sin paréntesis (es propiedad, no método) |

---

## Resumen de lo que funcionó

Luego de varios intentos, la configuración que funcionó fue:

- ✅ **SoftSPI** en lugar de SPI por hardware
- ✅ **GPIO 4** como CS (no GPIO 5)
- ✅ **baudrate=100000** (conservador y estable)
- ✅ Tarjeta formateada con **SD Card Formatter** en modo Overwrite