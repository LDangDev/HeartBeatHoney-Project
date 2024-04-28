from machine import ADC
from fifo import Fifo
from piotimer import Piotimer

class PulseDetector:
    def __init__(self, adc_pin_nr, sample_rate=250, threshold_percentage=0.15):
        self.adc_pin_nr = adc_pin_nr    
        self.sample_rate = sample_rate
        self.threshold_percentage = threshold_percentage
        self.ms_in_minute = 60000
        self.min_hr = 30
        self.max_hr = 240
        self.prev_sample = 0
        self.current_peak_index = 0
        self.index = 0  
        self.av = ADC(self.adc_pin_nr)
        self.fifo = Fifo(500)
        self.tmr = Piotimer(mode=Piotimer.PERIODIC, freq=self.sample_rate, callback=self.handler)

    def handler(self, tid):
        self.fifo.put(self.av.read_u16())

    def calculate_threshold(self):
        min_value = min(self.fifo.data)
        max_value = max(self.fifo.data)
        amplitude = max_value - min_value
        threshold = max_value - self.threshold_percentage * amplitude
        return threshold

    def detect_pulse(self):
        peak_tmp = 0
        max_tmp = 0
        peak_index = 0
        while True:
            if self.fifo.has_data():
                value = self.fifo.get()
                # print(value)
                threshold = self.calculate_threshold()
                # print(f"threshold {threshold}")
                if value > threshold:
                    if self.prev_sample > value:
                        peak_tmp = self.prev_sample
                        # print(f"peak tmp {peak_tmp}")
                        if peak_tmp >= max_tmp:
                            max_tmp = peak_tmp
                            peak_index = self.index - 1
                            # print(f"max tmp {max_tmp}")
                            # print(f"index {self.index - 1}")
                else:
                    if max_tmp != 0:
                        # print("test")
                        # print(f"threshold {threshold}")
                        # print(f"peak: {max_tmp}")
                        self.current_peak_index = peak_index
                        ppi_samples = peak_index
                        ppi_ms = ppi_samples * 4
                        # print(ppi_samples)
                            
                        if ppi_ms != 0:
                            hr = round(self.ms_in_minute / ppi_ms)
                            if self.min_hr <= hr <= self.max_hr:
                                print(hr)
                            # print("-------------------------------")

                        self.index = -1
                    max_tmp = 0

                self.prev_sample = value
                self.index += 1
    

def main():
    pin_nr = 26
    pulse_detector = PulseDetector(pin_nr)
    pulse_detector.detect_pulse()

if __name__ == "__main__":
    main()
