import machine, sdcard, os, time

# ─── Montar SD ───────────────────────────────────────────────────
spi = machine.SoftSPI(baudrate=100000, polarity=0, phase=0,
    sck=machine.Pin(18), mosi=machine.Pin(23), miso=machine.Pin(19))

cs = machine.Pin(4, machine.Pin.OUT)
cs.value(1)

sd = sdcard.SDCard(spi, cs)
os.mount(os.VfsFat(sd), "/sd")
print("SD montada ✓")

# ─── Funciones ───────────────────────────────────────────────────
def escribir(ruta, contenido):
    with open(ruta, "w") as f:
        f.write(contenido)
    print("Escrito:", ruta)

def agregar(ruta, contenido):
    with open(ruta, "a") as f:
        f.write(contenido)

def leer(ruta):
    with open(ruta, "r") as f:
        print(f.read())

def listar():
    for item in os.listdir("/sd"):
        stat = os.stat("/sd/" + item)
        print(" ", item, "-", stat[6], "bytes")

# ─── Demo ────────────────────────────────────────────────────────
escribir("/sd/log.txt", "=== Inicio del registro ===\n")

for i in range(5):
    linea = "Muestra {}: tiempo={}ms\n".format(i+1, time.ticks_ms())
    agregar("/sd/log.txt", linea)
    time.sleep(0.5)

leer("/sd/log.txt")
listar()

# ─── Datalogger continuo (cada 10 segundos) ──────────────────────
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
        print("SD desmontada ✓")
        break
