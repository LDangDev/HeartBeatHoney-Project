from machine import Pin, I2C, ADC
from ssd1306 import SSD1306_I2C
from fifo import Fifo
import framebuf
from plot_signals import plotting_signal
from icons import *

import time
import utime

import micropython
micropython.alloc_emergency_exception_buf(200)



# Initialize I2C interface and OLED display
i2c = I2C(1, scl=Pin(15), sda=Pin(14), freq=400000)
oled_width = 128
oled_height = 64
oled = SSD1306_I2C(oled_width, oled_height, i2c)

######################################################################









######################################################################


class Encoder:
    def __init__(self, rot_a, rot_b, rot_p, debouncing, last_time):
        self.a = Pin(rot_a, mode=Pin.IN, pull=Pin.PULL_UP)
        self.b = Pin(rot_b, mode=Pin.IN, pull=Pin.PULL_UP)
        self.p = Pin(rot_p, mode=Pin.IN, pull=Pin.PULL_UP)
        self.fifo = Fifo(100, typecode = 'i')
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
        new_time = utime.ticks_ms()  # Get current time in milliseconds
        if new_time - self.last_time > self.debouncing:
            self.fifo.put(0)  # Push-button press event
            self.last_time = new_time

class pulseSensor:
    def __init__(self, pin_adc, sample_rate) -> None:
        self.av = ADC(pin_adc)
        self.fifo = Fifo(500)
        self.sample_rate = sample_rate

    def handler(self, tid):
        self.fifo.put(self.av.read_u16())


######################################################################
        



def display_menu(images, menu_options, selected_index, on_states):
    oled.fill(0)

    for i, option in enumerate(menu_options):
        if i == selected_index:
            x = int((128 - (len(option * 8))) / 2)
            icon = framebuf.FrameBuffer(images[selected_index], 32, 32, framebuf.MONO_VLSB)
            oled.blit(icon, 48, 16)
            oled.text(option, x, 56, 1)
            oled.text(on_states[selected_index], 36, 0, 1)
            oled.show()

def home_menu():
    oled.fill(0)
    oled.text("HoneyHeartBeat", 7, 17, 1)
    oled.text("Group 12's", 29, 27, 1)
    oled.text("project!", 33, 37, 1)
    oled.show()
    time.sleep(3)

def show_heart_rate(hr_result, ppi_result):
    oled.fill(0)
    oled.text(f"BPM: {hr_result}", 0, 0, 1)
    oled.text(f"PPI: {ppi_result}", 40, 0, 1)
    oled.show()

######################################################################
 

#initialize rotary encoder and pulse 
rot = Encoder(10, 11, 12, 50, 0)
pulse = pulseSensor(26, 250)
######################################################################

def main():
    #show welcome text
    # home_menu()


    images = [heart_rate, analysis, cloud, history]
    menu_options = ["HR Measurement", "Analysis", "Kubios Cloud", "History"]
    on_states = ["* . . .", ". * . .", ". . * .", ". . . *"]
    selected_index = 0
    display_menu(images, menu_options, selected_index, on_states)
    while True:
        while rot.fifo.has_data():
            event = rot.fifo.get()

            if event == 1:
                selected_index = (selected_index + 1) % len(menu_options)
            elif event == -1:
                selected_index = (selected_index - 1) % len(menu_options)
            else:
                if selected_index == 0:
                    while True:
                        # print(event)
                        plotting_signal(rot, pulse)
                        break
                        
            display_menu(images, menu_options, selected_index, on_states)
            
if __name__ == "__main__":
    main()






