def calculate_SDNN(signal_arr, mean_ppi_value):
    sum = 0
    for signal in signal_arr:
        sum += (signal - mean_ppi_value) ** 2
    SDNN_value = (sum / len(signal_arr) - 1) ** (1/2)
    return int(SDNN_value)

def calculate_mean_PPI(ppi_array):
    sum = 0
    for ppi in ppi_array:
        sum += ppi
    return int(sum / len(ppi_array))