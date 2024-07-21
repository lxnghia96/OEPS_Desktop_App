# Author: NghiaLX
import os
import sys
# Import UI library
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5 import uic
import pyqtgraph as pg
import time
from PyQt5.QtWidgets import QMessageBox
# Import utils helper function
# Get static var from global_var file
from utils.global_var import *
from utils.util import *
from utils.calculate import *
from utils.control_usb import *
# Import class Device
from models.device import Device
# Import UI class
from ui.model.manual_ui import Manual
from ui.model.calibrate_ui import Calibration
from ui.model.create import Create, Edit_Measure
from ui.model.frame import Frame
from pyqtgraph.Qt import  QtGui
from pathlib import Path

# Init and set color of UI
pg.setConfigOptions(foreground="#e5e5e5", background="#00304f")
# Read config to stop zero offset funciton
CONFIG = get_config('./config/config.yml')
# path save file result
base_dir = os.path.dirname(os.path.realpath(__file__))
# Create path dir for save result technique
SAVE_PATH = os.path.join(base_dir, 'save')
# Create save path for each technique
Path(SAVE_PATH).mkdir(parents=True, exist_ok=True)


class main(QMainWindow):
    '''
    Main window of UI:
    1. Add sub window from other UI class
    2. Add control logic to UI
    '''
    def __init__(self):
        super(main, self).__init__()
        # Load main window UI
        uic.loadUi('./ui/mainwindow.ui', self)
        # Set tracking mouse to get the coordinate in UI
        self.setMouseTracking(True)

        self.runLoop = False
        # Set default value for VID, PID, value usb_vid_, usb_pid_ was imported in utils/global_var.py
        self.usb_vid.setText(usb_vid_)
        self.usb_pid.setText(usb_pid_)

        # Create new Device object
        self.new_device = Device(self)

        # Add sub UI with manual and calibaration in taskbar main UI
        self.manual_window = Manual(self, self.new_device)
        self.calibration_window = Calibration(self.new_device)

        # Add control for mouse click connect button
        self.usb_connect.clicked.connect(
            self.new_device.connect_disconnect_usb)
        # Add control for start button
        self.button_start.clicked.connect(self.new_device.start)
        # Add control for auto_zero button in Calibration UI
        self.calibration_window.auto_zero.clicked.connect(
            self.button_zero_offset)
        # Add control for auto_calibrate button in Calibration UI
        self.calibration_window.auto_calibrate.clicked.connect(
            self.new_device.dac_calibrate)
        # Add control for load_from_device button in Calibration UI
        self.calibration_window.load_from_device.clicked.connect(
            self.new_device.get_calibration)
        # Add control for save_to_device button in Calibration UI
        self.calibration_window.save_to_device.clicked.connect(
            self.new_device.set_calibration)
        # Add control for refresh button
        self.button_refresh.clicked.connect(self.refresh)
        # Add control for open_manual taskbar
        self.actionControl.triggered.connect(self.open_manual)
        # Add control for open_calibration taskbar
        self.actionCalibration.triggered.connect(self.open_calibration)
        # Add control for current_range_set in Manual UI
        self.current_range_set.clicked.connect(
            self.new_device.set_current_range)

        # Set value for current_range_set in Manual UI
        self.manual_window.current_range_box.addItems(
            ["200 mA", "20 mA", u"200 µA", u"2 µA"])

        # Set value for Potential in Manual UI
        self.manual_window.comboBox_2.addItems(
            ["Potential (V)", "Current (mA)", "DAC Code"])
        # Get the i_th measure of table measure
        # Get the i_th measure of list ready measure in start/refresh bar
        self.status_line = 0

        # Create new measure in main UI with Add button in techique area
        self.create_measure.clicked.connect(self.open_new)
        # Delete new measure in main UI with Add button in techique area
        self.delete_measure.clicked.connect(self.delete_mes)
        # Delete new measure in main UI with Add button in techique area
        self.edit_measure.clicked.connect(self.edit_mes)

        # Set first plot zone UI -> dynamic plot continuous update
        self.dynamicPlt = pg.PlotWidget(self)

        self.dynamicPlt.move(305, 92)
        self.dynamicPlt.resize(690, 450)
        # Set first plot zone UI -> result zone
        # self.dynamicPlt2 = pg.PlotWidget(self)
        # self.dynamicPlt2.move(1000, 22)
        # self.dynamicPlt2.resize(370, 520)
        # Set timer for loop UI
        self.timer2 = pg.QtCore.QTimer()
        # Auto run self.update method loop with timer
        self.timer2.timeout.connect(self.update)
        self.timer2.start(self.new_device.qt_timer_period)

        # Plot Main UI and Sub UI
        self.show()


    def emergency_shutdown(self):
        '''Turns the cell off if the current is above 220 mA'''
        global current, state
        if np.absolute(current) > 220.:
            if state != States.Idle:
                state = States.Idle
            set_control_mode(True)
            self.set_output(1,0.)
            # QMessageBox.critical(mainwidget, "Warning!","The current has exceeded its maximum value of 200 mA.")
        pass

    def update(self):
        global queue_measure, para_run
        #queue_measure: Queue of list measure
        # Check state of Device
        if self.new_device.isUsbConnected() == True:
            self.runLoop = True
            pass
        else:
            self.runLoop = False
            pass
        if self.runLoop == True:
            if self.new_device.state == States.Idle_Init:
                # Init idel device
                self.new_device.idle_init()
            elif self.new_device.state == States.Idle:
                self.new_device.read_potential_current()
                self.new_device.update_live_graph()
            elif stop: # stop default = 0
                pass
            # Init measure follow its techniques
            elif self.new_device.state == States.Measuring_CD and stop == 0:
                self.new_device.cd_update(para_run)
                self.new_device.Status_bar_Blynk(self.new_device.status_Num)
            elif self.new_device.state == States.Measuring_CV and stop == 0:
                self.new_device.cv_update(para_run)
                self.new_device.Status_bar_Blynk(self.new_device.status_Num)
            elif self.new_device.state == States.Measuring_Rate and stop == 0:
                self.new_device.rate_update(para_run)
                self.new_device.Status_bar_Blynk(self.new_device.status_Num)
            elif self.new_device.state == States.Measuring_DPV and stop == 0:
                self.new_device.dpv_update(para_run)
                self.new_device.Status_bar_Blynk(self.new_device.status_Num)
            elif self.new_device.state == States.Measuring_start and stop == 0:
                if queue_measure:
                    if queue_measure[0]["type"] == "cd":
                        # Calibrate to zero offet to start new measure
                        # self.button_zero_offset()
                        self.new_device.cd_start(queue_measure[0]['value'])
                        para_run = queue_measure[0]['value']
                        queue_measure.pop(0)
                    elif queue_measure[0]["type"] == "cv":
                        # Calibrate to zero offet to start new measure
                        # self.button_zero_offset()
                        self.new_device.cv_start(queue_measure[0]['value'])
                        para_run = queue_measure[0]['value']
                        queue_measure.pop(0)
                    elif queue_measure[0]["type"] == "rate":
                        # Calibrate to zero offet to start new measure
                        # self.button_zero_offset()
                        self.new_device.rate_start(queue_measure[0]['value'])
                        para_run = queue_measure[0]['value']
                        queue_measure.pop(0)
                    elif queue_measure[0]["type"] == "dpv":
                        # Calibrate to zero offet to start new measure
                        # self.button_zero_offset()
                        self.new_device.dpv_start(queue_measure[0]['value'])
                        para_run = queue_measure[0]['value']
                        queue_measure.pop(0)
                    self.new_device.status_Num += 1
                else:
                    # IF Queue is empty -> reset button to start
                    self.new_device.state = States.Stationary_Graph
                    self.new_device.Status_bar_Blynk(self.new_device.status_Num)
                    self.button_start.setText('Start')
            elif self.new_device.state == States.Stationary_Graph:
                self.new_device.read_potential_current()
                self.new_device.update_live_graph()

    def button_zero_offset(self):
        '''
        Calibrate to zero offet to start new measure
        '''
        check_auto_zero = 0
        counter = 0
        while not check_auto_zero:
            # offset the device
            self.new_device.zero_offset_()
            # Read current value
            self.new_device.read_potential_current()
            # Update main UI
            self.new_device.update_live_graph()
            time.sleep(0.3)
            print(self.new_device.potential,
                  self.new_device.current, check_auto_zero)
            counter += 1
            # Condition to stop zero offet
            if counter >= 2:
                check_auto_zero = 1
            else:   
                check_auto_zero = CONFIG['para']['pot_offs_zero'][0] < self.new_device.potential < CONFIG['para']['pot_offs_zero'][
                    1] and CONFIG['para']['cur_offs_zero'][0] < self.new_device.current < CONFIG['para']['cur_offs_zero'][1]
            

    def refresh(self):
        '''
        Refresh button to reset the UI
        '''
        global queue_measure
        self.new_device.refresh()
        self.button_start.setText('Start')
        for frame in listFrame:
            if frame.check_stack:
                frame.frame_refresh()

    def open_new(self):
        # Create new measure
        qt_wid = Create(self)
        qt_wid.show()

    def edit_mes(self):
        for frame in listFrame:
            if frame.checkSelect:
                qt_wid = Edit_Measure(self, frame)
                qt_wid.show()

    def delete_mes(self):
        idx = 0
        self.update_measure_show(DE_ACTIVE)
        for frame in listFrame:
            if frame.checkSelect:
                listFrame.remove(frame)
        for frame in listFrame:
            frame.index_table = idx
            idx +=1    
        self.update_measure_show(ACTIVE)

        
    def update_measure_show(self, isShow):
        global listFrame, x_axis, y_axis
        if isShow == ACTIVE:
            for frame in  listFrame:
                frame.setStyleSheet("background-color: %s;" %
                                        COLOR_TABLE[frame.index_measure])
                frame.setText(frame.name_technique)
                frame.resize(80, 60)
                frame.setParent(self.main_widget)
                frame.move((x_axis[int(frame.index_table % ADD_TABLE_SIZE[1])]),
                            int(y_axis[int(frame.index_table / ADD_TABLE_SIZE[1])]))
                frame.show() 
        else:
            for frame in  listFrame:
                frame.hide()

    def open_manual(self):
        # Open manual taskbar
        self.manual_window.show()

    def open_calibration(self):
        # Open open_calibration taskbar
        self.calibration_window.show()

    def mouseMoveEvent(self, e):
        global listFrame
        # Get the coordinate of mouse, if mouse click in measure, it will move measure to album zone
        for frame in listFrame:
            if frame.check_move:
                frame.move(e.x()-50, e.y()-50)





app = QApplication(sys.argv)
main_window = main()
main_window.activateWindow()
app.exec_()
