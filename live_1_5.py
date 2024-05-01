from machine import ADC
from fifo import Fifo
from piotimer import Piotimer


class pulseSensor:
    def __init__(self, pin_adc, sample_rate) -> None:
        self.av = ADC(pin_adc)
        self.fifo = Fifo(500)
        self.sample_rate = sample_rate

    def handler(self, tid):
        self.fifo.put(self.av.read_u16())



pre_value = 0
tmp_peak = 0
peak_index = 0
index = 0
peak = 0
peak_indexes = []
first_time_peak = True

pulse = pulseSensor(26, 250)

tmr = Piotimer(mode = Piotimer.PERIODIC, freq = 250, callback = pulse.handler)


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



