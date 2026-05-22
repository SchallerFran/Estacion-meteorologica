# Pluviómetro con ESP32 y MicroPython

## ¿Qué es un pluviómetro?

Un pluviómetro es un instrumento utilizado para medir la cantidad de lluvia caída en un lugar durante un período de tiempo.

Los modelos más comunes en estaciones meteorológicas DIY utilizan un sistema llamado:

- **Pluviómetro basculante**
- o **Tipping Bucket Rain Gauge**

---

# ¿Cómo funciona?

Internamente posee dos pequeñas “cucharas” o recipientes basculantes.

## Funcionamiento físico

1. La lluvia entra por la parte superior.
2. El agua llena una de las cucharas.
3. Cuando alcanza cierto peso:
   - la cuchara se inclina,
   - vacía el agua,
   - la otra cuchara queda lista para llenarse.
4. En ese movimiento:
   - un imán pasa cerca de un reed switch,
   - se genera un pulso eléctrico.

Cada pulso representa una cantidad conocida de lluvia.

Por ejemplo:

| Pulsos | Lluvia |
|---|---|
| 1 | 0.2794 mm |
| 10 | 2.794 mm |
| 100 | 27.94 mm |

---

# Reed Switch

La mayoría de los pluviómetros tienen únicamente:

- 2 cables

porque internamente utilizan un:

- **reed switch**

El reed switch es un interruptor magnético que:

- normalmente está abierto,
- y se cierra momentáneamente cuando pasa un imán cerca.

---

# Conexión al ESP32

## Materiales

- ESP32
- Pluviómetro basculante
- Cable USB
- MicroPython instalado

---

## Cableado

El pluviómetro no necesita alimentación externa.

### Conexión:

| Cable del pluviómetro | ESP32 |
|---|---|
| Cable 1 | GND |
| Cable 2 | GPIO 14 |

También puede usarse cualquier otro GPIO digital.

---

# Esquema básico

```text
PLUVIÓMETRO
   ┌──────────────┐
   │              │
   │ Reed Switch  │
   │              │
   └─────┬───┬────┘
         │   │
         │   │
       GND GPIO14

           ESP32
```

---

# Código en MicroPython

```python
from machine import Pin
import time

# GPIO donde conectás el pluviómetro
PIN_PLUVIO = 14

# Cantidad de mm por pulso
MM_POR_PULSO = 0.2794

pulsos = 0
ultimo_pulso = 0

# Antirrebote
DEBOUNCE_MS = 300

def lluvia(pin):
    global pulsos
    global ultimo_pulso

    ahora = time.ticks_ms()

    # Evita rebotes eléctricos
    if time.ticks_diff(ahora, ultimo_pulso) > DEBOUNCE_MS:
        pulsos += 1
        ultimo_pulso = ahora

# Configuración del pin
sensor = Pin(PIN_PLUVIO, Pin.IN, Pin.PULL_UP)

# Interrupción
sensor.irq(
    trigger=Pin.IRQ_FALLING,
    handler=lluvia
)

print("Pluviometro iniciado")

while True:

    lluvia_mm = pulsos * MM_POR_PULSO

    print("----------------")
    print("Pulsos:", pulsos)
    print("Lluvia acumulada:", round(lluvia_mm, 2), "mm")

    time.sleep(5)
```

---

# Explicación del código

## 1. Configuración del pin

```python
sensor = Pin(PIN_PLUVIO, Pin.IN, Pin.PULL_UP)
```

El pin se configura como:

- entrada digital,
- con resistencia pull-up interna.

Esto mantiene el pin en estado HIGH hasta que el reed switch se cierra.

---

## 2. Interrupciones

```python
sensor.irq(trigger=Pin.IRQ_FALLING, handler=lluvia)
```

El ESP32 detecta automáticamente cuando:

- el reed switch se cierra,
- la señal pasa de HIGH a LOW.

Entonces ejecuta la función:

```python
lluvia()
```

---

## 3. Antirrebote

```python
DEBOUNCE_MS = 300
```

Los contactos mecánicos generan pequeños rebotes eléctricos.

El antirrebote evita contar múltiples pulsos falsos.

---

## 4. Conversión a milímetros

```python
lluvia_mm = pulsos * MM_POR_PULSO
```

Cada pulso equivale a cierta cantidad de lluvia.

Ese valor depende del modelo del pluviómetro.

Valores típicos:

- 0.2 mm
- 0.2794 mm
- 0.5 mm

---

# ¿Cómo probarlo?

## Método 1

Mover manualmente el balancín.

---

## Método 2

Tocar rápidamente los dos cables entre sí.

Cada contacto debería generar un pulso.

---

# Posibles mejoras

Este sistema puede ampliarse para:

- guardar datos en microSD,
- enviar datos por WiFi,
- usar MQTT,
- subir datos a ThingSpeak,
- crear una estación meteorológica completa,
- medir intensidad de lluvia,
- calcular lluvia por hora,
- integrar sensores BME280,
- usar panel solar y batería.

---

# Conceptos importantes aprendidos

## Pull-Up

La resistencia pull-up mantiene el pin en HIGH cuando el interruptor está abierto.

---

## GPIO

Los GPIO son pines digitales del ESP32.

---

## Interrupciones

Permiten detectar eventos instantáneamente sin usar polling constante.

---

## Reed Switch

Interruptor magnético activado por un imán.

---

# Resultado final

El ESP32 puede:

- detectar lluvia,
- contar pulsos,
- calcular precipitación acumulada,
- y servir como base para una estación meteorológica profesional DIY.