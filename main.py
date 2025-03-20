import os
import dht
import machine
import time
import ssd1306
import ntptime
import network
import utime

from env import variables

sta_if = network.WLAN(network.WLAN.IF_STA)

d = dht.DHT22(machine.Pin(2))

red = machine.Pin(5, machine.Pin.OUT)
yellow = machine.Pin(21, machine.Pin.OUT)
green = machine.Pin(0, machine.Pin.OUT)

prev_led = None

morning = 8  # 8AM
night = 22  # 10PM


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


class Schedule():
    def __init__(self):
        self.sync_time()
        self.start_time = self.get_time_hour()

        if self.start_time >= morning and self.start_time < night:
            self.mode = "AM"
        else:
            self.mode = "PM"

        self.mode_changed = True

    def sync_time(self):
        # Connect to wifi
        try:
            sta_if.active(True)
            ssid = variables['SSID']
            password = variables['PASS']
            if ssid is None or password is None:
                raise Exception(("Create env.py with a dict 'variables'"
                                 "containing SSID & PASS for Wifi."))
            sta_if.connect(variables['SSID'], variables['PASS'])
            while not sta_if.isconnected():
                print("connecting...")
                time.sleep(1)
            print('network info:', sta_if.ifconfig())
        except Exception as e:
            print(f"Failed to connect to internet: {e}")

        # Sync time
        try:
            print("Synchronizing time with NTP...")
            ntptime.settime()  # Synchronize with NTP server
            print("Time synchronized!")
        except Exception as e:
            print(f"Failed to sync time: {e}")

        # Close wifi connection
        sta_if.active(False)

    def get_time_hour(self):
        current_time = utime.localtime()
        return current_time[3]


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


schedule = Schedule()

display = Display()

sleep_length = 100

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

    time.sleep(sleep_length)
