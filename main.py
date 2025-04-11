import dht
import machine
import ssd1306
import ntptime
import network
import utime
import uasyncio

import micropython_ota
from button_click_handler import ButtonClickHandler

from env import variables

sta_if = network.WLAN(network.WLAN.IF_STA)

d = dht.DHT22(machine.Pin(2))

red = machine.Pin(5, machine.Pin.OUT)
yellow = machine.Pin(21, machine.Pin.OUT)
green = machine.Pin(6, machine.Pin.OUT)

prev_led = None

morning = variables['MORNING']  # eg 8 for 8AM
night = variables['NIGHT']  # eg 20 for 8PM


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


def connect_to_wifi():
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
            utime.sleep(1)
        print('network info:', sta_if.ifconfig())
    except Exception as e:
        print(f"Failed to connect to internet: {e}")


def disconnect_from_wifi():
    # Close wifi connection
    sta_if.active(False)


def check_for_updates():
    # Check the nginx server for new version of env.py and main.py files
    ota_host = variables['OTA_HOST']
    project_name = variables['OTA_PROJECT_NAME']
    filenames = ['env.py', 'main.py']

    micropython_ota.ota_update(ota_host, project_name, filenames,
                               use_version_prefix=False,
                               hard_reset_device=True,
                               soft_reset_device=False, timeout=5)


def button_clicked(time_held_ms):
    """Sets needs_feeding to False if button clicked"""
    global schedule
    schedule.reset_food_days_counter()


class Schedule():
    def __init__(self):
        self.sync_time()
        self.start_time = self.get_time_hour()

        # Whether target humidity was achieved after mode changed
        self._target_humidity_achieved = False

        self.days_since_fed = variables['CHANGE_FOOD_DAYS']

        self.update()

    def set_target_humidity_achieved(self):
        self._target_humidity_achieved = True

    def is_target_humidity_achieved(self):
        return self._target_humidity_achieved

    def needs_food(self):
        return self.days_since_fed >= variables['CHANGE_FOOD_DAYS']

    def reset_food_days_counter(self):
        self.days_since_fed = 0
        prev_led.value(1)

    def update(self):
        current_mode = ("AM" if self.start_time >= morning and
                        self.start_time < night else "PM")

        # Set inital mode and return it
        if not hasattr(self, 'mode'):
            self.mode = current_mode
            return

        # If the mode is to be changed
        if self.mode != current_mode:
            self.mode = current_mode
            self._target_humidity_achieved = False
            self.days_since_fed += 0.5

    def sync_time(self):
        # Sync time
        try:
            print("Synchronizing time with NTP...")
            ntptime.settime()  # Synchronize with NTP server
            print("Time synchronized!")
        except Exception as e:
            print(f"Failed to sync time: {e}")

    def get_time_hour(self):
        current_time = utime.localtime()
        return current_time[3]

    def get_time_minutes(self):
        current_time = utime.localtime()
        return current_time[4]


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


async def blink_led():
    global prev_led
    while True:
        prev_led.value(0 if prev_led.value() else 1)
        await uasyncio.sleep(0.5)


async def main():
    """
        Contains the main loop and initialization code.
    """
    connect_to_wifi()

    # Check for updates on boot using micropython-ota
    check_for_updates()

    global schedule
    schedule = Schedule()

    disconnect_from_wifi()

    display = Display()

    # Setup button click handler
    ButtonClickHandler(7, button_clicked)

    blink_led_task = None

    while True:
        # Sleep for 5s. Decrease sleep to 100ms if target humidity is not met.
        sleep_time = 5 if schedule.is_target_humidity_achieved() else 0.1

        d.measure()
        temp = d.temperature()
        humidity = d.humidity()

        output = f"Temperature: {temp}°C, Humidity: {humidity}%"

        print(output)
        display.reset()
        display.add_text(f"{temp}c", 7)
        display.add_text(f"{humidity}%", 41)
        display.show()

        schedule.update()

        if not schedule.is_target_humidity_achieved():
            if schedule.mode == "AM":
                green_bounds = 70
                yellow_bounds = 60
            else:
                green_bounds = 80
                yellow_bounds = 70

            if (humidity >= green_bounds):
                change_led_color(green)
                schedule.set_target_humidity_achieved()
            elif (humidity >= yellow_bounds):
                change_led_color(yellow)
            elif (humidity < yellow_bounds):
                change_led_color(red)

        if schedule.needs_food() and blink_led_task is None:
            blink_led_task = uasyncio.create_task(blink_led())

        if not schedule.needs_food() and blink_led_task is not None:
            prev_led.value(1)
            blink_led_task.cancel()
            blink_led_task = None

        # Update every 100ms until target achieved, otherwise update every 5s
        await uasyncio.sleep(sleep_time)


# Starts the main thread
uasyncio.run(main())
