
from fifo import Fifo
from piotimer import Piotimer
from machine import Pin, I2C, ADC
from ssd1306 import SSD1306_I2C
import utime


# Initialize I2C interface and OLED display
i2c = I2C(1, scl=Pin(15), sda=Pin(14), freq=400000)
oled_width = 128
oled_height = 64
oled = SSD1306_I2C(oled_width, oled_height, i2c)




class pulseSensor:
    def __init__(self, pin_adc, sample_rate) -> None:
        self.av = ADC(pin_adc)
        self.fifo = Fifo(500)
        self.sample_rate = sample_rate

    def handler(self, tid):
        self.fifo.put(self.av.read_u16())



def plotting_signal(rot_en, pulse):

    pulse = pulseSensor(26, 250)

    #starting time
    start_time = utime.ticks_ms()


    pre_value = 0
    tmp_peak = 0
    index = 0
    peak = 0
    peak_indexes = []
    first_time_peak = True
    hr = 0
    min_value = 0
    max_value = 0
    scaled_value = 0

    # Graph settings
    graph_start = 0
    last_y = oled_height // 2  # Start in the middle of the screen

    tmr = Piotimer(mode = Piotimer.PERIODIC, freq = 250, callback = pulse.handler)

    oled.fill(0)
    while True:
        while pulse.fifo.has_data():
            value = pulse.fifo.get()
            # print(value)

            min_value = min(pulse.fifo.data)
            max_value = max(pulse.fifo.data)
            #threshold with 5% margin
            threshold = (((max_value - min_value) / 2) + min_value) * 1.05
            # when sample greater than threshold start checking the peak
            if value > threshold:
                # 
                if pre_value > value and first_time_peak:
                    tmp_peak = pre_value
                    first_time_peak = False
                    peak = pre_value
                    # print("first")
                elif pre_value > value:
                    tmp_peak = pre_value
                    if tmp_peak > peak:
                        peak = tmp_peak
                        # peak_index = index
                        # print(f"peak index: {peak_index}")
            else:
                if tmp_peak != 0:
                    peak_indexes.append(index)
                    # print(f"peak index: {index}")

                    if len(peak_indexes) == 2:
                        ppi_samples = peak_indexes[1] - peak_indexes[0]
                        ppi_ms = ppi_samples * 4

                        if ppi_ms != 0:
                            hr = round(60000 / ppi_ms)
                            if hr >= 40 and hr <= 240:
                                print(f"heart rate: {hr}")
                        peak_indexes.pop(0)
                tmp_peak = 0

            index += 1
            pre_value = value

        # display time in 60s:
        current_time = utime.ticks_ms()
        elapsed_time = int((current_time - start_time) / 1000)
        
        # check if time is more than 10s
        if elapsed_time > 10:
            break
        if rot_en.fifo.has_data():
            e =  rot_en.fifo.get()
            if e == 0:
                # stop adding data to fifo and back to main menu
                tmr.deinit()
                break

        # Plotting signals
        # update screen outside the loop
        value = pulse.av.read_u16()

        oled.fill_rect(0, 53, 127, 63, 1)
        oled.text(f'Time:{elapsed_time}s', 63, 55, 0)  # Display elapsed time
        oled.text(f"HR:{hr if hr >= 40 and hr <= 240 else ''}",0, 55, 0)
        if (max_value - min_value) != 0:
            scaled_value = int((value - min_value) / (max_value - min_value) * 53)

        # print(scaled_value)
        

        oled.line(graph_start, 53 - last_y, graph_start, 53 - scaled_value, 1)
        last_y = scaled_value
        graph_start += 1

        if graph_start >= oled_width:
            graph_start = 0
            oled.fill_rect(0, 0, 128, 53, 0)

        oled.show()

# plotting_signal()




