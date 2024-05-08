
from fifo import Fifo
from piotimer import Piotimer
from machine import Pin, I2C, ADC
from ssd1306 import SSD1306_I2C
import utime
import urequests as requests
import ujson
import network
import mip
from umqtt.simple import MQTTClient


#WLAN CONNECTION
SSID = "**********"
PASSWORD = "**********"
BROKER_IP = "***********"

# Kubios Cloud
APIKEY = "pbZRUi49X48I56oL1Lq8y8NDjq6rPfzX3AQeNo3a"
CLIENT_ID = "3pjgjdmamlj759te85icf0lucv"
CLIENT_SECRET = "111fqsli1eo7mejcrlffbklvftcnfl4keoadrdv1o45vt9pndlef"
LOGIN_URL = "https://kubioscloud.auth.eu-west-1.amazoncognito.com/login"
TOKEN_URL = "https://kubioscloud.auth.eu-west-1.amazoncognito.com/oauth2/token"
REDIRECT_URI = "https://analysis.kubioscloud.com/v1/portal/login"

######################################################################

# History

# HISTORY = {'item 1': {'hr mean': 74, 'ppi mean': 500}, 'item 2': {'hr mean': 89, 'ppi mean': 477}}
HISTORY = {}
HISTORY_OPTION = ["Back to menu"]
index = 0
TIME_TO_TAKE_SAMPLE = 30


# Initialize I2C interface and OLED display
i2c = I2C(1, scl=Pin(15), sda=Pin(14), freq=400000)
oled_width = 128
oled_height = 64
oled = SSD1306_I2C(oled_width, oled_height, i2c)


######################################################################

class pulseSensor:
    def __init__(self, pin_adc, sample_rate) -> None:
        self.adc = ADC(pin_adc)
        self.fifo = Fifo(500)
        self.sample_rate = sample_rate

    def handler(self, tid):
        self.fifo.put(self.adc.read_u16())
        
######################################################################

def calculate_SDNN(ppi_arr, mean_ppi_value):
    sum = 0
    for ppi in ppi_arr:
        sum += (ppi - mean_ppi_value) ** 2
    SDNN_value = (sum / len(ppi_arr) - 1) ** (1/2)
    return SDNN_value

def calculate_mean_PPI(ppi_array):
    sum = 0
    for ppi in ppi_array:
        sum += ppi
    return sum / len(ppi_array)

def calculate_RMSSD(ppi_array):
    sum = 0
    for i in range(len(ppi_array) - 1):
        sum += (ppi_array[i + 1] - ppi_array[i]) ** 2
    return (sum / (len(ppi_array) - 1)) ** (1/2)

def calculate_her_mean(hr_arr):
    sum = 0
    for data in hr_arr:
        sum += data
    mean_hr = sum / len(hr_arr)
    return int(mean_hr)

def connect_wlan():
    # Connect to WLAN
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)

    # Try to connect to the network once/s
    while not wlan.isconnected():
        oled.fill(0)
        oled.text("Connecting to", align_center(len("Connecting to")), 28, 1)
        oled.text("wlan......", align_center(len("wlan......")), 38, 1)
        oled.show()
        utime.sleep(1)
    
    oled.fill(0)
    oled.text("wlan connect", align_center(len("wlan connect")), 23, 1)
    oled.text("succesfully", align_center(len("succesfully")), 33, 1)
    oled.show()
    utime.sleep(2)


def install_mqtt():
    try:
        mip.install("umqtt.simple")
    except Exception as e:
        print(f"Could not install MQTT: {e}") 


def connect_mqtt():
    mqtt_client = MQTTClient("", BROKER_IP)
    mqtt_client.connect(clean_session=True)
    return mqtt_client

def send_mqtt_message(measurement):
    install_mqtt()

    # Connect to MQTT
    try:
        mqtt_client = connect_mqtt()
    except Exception as e:
        print(f"Failed to connect to MQTT: {e}")

    # Send MQTT message
    try:
        topic = "HeartBeatHoney"
        json_message = ujson.dumps(measurement) 
        mqtt_client.publish(topic, json_message)
        print(f"Sending to MQTT: {topic} -> {json_message}")
            
    except Exception as e:
        print(f"Failed to send MQTT message: {e}")
    

    

def get_response_from_kubios(intervals):
    response = requests.post(
    url = TOKEN_URL,
    data = 'grant_type=client_credentials&client_id={}'.format(CLIENT_ID),
    headers = {'Content-Type':'application/x-www-form-urlencoded'},
    auth = (CLIENT_ID, CLIENT_SECRET))
    response = response.json() #Parse JSON response into a python dictionary
    access_token = response["access_token"] #Parse access token

    #Create the dataset dictionary HERE

    dataset = {
    "type": "RRI",
    "data": intervals,
    "analysis": {"type": "readiness"}
    }

    # Make the readiness analysis with the given data
    response = requests.post(
    url = "https://analysis.kubioscloud.com/v2/analytics/analyze",
    headers = { "Authorization": "Bearer {}".format(access_token),
    "X-Api-Key": APIKEY},
    json = dataset)
    response = response.json()

    return response

