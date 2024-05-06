from machine import Pin, I2C, ADC
from ssd1306 import SSD1306_I2C
from fifo import Fifo
import framebuf
from plot_signals import plotting_signal, align_center, HISTORY, HISTORY_OPTION
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
        



def display_menu(images, menu_options, selected_menu_index, on_states):
    oled.fill(0)

    for i, option in enumerate(menu_options):
        if i == selected_menu_index:
            x = align_center(len(option))
            icon = framebuf.FrameBuffer(images[selected_menu_index], 32, 32, framebuf.MONO_VLSB)
            oled.blit(icon, 48, 16)
            oled.text(option, x, 56, 1)
            oled.text(on_states[selected_menu_index], 28, 0, 1)
            oled.show()

def display_history_options(HISTORY_OPTION, selected_history_index):
    
    oled.fill(0)
    for i in range(len(HISTORY_OPTION)) :
        if i == selected_history_index and i == 0:
            # Add 2 pixel gap between lines
            oled.fill_rect(0, i * 10, 127, 8, 1)
            oled.text(f"{HISTORY_OPTION[selected_history_index]}", 0, i * 10, 0)

        elif i == selected_history_index:
            oled.fill_rect(0, i * 10, 127, 8, 1)
            oled.text(f"{HISTORY_OPTION[selected_history_index]}", 16, i * 10, 0)
        else:
            if i == 0:
                oled.text(f"{HISTORY_OPTION[i]}", 0, i * 10, 1)
            else:
                oled.text(f"{HISTORY_OPTION[i]}", 16, i * 10, 1)	
        oled.show()


def home_menu():
    oled.fill(0)
    oled.text("HoneyHeartBeat", 7, 17, 1)
    oled.text("Group 12's", 29, 27, 1)
    oled.text("project!", 33, 37, 1)
    oled.show()
    time.sleep(3)


######################################################################
 

#initialize rotary encoder and pulse 
rot = Encoder(10, 11, 12, 50, 0)
pulse = pulseSensor(26, 250)
######################################################################

def main():
    # show welcome text
#     home_menu()


    images = [heart_rate, analysis, cloud, history, exit_icon]
    menu_options = ["MEASURE HR", "BASIC ANALYSIS", "KUBIOS", "HISTORY", "EXIT"]

    on_states = ["* . . . .", ". * . . .", ". . * . .", ". . . * .", ". . . . *"]
    selected_menu_index = 0
    selected_history_index = 0
    pre_state_rot = 0
    is_exit = False

    display_menu(images, menu_options, selected_menu_index, on_states)
    while True:
        while rot.fifo.has_data():
            event = rot.fifo.get()
            # print(event)
            if event == 1:
                selected_menu_index = (selected_menu_index + 1) % len(menu_options)
            elif event == -1:
                selected_menu_index = (selected_menu_index - 1) % len(menu_options)
            else:
                # Access history
                if selected_menu_index == 3:
                    # print(HISTORY)
                    if HISTORY != {}:
                        display_history_options(HISTORY_OPTION, selected_history_index)
                        # print(f"rot_event: {event}")
                        while True:
                            # print("test")
                            # print(HISTORY_OPTION)
                            if rot.fifo.has_data():
                                rot_event = rot.fifo.get()
                                
                                # print(f"selected history index: {selected_history_index}")
                                # print(f"rot value: {rot_event}")
                                if pre_state_rot == rot_event:
                                    is_exit = True
                                    
                                if rot_event == 1:
                                    selected_history_index = (selected_history_index + 1) % len(HISTORY_OPTION)
                                elif rot_event == -1:
                                    selected_history_index = (selected_history_index - 1) % len(HISTORY_OPTION)
                                elif rot_event == 0 and selected_history_index != 0:
                                    item_key = f"item{selected_history_index}"
                                    
                                    while True:
                                        oled.fill(0)
                                        oled.text(f"{HISTORY[item_key]['date_create']} { HISTORY[item_key]['time_create']}", 8, 0)
                                        oled.text(f"MEAN HR:{HISTORY[item_key]['hr_mean']}", 0, 8)
                                        oled.text(f"MEAN PPI:{HISTORY[item_key]['ppi_mean']}", 0, 18)
                                        oled.text(f"RMSSD:{HISTORY[item_key]['rmssd']}", 0, 28)
                                        oled.text(f"SDNN:{HISTORY[item_key]['sdnn']}", 0, 38)
                                        oled.text(f"SNS:{HISTORY[item_key]['sns']}", 0, 48)
                                        oled.text(f"PNS:{HISTORY[item_key]['pns']}", 0, 56)
                                        oled.show()
                                        if rot.fifo.has_data():
                                            e = rot.fifo.get()
                                            if e == 0:
                                                break
                                elif rot_event == 0 and selected_history_index == 0 and is_exit:
                                    break
                                
                                
                                display_history_options(HISTORY_OPTION, selected_history_index)

                            
                    else:
                        while True:
                            oled.fill(0)
                            oled.text(f"NO HISTORY!!!", 12, 0, 1)
                            oled.text(f"Press button", 16, 20, 1)
                            oled.text(f"to back to", 16, 30, 1)
                            oled.text(f"main menu", 16, 40, 1)
                            oled.show()
                            if rot.fifo.has_data():
                                e = rot.fifo.get()
                                # print(e)
                                if e == 0:
                                    break
                # exit program               
                elif selected_menu_index == 4:
                    print("test")
                    oled.fill(0)
                    oled.show()
                    machine.reset()
                else:
                    while True:
                        # print(event)
                        plotting_signal(rot, pulse, selected_menu_index)
                        break
                        
            display_menu(images, menu_options, selected_menu_index, on_states)
            
if __name__ == "__main__":
    main()






