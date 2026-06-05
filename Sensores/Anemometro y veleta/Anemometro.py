# ============================================================
# ANEMÓMETRO - SparkFun SEN-15901
# Verde → GPIO32  |  Negro → GND  |  Rojo → 3.3V
# ============================================================
from machine import Pin
import utime

PIN          = 32
INTERVALO_MS = 5000
FACTOR_KMH   = 2.4   # km/h por pulso/segundo (SparkFun oficial)

_pulsos = 0

sensor = Pin(PIN, Pin.IN, Pin.PULL_UP)

def _irq(pin):
    global _pulsos
    _pulsos += 1

sensor.irq(trigger=Pin.IRQ_FALLING, handler=_irq)

t0 = utime.ticks_ms()

while True:
    utime.sleep_ms(50)

    if utime.ticks_diff(utime.ticks_ms(), t0) >= INTERVALO_MS:
        elapsed = utime.ticks_diff(utime.ticks_ms(), t0)

        sensor.irq(handler=None)
        p       = _pulsos
        _pulsos = 0
        sensor.irq(trigger=Pin.IRQ_FALLING, handler=_irq)

        t0  = utime.ticks_ms()
        pps = p / (elapsed / 1000.0)
        kmh = pps * FACTOR_KMH
        mph = kmh * 0.621371
        ms  = kmh / 3.6

        print(f"Pulsos: {p:3d}  |  {pps:.2f} p/s  |  {kmh:.1f} km/h  |  {mph:.1f} mph  |  {ms:.2f} m/s")