def create_history(hr_mean, ppi_mean=0, rmssd=0, sdnn=0, sns=0, pns=0, method=''):
    global index
    # Get current time in seconds since the Epoch
    current_time = utime.time()


    # Convert to a struct_time
    time_struct = utime.gmtime(current_time)
    year, month, day, hour, minutes, seconds, week_day, day_of_year  = time_struct
    #print(year, month, day, hour, minutes)
    date_tuple = (day, month, year)
    time_tuple = (hour, minutes)

    # Convert each element to string before join
    date_created = ".".join(map(str, date_tuple)) 
#     print(date_created)

    time_created = ":".join(map(str, time_tuple))
#     print(time_created)
    
    HISTORY[f"item{len(HISTORY) + 1}"] = {
        "date_create": date_created,
        "time_create": time_created,
        "method": method,
        "hr_mean": hr_mean,
        "ppi_mean": ppi_mean,
        "rmssd": rmssd,
        "sdnn": sdnn,
        "sns": sns,
        "pns": pns
    }
    HISTORY_OPTION.append(f"Measurement{index + 1}")
    index += 1
    

def align_center(length):
    return int((128 - length * 8) / 2)

def show_error():
    oled.fill(0)
    oled.text(f"!!!Error!!!", align_center(len("!!!Error!!!")), 0, 1)
    oled.text(f"Can't detect HR", align_center(len("Can't detect HR")), 26, 1)
    oled.text("Back to menu", align_center(len("Back to menu")), 36, 1)
    oled.text("and try again", align_center(len("and try again")), 46, 1)
    oled.show()

######################################################################

