import collections
import os
from pathlib import Path
import time

'''
    STATIC VARIABLE
'''

ADD_TABLE_SIZE = [4, 3]  # Size of album table
COLOR_TABLE = [
    '#b18484',
    '#eababa',
    '#c4c7ff',
    '#d67676',
    '#86a9dc',
    '#feff57',
    '#5700ff',
]
INDEX_TECHNIQUES = [1, 1, 1, 1]
LIST_TECHNIQUES = [
    "Charge/disch",
    "Rate testing",
    "Cyclic voltammetry",
    "Differential Pulse Voltammetry"
]

CV_MEASURE = 0
LSV_MEASURE = 1

DPV_RAISING = 0
DPV_FALLING = 1
DPV_TIME_STAMP = 2
USB_SIZE = 120
usb_vid_ = "0xa0a0"  # Default USB vendor ID, can also be adjusted in the GUI
usb_pid_ = "0x0003"  # Default USB product ID, can also be adjusted in the GUI
current_range_list = ["200 mA", u"20 mA", u"200 µA", u"2 µA"]
cv_range_checkboxes = []

# Fine adjustment for shunt resistors, containing values of R1/10ohm, R2/1kohm, R3/100kohm (can also be adjusted in the GUI)
shunt_calibration = [1.,1.,1.,1.] # Fine adjustment for shunt resistors, containing values of R1/1ohm, R2/10ohm, R3/1kohm, R4/100kohm (can also be adjusted in the GUI)

# Default current range (expressed as index in current_range_list)
currentrange = 0
units_list = ["Potential (V)", "Current (mA)", "DAC Code"]
dev = None  # Global object which is reserved for the USB device
current_offset = 0.  # Current offset in DAC counts
potential_offset = 0.  # Potential offset in DAC counts
potential = 0.  # Measured potential in V
current = 0.  # Measured current in mA
last_potential_values = collections.deque(maxlen=200)
last_current_values = collections.deque(maxlen=200)
raw_potential = 0  # Measured potential in ADC counts
raw_current = 0  # Measured current in ADC counts
last_raw_potential_values = collections.deque(maxlen=200)
last_raw_current_values = collections.deque(maxlen=200)

# Global counters used for automatic current ranging
overcounter, undercounter, skipcounter = 0, 0, 0
time_of_last_adcread = 0.
adcread_interval = 0.05  # ADC sampling interval (in seconds)

# Enable logging of potential and current in idle mode (can be adjusted in the GUI)
logging_enabled = False
status_table = 0
# usb_connected = False
start_stop = 1
stop = 0
listFrame = []
queue_measure = []
queue_create = []
id_ = 0
idx_frame = 0
para_run = {}

x_axis = [5, 110, 215]
y_axis = [190, 260, 330, 400]

OPTION_NO = 0
OPTION_EDIT = 1
OPTION_REMOVE = 2
OPTION_DUMPLICATE = 3

ACTIVE = 0
DE_ACTIVE = 1