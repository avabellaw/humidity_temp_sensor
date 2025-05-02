import dht
import machine
import ssd1306
import ntptime
import network
import utime
import uasyncio
import urequests

import micropython_ota
from button_click_handler import ButtonClickHandler

from env import variables

sta_if = network.WLAN(network.WLAN.IF_STA)

red = machine.Pin(5, machine.Pin.OUT)
yellow = machine.Pin(21, machine.Pin.OUT)
green = machine.Pin(6, machine.Pin.OUT)

current_led = None

morning = variables['MORNING']  # eg 8 for 8AM
night = variables['NIGHT']  # eg 20 for 8PM

BLYNK_TOKEN = variables['BLYNK_AUTH_TOKEN']
BLYNK_API_URL = (
    f'https://blynk.cloud/external/api/batch/update?token={BLYNK_TOKEN}')


class Sensor:
    """The dht humidity and temperature sensor."""

    def __init__(self, pin):
        self.dht = dht.DHT22(machine.Pin(pin))
        self.update()

    def update(self):
        """Calls dht measure and updates temp & humidity values"""
        self.dht.measure()
        self.temp = self.dht.temperature()
        self.humidity = self.dht.humidity()


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
    """Sets days_since_fed to 0 on button click event"""
    global schedule
    schedule.reset_food_days_counter()


class Schedule():
    def __init__(self):
        self.sync_time()

        # Whether target humidity was achieved after mode changed
        self._target_humidity_achieved = False

        self.days_since_fed = variables['CHANGE_FOOD_DAYS']

        self.update()

    def set_target_humidity_achieved(self):
        self._target_humidity_achieved = True

    def is_target_humidity_achieved(self):
        return self._target_humidity_achieved

    def food_change_due(self):
        return self.days_since_fed >= variables['CHANGE_FOOD_DAYS']

    def reset_food_days_counter(self):
        self.days_since_fed = 0
        current_led.value(1)

    def update(self):
        current_mode = ("AM" if self.get_time_hour() >= morning and
                        self.get_time_hour() < night else "PM")

        # Set inital mode and return
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
    """
        Change the LED to the new led value

        parameter: led (green, yellow, red)
    """
    global current_led
    # Turn the current LED off or leave on and return
    if current_led is not None:
        if current_led is led:
            return
        else:
            current_led.value(0)

    # Turn the 'led' argument that was passed
    led.value(1)

    # Set current_led to 'led'
    current_led = led


async def blink_led():
    """Blinks the current LED on/off every half second """
    global current_led, schedule
    while schedule.food_change_due():
        current_led.value(0 if current_led.value() else 1)
        await uasyncio.sleep(0.5)


async def send_data_to_blynk(sensor, interval=30):
    """
        Send temperature and humidity data to Blynk server to be viewed on app.

        parameter: [int] interval (in minutes) to the send data
    """

    BLYNK_API_URL = ('https://blynk.cloud/external/api/batch/update'
                     f'?token={variables['BLYNK_AUTH_TOKEN']}')

    while True:
        connect_to_wifi()

        url = f'{BLYNK_API_URL}&v0={sensor.temp}&v1={sensor.humidity}'
        urequests.get(url)

        disconnect_from_wifi()

        await uasyncio.sleep(60 * interval)  # Update every 30 minutes


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

    sensor = Sensor(2)  # DHT22 sensor on GPIO2

    # Create a task to continuously send data to Blynk
    uasyncio.create_task(send_data_to_blynk(sensor))

    while True:
        # Sleep for 5s. Decrease sleep to 100ms if target humidity is not met.
        sleep_time = 5 if schedule.is_target_humidity_achieved() else 0.1

        sensor.update()  # Update temp & humidity values

        output = f"Temperature: {sensor.temp}°C, Humidity: {sensor.humidity}%"

        print(output)
        display.reset()
        display.add_text(f"{sensor.temp}c", 7)
        display.add_text(f"{sensor.humidity}%", 41)
        display.show()

        schedule.update()

        if not schedule.is_target_humidity_achieved():
            if schedule.mode == "AM":
                green_bounds = 70
                yellow_bounds = 60
            else:
                green_bounds = 80
                yellow_bounds = 70

            if (sensor.humidity >= green_bounds):
                change_led_color(green)
                schedule.set_target_humidity_achieved()
            elif (sensor.humidity >= yellow_bounds):
                change_led_color(yellow)
            elif (sensor.humidity < yellow_bounds):
                change_led_color(red)

        # If food change due, flash the LED
        if schedule.food_change_due() and blink_led_task is None:
            blink_led_task = uasyncio.create_task(blink_led())

        # Cancel asyncio blink LED task if button pressed
        if not schedule.food_change_due() and blink_led_task is not None:
            blink_led_task.cancel()
            blink_led_task = None

        # Update every 100ms until target achieved, otherwise update every 5s
        await uasyncio.sleep(sleep_time)


# Starts the main thread
uasyncio.run(main())