def plotting_signal(rot_en, pulse, current_index):

    pulse = pulseSensor(26, 250)

    #starting time
    start_time = utime.ticks_ms()

    count_hr_display = -1
    display_hr_arr = []
    display_hr = 0

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



    hr_array = []
    ppi_array = []
    ppi_mean = 0
    # Graph settings
    graph_start =  0
    last_x = 0
    # Start in the middle of the screen
    last_y = 64 // 2
    
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
                # 2 pointers tmp_peak and peak point at the first peak
                if pre_value > value and first_time_peak:
                    tmp_peak = pre_value
                    first_time_peak = False
                    peak = pre_value
                    # print("first")
                elif pre_value > value:
                    tmp_peak = pre_value
                    # check if current peak is greater than previous peak
                    if tmp_peak > peak:
                        peak = tmp_peak
                        # peak_index = index
                        # print(f"peak index: {peak_index}")
            # when sample is under threshold the latest peak is the max peak
            else:
                if tmp_peak != 0:
                    peak_indexes.append(index)
                    # print(f"peak index: {index}")

                    if len(peak_indexes) == 2:
                        ppi_samples = peak_indexes[1] - peak_indexes[0]
                        ppi_ms = ppi_samples * 4

                        if ppi_ms != 0:
                            hr = round(60000 / ppi_ms)
                            if hr >= 40 and hr <= 160:
                                #print(f"heart rate: {hr}")
                                display_hr_arr.append(hr)
                                hr_array.append(hr)
                                ppi_array.append(ppi_ms)
                                count_hr_display = (count_hr_display + 1) % 5
                                print(count_hr_display)
                                if count_hr_display == 4:
                                    display_hr_arr.sort()
                                    print(display_hr_arr)
                                    mean_index = len(display_hr_arr) // 2
                                    display_hr = display_hr_arr[mean_index]
                                    print(f"display heart rate: {display_hr}")
                                    display_hr_arr = []
                        peak_indexes.pop(0)
                tmp_peak = 0

            index += 1
            pre_value = value

        # display time in 60s:
        current_time = utime.ticks_ms()
        elapsed_time = int((current_time - start_time) / 1000)


    
        # check if time is more than 10s
        # if elapsed_time > 40 or rot_en.fifo.get() == 0:
        if elapsed_time > TIME_TO_TAKE_SAMPLE and current_index == 0:
            # stop reading data from pulse
            tmr.deinit()

            if hr_array:
                hr_mean = calculate_her_mean(hr_array)
                create_history(hr_mean)
                oled.fill(0)
                oled.text(f"HR mean: {hr_mean}", 20, 0, 1)
                oled.text("Press button", align_center(len("Press button")), 18, 1)
                oled.text("to back", align_center(len("to back")), 28, 1)
                oled.text("to main menu", align_center(len("to main menu")), 38, 1)
                oled.show()
            else:
                show_error()

            
            while True:
                if rot_en.fifo.has_data():
                    e = rot_en.fifo.get()
                    if e == 0:
                        break
            # back to main menu
            break
        
        elif elapsed_time > TIME_TO_TAKE_SAMPLE and current_index == 1:
            # stop reading data from pulse
            tmr.deinit()
            connect_wlan()
            
            if hr_array:
            
                hr_mean = calculate_her_mean(hr_array)
                ppi_mean = calculate_mean_PPI(ppi_array)
                sdnn = calculate_SDNN(ppi_array, ppi_mean)
                rmssd = calculate_RMSSD(ppi_array)
                
                measurement = {
                    "mean_hr": hr_mean,
                    "mean_ppi": ppi_mean,
                    "rmssd": rmssd,
                    "sdnn": sdnn
                    }
                
                send_mqtt_message(measurement)
                
                create_history(hr_mean, ppi_mean=ppi_mean, sdnn=sdnn, rmssd=rmssd)
                
                oled.fill(0)
                oled.text(f"HR mean: {hr_mean}", 0, 0, 1)
                oled.text(f"PPI mean: {ppi_mean}", 0, 10, 1)
                oled.text(f"SDNN: {sdnn}", 0, 20, 1)
                oled.text(f"RMSSD: {rmssd}", 0, 30, 1)
                oled.text("Press to back", align_center(len("Press to back")), 44, 1)
                oled.text("to main menu", align_center(len("to main menu")), 54, 1)
                oled.show()
                
            else:
                show_error()
            

            
            while True:
                if rot_en.fifo.has_data():
                    e = rot_en.fifo.get()
                    if e == 0:
                        break
            # back to main menu
            break

        elif elapsed_time > TIME_TO_TAKE_SAMPLE and current_index == 2:
            # stop reading data from pulse
            tmr.deinit()
            
            connect_wlan()
            
            if hr_array:
                while True:
                

                    oled.fill(0)
                    oled.text("Sending data to", align_center(len("Sending data to")), 23, 1)
                    oled.text("Kubios...", align_center(len("Kubios...")) , 35, 1)
                    oled.show()

                    kubios_data = get_response_from_kubios(ppi_array)
                    
            
                    if kubios_data["status"] == 'ok':

                        measurement = {
                        "mean_hr": kubios_data["analysis"]["mean_hr_bpm"],
                        "mean_ppi": kubios_data["analysis"]["mean_rr_ms"],
                        "rmssd": kubios_data["analysis"]["rmssd_ms"],
                        "sdnn": kubios_data["analysis"]["sdnn_ms"],
                        "sns": kubios_data["analysis"]["sns_index"],
                        "pns": kubios_data["analysis"]["pns_index"]
                        }
                    
                        send_mqtt_message(measurement)
                        oled.fill(0)
                        oled.text("Succesfully!!!", align_center(len("Succesfully!!!")), 0, 1)
                        oled.text("Getting data", align_center(len("Getting data")), 28, 1)
                        oled.text("from Kubios...", align_center(len("from Kubios...")), 38, 1)
                        oled.show()
                        
                        utime.sleep(2)
                        
                        
                        oled.fill(0)
                        oled.text(f"HR mean:{kubios_data["analysis"]["mean_hr_bpm"]}", 0, 0, 1)
                        oled.text(f"PPI mean:{kubios_data["analysis"]["mean_rr_ms"]}", 0, 10, 1)
                        oled.text(f"RMSSD:{kubios_data["analysis"]["rmssd_ms"]}", 0, 20, 1)
                        oled.text(f"SDNN:{kubios_data["analysis"]["sdnn_ms"]}", 0, 30, 1)
                        oled.text(f"SNS:{kubios_data["analysis"]["sns_index"]}", 0, 40, 1)
                        oled.text(f"PNS:{kubios_data["analysis"]["pns_index"]}", 0, 50, 1)
                        oled.show()
                        create_history(hr_mean=kubios_data["analysis"]["mean_hr_bpm"], ppi_mean=kubios_data["analysis"]["mean_rr_ms"], sdnn=kubios_data["analysis"]["sdnn_ms"], rmssd=kubios_data["analysis"]["rmssd_ms"], sns=kubios_data["analysis"]["sns_index"], pns=kubios_data["analysis"]["pns_index"])
                        break
            else:
                show_error()
                    

            
            while True:
                if rot_en.fifo.has_data():
                    e = rot_en.fifo.get()
                    if e == 0:
                        break
            # back to main menu
            break

        elif rot_en.fifo.has_data():
                e =  rot_en.fifo.get()
                if e == 0:
                    # stop adding data to fifo and back to main menu
                    tmr.deinit()
                    #back to main menu
                    break
        else:

            # Plotting signals
            # update screen outside the loop

            value = pulse.adc.read_u16()

            oled.fill_rect(0, 53, 127, 63, 1)
            oled.text(f'Time:{elapsed_time}s', 63, 55, 0)  # Display elapsed time
            oled.text(f"HR: ",0, 55, 0)
            oled.text(f"HR: {display_hr}",0, 55, 0)
            if (max_value - min_value) != 0:
                scaled_value = int((value - min_value) / (max_value - min_value) * 53)

            # print(scaled_value)
            
            graph_start += 3

            oled.line(last_x, 53 - last_y, graph_start, 53 - scaled_value, 1)
            last_x = graph_start
            last_y = scaled_value

            if last_x >= oled_width:
                last_x = 0
                graph_start = 0
                oled.fill_rect(0, 0, 128, 53, 0)

            oled.show()

# plotting_signal()