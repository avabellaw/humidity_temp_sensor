import dht
import machine
import time
import ssd1306

d = dht.DHT22(machine.Pin(2))

red = machine.Pin(5, machine.Pin.OUT)
yellow = machine.Pin(21, machine.Pin.OUT)
green = machine.Pin(0, machine.Pin.OUT)

prev_led = None


class Display():
    def __init__(self):
        # Initialize I2C with default pins (SDA=Pin(4), SCL=Pin(5))
        i2c = machine.I2C(sda=machine.Pin(1), scl=machine.Pin(0))

        # Initialize the OLED display
        self.display = ssd1306.SSD1306_I2C(128, 64, i2c)

        # Clear the display
        self.display.fill(0)
        self.display.show()

    def add_text(self, text, y):
        start_x = int((128 - len(text) * 24) / 2)

        if start_x < 0:
            start_x = 0
        self.display.write_text(text, start_x, y, size=3)

    def reset(self):
        self.display.fill(0)

    def show_text(self, text, y):
        self.reset()
        self.add_text(text, y)
        self.show()

    def show(self):
        self.display.show()


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
    elif led is yellow:
        yellow.value(1)

    prev_led = led


display = Display()


while True:
    d.measure()
    temp = d.temperature()
    humidity = d.humidity()

    output = f"Temperature: {temp}°C, Humidity: {humidity}%"

    print(output)
    display.reset()
    display.add_text(f"{temp}c", 7)
    display.add_text(f"{humidity}%", 41)
    display.show()

    if (humidity >= 70):
        change_led_color(green)
    elif (humidity >= 60):
        change_led_color(yellow)
    elif (humidity < 60):
        change_led_color(red)

    time.sleep(1)
