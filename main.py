from machine import Pin, I2C
from ssd1306 import SSD1306_I2C
from fifo import Fifo
from time import ticks_ms
import time


# Initialize I2C interface and OLED display
i2c = I2C(1, scl=Pin(15), sda=Pin(14), freq=400000)
oled_width = 128
oled_height = 64
oled = SSD1306_I2C(oled_width, oled_height, i2c)


class Encoder:
    def __init__(self, rot_a, rot_b, rot_p, debouncing, last_time):
        self.a = Pin(rot_a, mode=Pin.IN, pull=Pin.PULL_UP)
        self.b = Pin(rot_b, mode=Pin.IN, pull=Pin.PULL_UP)
        self.p = Pin(rot_p, mode=Pin.IN, pull=Pin.PULL_UP)
        self.fifo = Fifo(30, typecode = 'i')
        self.debouncing = debouncing
        self.last_time = last_time

        self.a.irq(handler=self.handler, trigger=Pin.IRQ_RISING, hard=True)
        self.p.irq(handler=self.p_handler, trigger=Pin.IRQ_RISING, hard=True)

    def handler(self, pin):
        if self.b():
            self.fifo.put(-1)
        else:
            self.fifo.put(1)

    def p_handler(self, pin):
        new_time = ticks_ms()  # Get current time in milliseconds
        if new_time - self.last_time > self.debouncing:
            self.fifo.put(0)  # Push-button press event
            self.last_time = new_time

def display_menu(oled, menu_options, led_states, selected_index):
    # Function to update the menu on the OLED display with current selection highlighted and LED states
    oled.fill(0)  # Clear the OLED display
    for i, option in enumerate(menu_options):
        if i == selected_index:
            if led_states[i]:
                oled.text(f"[{option} - ON]", 0, i * 10)
            else:
                oled.text(f"[{option} - OFF]", 0, i * 10)

        else:
            if led_states[i]:
                oled.text(f"{option} - ON ", 8, i * 10)
            else:
                oled.text(f"{option} - OFF", 8, i * 10)
    oled.show()  # Update OLED display

def home_menu():
    oled.fill(0)
    oled.text("HoneyHeartBeat", 7, 17, 1)
    oled.text("Group 12's", 29, 27, 1)
    oled.text("project!", 33, 37, 1)
    oled.show()
    time.sleep(3)

def main():
    home_menu()
    # Initialize the encoder
    rot = Encoder(10, 11, 12, 50, 0)
    # Initialize LED states
    led_states = [False, False, False, False]
    menu_options = ["1.Option", "2.Option", "3.Option", "4.Option"]
    selected_index = 0

    display_menu(oled, menu_options, led_states, selected_index)

    while True:
        while rot.fifo.has_data():
            event = rot.fifo.get()

            if event == 1:  # Clockwise rotation
                selected_index = (selected_index + 1) % len(menu_options)
                # print(selected_index)
            elif event == -1:  # Counter-clockwise rotation
                selected_index = (selected_index - 1) % len(menu_options)
            else:  # Push-button press event
                led_states[selected_index] = not led_states[selected_index]  # Toggle LED state
                # print(f"Toggle LED {selected_index + 1}: {'On' if led_states[selected_index] else 'Off'}")
                # print("led state: ", led_states)
        display_menu(oled, menu_options, led_states, selected_index)

if __name__ == "__main__":
    main()






