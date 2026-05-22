from machine import Pin
import time

# GPIO donde conectás el pluviómetro
PIN_PLUVIO = 14

# Ajustar según tu modelo
MM_POR_PULSO = 0.2794 

pulsos = 0
ultimo_pulso = 0

# Antirrebote
DEBOUNCE_MS = 300

def lluvia(pin):
    global pulsos
    global ultimo_pulso

    ahora = time.ticks_ms()

    if time.ticks_diff(ahora, ultimo_pulso) > DEBOUNCE_MS:
        pulsos += 1
        ultimo_pulso = ahora

# Configuración del pin
sensor = Pin(PIN_PLUVIO, Pin.IN, Pin.PULL_UP)

# Interrupción
sensor.irq(trigger=Pin.IRQ_FALLING, handler=lluvia)

print("Pluviometro listo")

while True:

    mm = pulsos * MM_POR_PULSO

    print("----------------")
    print("Pulsos:", pulsos)
    print("Lluvia acumulada:", round(mm, 2), "mm")

    time.sleep(5)
