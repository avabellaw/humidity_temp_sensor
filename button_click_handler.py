from machine import Pin
import utime


class ButtonClickHandler:
    """
        Creates a click handler using the GPIO pin provided
    """
    def __init__(self, GPIO_pin, click_handler):
        """
            Parameters:
                GPIO_PIN - GPIO pin to use for the button.
                click_handler - Click handler function with arg time_held_down.
        """
        self.button_down = False
        self.button_held_down_start = 0
        self.click_handler = click_handler

        # Sets the GPIO as an input and listens
        # Pin.PULL_UP enables the internal pull up resistor
        button = Pin(GPIO_pin, Pin.IN, Pin.PULL_UP)

        # Will call the event handler when button is pressed down or released
        button.irq(trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING,
                   handler=self._button_event_handler)

    def _button_event_handler(self, pin):
        """
            Private method - processes button clicks and calls click handler.
        """
        if not pin.value():  # Button down
            if not self.button_down:
                self.button_down = True
                self.button_held_down_start = utime.ticks_ms()
        else:  # Button released
            if self.button_down:
                button_held_down_finish = utime.ticks_ms()

                time_held_down = button_held_down_finish
                - self.button_held_down_start

                self.button_down = False

                self.click_handler(time_held_down)
