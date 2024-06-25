import dht
import machine
import time

d = dht.DHT11(machine.Pin(4))
d = dht.DHT22(machine.Pin(4))

red = machine.Pin(3, machine.Pin.OUT)
green = machine.Pin(2, machine.Pin.OUT)
white = machine.Pin(1, machine.Pin.OUT)

prev_led = None


def change_led_color(led):
    global prev_led
    if prev_led is not None:
        if prev_led is led:
            return
        else:
            prev_led.value(0)

    if led is red:
        red.value(1)
    elif led is green:
        green.value(1)
    elif led is white:
        white.value(1)

    prev_led = led


while True:
    d.measure()
    temp = d.temperature()
    humidity = d.humidity()

    print(f"Temperature: {temp}°C, Humidity: {humidity}%")

    if (humidity >= 70):
        change_led_color(green)
    elif (humidity >= 60):
        change_led_color(white)
    elif (humidity < 60):
        change_led_color(red)

    time.sleep(5)
