from machine import Pin, I2C
from ssd1306 import SSD1306_I2C
from fifo import Fifo
import framebuf
from time import ticks_ms
import time


# Initialize I2C interface and OLED display
i2c = I2C(1, scl=Pin(15), sda=Pin(14), freq=400000)
oled_width = 128
oled_height = 64
oled = SSD1306_I2C(oled_width, oled_height, i2c)

######################################################################

heart_rate = bytearray( [
    #// font edit begin : monovlsb : 32 : 32 : 32
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
    0x00, 0x00, 0x00, 0x00, 0x00, 0xC0, 0xC0, 0x00, 
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xC0, 
    0xE0, 0x80, 0x80, 0xC0, 0xFC, 0x0F, 0x1F, 0xF8, 
    0x00, 0x00, 0x00, 0x00, 0xE0, 0xE0, 0x00, 0x00, 
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
    0x00, 0x00, 0x02, 0x02, 0x03, 0x03, 0x03, 0x01, 
    0x01, 0x07, 0x1F, 0x0F, 0x00, 0x00, 0x00, 0x07, 
    0xFF, 0xC0, 0xF0, 0x1F, 0x01, 0x01, 0x07, 0x1C, 
    0x0E, 0x02, 0x02, 0x03, 0x03, 0x02, 0x00, 0x00, 
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
    0x03, 0x03, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
    #// font edit end
    ])

analysis = bytearray( [
    #// font edit begin : monovlsb : 32 : 32 : 32
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x80, 
    0x80, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
    0x80, 0xC0, 0x60, 0x38, 0x0E, 0x0C, 0x00, 0x00, 
    0x00, 0x00, 0x80, 0x80, 0x80, 0xC0, 0x40, 0x40, 
    0x60, 0x30, 0x30, 0x18, 0x0C, 0x06, 0x82, 0x83, 
    0x81, 0x03, 0x82, 0x06, 0x04, 0x0C, 0x1C, 0x06, 
    0x03, 0x00, 0xFC, 0x26, 0x04, 0x04, 0xFE, 0x20, 
    0x00, 0x80, 0x81, 0x81, 0x80, 0x80, 0x00, 0xF0, 
    0x20, 0x30, 0x10, 0xE0, 0x00, 0x75, 0xDF, 0x00, 
    0x01, 0xFF, 0x92, 0x00, 0xFC, 0x08, 0x0C, 0x48, 
    0xFC, 0x00, 0xFF, 0x49, 0x00, 0x00, 0xFF, 0x22, 
    0x22, 0xFF, 0x80, 0x80, 0xD5, 0xFF, 0x00, 0xFF, 
    0xA2, 0x80, 0xC0, 0xFF, 0x00, 0x77, 0xDD, 0x80, 
    0x80, 0xFF, 0x52, 0x00, 0xFF, 0x80, 0xC0, 0x92, 
    0xFF, 0x00, 0xFF, 0xD2, 0x80, 0x80, 0xFF, 0x22
    #// font edit end
    ])

cloud = bytearray( [
    #// font edit begin : monovlsb : 32 : 32 : 32
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
    0x00, 0x00, 0x00, 0x00, 0x00, 0x80, 0x80, 0x40, 
    0x40, 0x60, 0x40, 0x60, 0x40, 0x40, 0x80, 0x80, 
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
    0x00, 0x80, 0x80, 0x40, 0x70, 0x18, 0x0C, 0x04, 
    0x06, 0x04, 0x04, 0x0E, 0x03, 0x01, 0x00, 0x00, 
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 
    0x03, 0x4E, 0xF8, 0x80, 0x80, 0x80, 0x00, 0x00, 
    0x1E, 0xF3, 0x80, 0x80, 0x00, 0x00, 0x00, 0x00, 
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
    0x00, 0x00, 0x00, 0x00, 0x00, 0x81, 0xE7, 0x3C, 
    0x00, 0x00, 0x00, 0x01, 0x01, 0x01, 0x03, 0x01, 
    0x01, 0x03, 0x02, 0x01, 0x03, 0x01, 0x02, 0x01, 
    0x03, 0x01, 0x02, 0x01, 0x03, 0x01, 0x02, 0x01, 
    0x03, 0x01, 0x02, 0x01, 0x01, 0x01, 0x00, 0x00
    #// font edit end
    ])

history = bytearray( [
    #// font edit begin : monovlsb : 32 : 32 : 32
    0x00, 0x00, 0xF8, 0x0C, 0x0C, 0x18, 0x30, 0x98, 
    0x0C, 0x0C, 0x98, 0x10, 0x98, 0x0C, 0x0C, 0x18, 
    0x10, 0x98, 0x0C, 0x84, 0x18, 0x10, 0x18, 0xAC, 
    0xFC, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
    0x00, 0x00, 0xFF, 0x00, 0x00, 0x20, 0xAD, 0xA5, 
    0xA5, 0x8D, 0x81, 0xA1, 0x25, 0x35, 0x25, 0x8C, 
    0x84, 0xA5, 0xB5, 0xA5, 0xAD, 0x00, 0x00, 0x24, 
    0xFF, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
    0x00, 0x00, 0xFF, 0x70, 0x18, 0xC8, 0x99, 0x38, 
    0xE9, 0x88, 0x19, 0x08, 0x09, 0x08, 0x18, 0x09, 
    0x08, 0x09, 0x08, 0x19, 0x08, 0x08, 0x18, 0x09, 
    0x1F, 0x08, 0x08, 0x18, 0x10, 0x30, 0xE0, 0x00, 
    0x00, 0x00, 0x07, 0x0C, 0x19, 0x13, 0x33, 0x18, 
    0x1F, 0x30, 0x10, 0x30, 0x10, 0x10, 0x30, 0x10, 
    0x10, 0x30, 0x10, 0x10, 0x30, 0x10, 0x10, 0x30, 
    0x10, 0x10, 0x30, 0x10, 0x10, 0x1C, 0x07, 0x00
    #// font edit end
    ])

######################################################################





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



def display_menu(images, menu_options, selected_index, on_states):
    oled.fill(0)

    for i, option in enumerate(menu_options):
        if i == selected_index:
            x = int((128 - (len(option * 8))) / 2)
            icon = framebuf.FrameBuffer(images[selected_index], 32, 32, framebuf.MONO_VLSB)
            oled.blit(icon, 48, 0)
            oled.text(option, x, 40, 1)
            oled.text(on_states[selected_index], 36, 56, 1)
            oled.show()

def home_menu():
    oled.fill(0)
    oled.text("HoneyHeartBeat", 7, 17, 1)
    oled.text("Group 12's", 29, 27, 1)
    oled.text("project!", 33, 37, 1)
    oled.show()
    time.sleep(3)

def main():
    #show welcome text
    home_menu()
    #initialize rotary encoder
    rot = Encoder(10, 11, 12, 50, 0)
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
                pass
            display_menu(images, menu_options, selected_index, on_states)
            
if __name__ == "__main__":
    main()





