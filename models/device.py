import os
import sys

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5 import uic, QtOpenGL, QtGui
import pyqtgraph as pg
import random
import copy
import usb
import time
import platform
import timeit
import collections
import scipy.integrate
from pathlib import Path

from utils.global_var import *
from utils.calculate import *
from utils.control_usb import *
import platform
import time

'''
Create attributes and methods for each device
'''


class Device():
    def __init__(self, main_window):

        if platform.system() != "Windows":
            # On Linux/OSX, use the Qt timer
            self.busyloop_interval = 0
            self.qt_timer_period = 1e3*adcread_interval  # convert to ms
        else:
            # On MS Windows, system timing is inaccurate, so use a busy loop instead
            self.busyloop_interval = adcread_interval
            self.qt_timer_period = 0

        self.state = States.NotConnected  # Initial state
        self.main_window = main_window
        self.dev = None
        self.currentCycle = 0
        self.prevPotential = 0
        self.currPotential = 0
        self.status_bar = [self.main_window.status_1, self.main_window.status_2, self.main_window.status_3, 
                           self.main_window.status_4, self.main_window.status_5, self.main_window.status_6, self.main_window.status_7]
        self.status_State = True
        self.prev_timestamp = time.time()
        self.status_Num = 0
        self.dpv_Data = []
        self.dpv_Len = 0
        self.potential_apply = 0

        self.checkUsbConnection = False

    def connect_disconnect_usb(self):
        """Toggle the USB device between connected and disconnected states."""
        # global dev, state
        if self.dev is not None:  # If the device is already connected, then this function should disconnect it
            usb.util.dispose_resources(self.dev)
            self.dev = None
            self.state = States.NotConnected
            self.main_window.usb_connect.setText("Connect")
            # log_message("USB Interface disconnected.")
            return

        # Otherwise, try to connect

        usb_vid_string = str(self.main_window.usb_vid.text())
        usb_pid_string = str(self.main_window.usb_pid.text())
        self.dev = usb.core.find(idVendor=int(usb_vid_string, 0),
                                 idProduct=int(usb_pid_string, 0))
        if self.dev is None:
            print("USB Device Not Found, No USB device was found with VID %s and PID %s. Verify the vendor/product ID and check the USB connection." %
                  (usb_vid_string, usb_pid_string))
        else:
            self.main_window.usb_connect.setText("Disconnect")
            # log_message("USB Interface connected.")
            try:
                self.main_window.label_manufacture.setText(
                    "Manufacture:   %s" % (self.dev.manufacturer))
                self.main_window.label_product.setText(
                    "Product:   %s" % (self.dev.product))
                self.main_window.label_serial.setText(
                    "Serial #:   %s" % (self.dev.serial_number))

                # hardware_device_info_text.setText("Manufacturer: %s\nProduct: %s\nSerial #: %s" % (
                #     dev.manufacturer, dev.product, dev.serial_number))
                self.get_calibration()
                set_cell_status(self.dev, self.main_window, False)  # Cell off
                set_control_mode(self.dev, self.main_window, False)  # Potentiostatic control
                self.set_current_range()  # Read current range from GUI
                self.checkUsbConnection = True
                self.state = States.Idle_Init  # Start idle mode
            except ValueError:
                self.checkUsbConnection = False
                print("### Error USB")
                pass  # In case the device is not yet calibrated

    def get_offset(self):
        """Retrieve offset values from the device's flash memory."""
        global potential_offset, current_offset
        if self.dev is not None:  # Make sure it's connected
            self.dev.write(0x01, b'OFFSETREAD')  # 0x01 = write address of EP1
            # 0x81 = read address of EP1
            response = bytes(self.dev.read(0x81, 64))
            # If no offset value has been stored, all bits will be set
            if response != bytes([255, 255, 255, 255, 255, 255]):
                potential_offset = dac_bytes_to_decimal(response[0:3])
                current_offset = dac_bytes_to_decimal(response[3:6])
                self.main_window.calibration_window.pot_offset_input.setText(
                    "%d" % potential_offset)
                self.main_window.calibration_window.curr_offset_input.setText(
                    "%d" % current_offset)
            else:
                print("ERROR get offset")
        else:
            print("Not connected")

    def dac_calibrate(self):
        """Activate the automatic DAC1220 calibration function and retrieve the results."""
        send_command(self.dev, self.main_window, b'DACCAL', b'OK',
                     "DAC calibration performed.")
        get_dac_calibration(self.dev, self.main_window)

    def shunt_calibration_changed_callback(self):
        """Set the shunt calibration values from the input fields."""
        for i in range(0, 4):
            try:
                shunt_calibration[i] = float(
                    self.main_window.calibration_window.R[i].text())
                # hardware_calibration_shuntvalues[i].setStyleSheet("")
            except ValueError:  # If the input field cannot be interpreted as a number, color it red
                self.main_window.calibration_window.R[i].setStyleSheet(
                    "")

    def set_calibration(self):
        """Save all calibration values to the device's flash memory."""
        set_dac_calibration(self.dev, self.main_window)
        set_offset(self.dev, self.main_window,
                   current_offset, potential_offset)
        set_shunt_calibration(self.dev, self.main_window, shunt_calibration)

    def get_calibration(self):
        """Retrieve all calibration values from the device's flash memory."""
        get_dac_calibration(self.dev, self.main_window)
        self.get_offset()
        get_shunt_calibration(self.dev, self.main_window, shunt_calibration)

    def set_output_from_gui(self):
        """Output data to the DAC from the GUI input field (hardware tab, manual control)."""
        value_units_index = self.main_window.manual_window.comboBox_2.currentIndex()
        if value_units_index == 0:  # Potential (V)
            try:
                value = float(
                    self.main_window.manual_window.lineEdit_13.text())
            except ValueError:
                QMessageBox.critical(
                    self.main_window, "Not a number", "<font color=\"White\">The value you have entered is not a floating-point number.")
                self.main_window.setStyleSheet(
                    "color: black;  background-color: black")
                return
        elif value_units_index == 1:  # Current (mA)
            try:
                value = float(
                    self.main_window.manual_window.lineEdit_13.text())
            except ValueError:
                QMessageBox.critical(
                    self.main_window, "Not a number", "<font color=\"White\">TThe value you have entered is not a floating-point number.")
                self.main_window.setStyleSheet(
                    "color: black;  background-color: black")
                return
        elif value_units_index == 2:  # DAC Code
            try:
                value = int(self.main_window.manual_window.lineEdit_13.text())
            except ValueError:
                QMessageBox.critical(
                    self.main_window, "Not a number", "<font color=\"White\">TThe value you have entered is not an integer number.")
                self.main_window.setStyleSheet(
                    "color: black;  background-color: black")
                return
        else:
            return
        self.set_output(value_units_index, value)

    def set_current_range(self):
        """Switch the current range based on the GUI dropdown selection."""
        global currentrange
        index = self.main_window.manual_window.current_range_box.currentIndex()
        commandstring = [b'RANGE 1',b'RANGE 2',b'RANGE 3',b'RANGE 4'][index]
        if send_command(self.dev, self.main_window, commandstring, b'OK'):
            self.main_window.current_range_monitor.setText(
                current_range_list[index])
            currentrange = index

    def set_output(self, value_units_index, value):
        """Output data to the DAC; units can be either V (index 0), mA (index 1), or raw counts (index 2)."""
        self.potential_apply = value
        if value_units_index == 0:
            send_command(self.dev, self.main_window,b'DACSET '+decimal_to_dac_bytes(value/13.4*2.**19+int(round(potential_offset/4.))), b'OK')
        elif value_units_index == 1:
            if currentrange == 0:
                send_command(self.dev, self.main_window,b'DACSET '+decimal_to_dac_bytes(value/(250./shunt_calibration[currentrange])*2.**19+int(round(current_offset/4.))), b'OK')
            if currentrange == 1:
                send_command(self.dev, self.main_window,b'DACSET '+decimal_to_dac_bytes(value/(25./shunt_calibration[currentrange])*2.**19+int(round(current_offset/4.))), b'OK')
            if currentrange == 2:
                send_command(self.dev, self.main_window,b'DACSET '+decimal_to_dac_bytes(value/(0.25/shunt_calibration[currentrange])*2.**19+int(round(current_offset/4.))), b'OK')
            if currentrange == 3:
                send_command(self.dev, self.main_window,b'DACSET '+decimal_to_dac_bytes(value/(0.0025/shunt_calibration[currentrange])*2.**19+int(round(current_offset/4.))), b'OK')
        elif value_units_index == 2:
            send_command(self.dev, self.main_window,b'DACSET '+decimal_to_dac_bytes(value), b'OK')

    def wait_for_adcread(self):
        """Wait for the duration specified in the busyloop_interval."""
        if self.busyloop_interval == 0:
            return  # On Linux/Mac, system timing is used instead of the busyloop
        else:
            # Sleep for some time to prevent wasting too many CPU cycles
            time.sleep(self.busyloop_interval/2.)
            # app.processEvents()  # Update the GUI
            while timeit.default_timer() < time_of_last_adcread + self.busyloop_interval:
                # Busy loop (this is the only way to get accurate timing on MS Windows)
                pass

    def potential_to_string(self, potential_in_V):
        """Format the measured potential into a string with appropriate units and number of significant digits."""
        return u"%+6.3f V" % potential_in_V

    def current_to_string(self, currentrange, current_in_mA):
        """Format the measured current into a string with appropriate units and number of significant digits."""
        abs_value = abs(current_in_mA)
        if currentrange == 0:
            if abs_value <= 99.995:
                return u"%+6.2f mA"%current_in_mA
            else:
                return u"%+6.1f mA"%current_in_mA
        elif currentrange == 1:
            if abs_value <= 9.9995:
                return u"%+6.3f mA"%current_in_mA
            else:
                return u"%+6.2f mA"%current_in_mA
        elif currentrange == 2:
            if abs_value < 9.9995e-2:
                return u"%+06.2f µA"%(current_in_mA*1e3)
            else:
                return u"%+6.1f µA"%(current_in_mA*1e3)
        elif currentrange == 3:
            return u"%+6.3f µA"%(current_in_mA*1e3)

    def read_potential_current(self):
        """Read the most recent potential and current values from the device's ADC."""
        global potential, current, raw_potential, raw_current, time_of_last_adcread
        self.wait_for_adcread()
        time_of_last_adcread = timeit.default_timer()
        self.dev.write(0x01,b'ADCREAD') # 0x01 = write address of EP1
        response = bytes(self.dev.read(0x81,64)) # 0x81 = read address of EP1
        if response != b'WAIT': # 'WAIT' is received if a conversion has not yet finished
            raw_potential = twocomplement_to_decimal(response[0], response[1], response[2])
            raw_current = twocomplement_to_decimal(response[3], response[4], response[5])
            potential = (raw_potential-potential_offset)/2097152.*13.4 # Calculate potential in V, compensating for offset
            if currentrange == 0:# Calculate current in mA, taking current range into account and compensating for offset
                current = (raw_current-current_offset)/2097152.*250./(shunt_calibration[currentrange])
            elif currentrange == 1:
                current = (raw_current-current_offset)/2097152.*25./(shunt_calibration[currentrange])
            elif currentrange == 2:
                current = (raw_current-current_offset)/2097152.*0.25/(shunt_calibration[currentrange])
            elif currentrange == 3:
                current = (raw_current-current_offset)/2097152.*0.0025/(shunt_calibration[currentrange])
            self.main_window.potential_monitor.setText(self.potential_to_string(potential))
            self.main_window.current_monitor.setText(self.current_to_string(currentrange, current))
            if logging_enabled: # If enabled, all measurements are appended to an output file (even in idle mode)
                try:
                    print("%.2f\t%e\t%e"%(time_of_last_adcread,potential,current*1e-3),file=open(hardware_log_filename.text(),'a',1)) # Output tab-separated data containing time (in s), potential (in V), and current (in A)
                except:
                    QMessageBox.critical(self.main_window, "Logging error!", "Logging error!")
                    # hardware_log_checkbox.setChecked(False) # Disable logging in case of file errors

    def zero_offset(self):
        """Calculate offset values in order to zero the potential and current."""
        if not check_state(self.state, [States.Idle]):
            return  # Device needs to be in the idle state for this
        # Average potential offset
        pot_offs = int(round(np.average(list(last_raw_potential_values))))
        # Average current offset
        cur_offs = int(round(np.average(list(last_raw_current_values))))
        print('-----')
        self.main_window.calibration_window.pot_offset_iut.setText(
            "%d" % pot_offs)
        self.main_window.calibration_window.curr_offset_input.setText(
            "%d" % cur_offs)
        self.offset_changed_callback()

    def zero_offset_(self):
        """Calculate offset values in order to zero the potential and current."""
        # if not check_state(state,[States.Idle]):
        # return  # Device needs to be in the idle state for this
        # Average potential offset
        pot_offs = int(round(np.average(list(last_raw_potential_values))))
        # Average current offset
        cur_offs = int(round(np.average(list(last_raw_current_values))))
        
        self.main_window.calibration_window.pot_offset_input.setText("%d" % pot_offs)
        self.main_window.calibration_window.curr_offset_input.setText("%d" % cur_offs)
        print('---> auto zero2')
        self.offset_changed_callback()
        self.potential = potential
        self.current = current

    def offset_changed_callback(self):
        """Set the potential and current offset from the input fields."""
        global potential_offset, current_offset
        try:
            potential_offset = int(
                self.main_window.calibration_window.pot_offset_input.text())
            # self.main_window.calibration_window.pot_offset_input.setStyleSheet("")
        except ValueError:  # If the input field cannot be interpreted as a number, color it red
            # hardware_calibration_potential_offset.setStyleSheet(
            #     "")
            pass
        try:
            current_offset = int(
                self.main_window.calibration_window.curr_offset_input.text())
            # self.main_window.calibration_window.curr_offset_input.setStyleSheet("")
        except ValueError:  # If the input field cannot be interpreted as a number, color it red
            self.main_window.calibration_window.curr_offset_input.setStyleSheet("")

    def idle_init(self):
        """Perform some necessary initialization before entering the Idle state."""
        global potential_plot_curve, current_plot_curve, legend
        self.main_window.dynamicPlt.clear()
        try:
            legend.scene().removeItem(legend)  # Remove any previous legends
        except AttributeError:
            pass  # In case the legend was already removed
        except NameError:
            pass  # In case a legend has never been created
        self.main_window.dynamicPlt.setLabel('bottom', 'Sample #', units="")
        self.main_window.dynamicPlt.setLabel('left', 'Value', units="")
        self.main_window.dynamicPlt.enableAutoRange()
        self.main_window.dynamicPlt.setXRange(0, 200, update=True)
        legend = self.main_window.dynamicPlt.addLegend(
            size=(5, 20), offset=(10, 10))
        potential_plot_curve = self.main_window.dynamicPlt.plot(
            pen='g', name='Potential (V)')
        current_plot_curve = self.main_window.dynamicPlt.plot(
            pen='r', name='Current (mA)')
        self.state = States.Idle  # Proceed to the Idle state

    def update_live_graph(self):
        """Add newly measured potential and current values to their respective buffers and update the plot curves."""
        last_potential_values.append(potential)
        last_current_values.append(current)
        last_raw_potential_values.append(raw_potential)
        last_raw_current_values.append(raw_current)
        xvalues = range(last_potential_values.maxlen -
                        len(last_potential_values), last_potential_values.maxlen)
        potential_plot_curve.setData(xvalues, list(last_potential_values))
        current_plot_curve.setData(xvalues, list(last_current_values))

    def auto_current_range(self):
        global cv_range_checkboxes
        """Automatically switch the current range based on the measured current; returns a number of measurements to skip (to suppress artifacts)."""
        global currentrange, overcounter, undercounter
        if currentrange == 0:
            relativecurrent = abs(current/(2000.))
        elif currentrange == 1:
            relativecurrent = abs(current/(20.))
        elif currentrange == 2:
            relativecurrent = abs(current/(0.2))
        elif currentrange == 3:
            relativecurrent = abs(current/(0.002))
        if relativecurrent > 1.05 and currentrange != 0 and cv_range_checkboxes[currentrange-1].isChecked(): # Switch to higher current range (if possible) after three detections
            overcounter += 1
        else:
            overcounter = 0
        if relativecurrent < 0.0095 and currentrange != 3 and cv_range_checkboxes[currentrange+1].isChecked(): # Switch to lower current range (if possible) after three detections
            undercounter += 1
        else:
            undercounter = 0
        if overcounter > 3:
            currentrange -= 1
            self.main_window.manual_window.current_range_box.setCurrentIndex(currentrange)
            self.set_current_range()
            overcounter = 0
            return 2 # Skip next two measurements to suppress artifacts
        elif undercounter > 3:
            currentrange += 1
            self.main_window.manual_window.current_range_box.setCurrentIndex(currentrange)
            self.set_current_range()
            undercounter = 0
            return 2 # Skip next two measurements to suppress artifacts
        else:
            return 0

    def current_range_from_current(self, current):
        """Return the current range that best corresponds to a given current."""
        current = abs(current)
        if current <= 0.002:
            return 3 # Lowest current range (2 uA)
        elif current <= 0.2:
            return 2 # Intermediate current range (200 uA)
        elif current <= 20.:
            return 1 # Intermediate current range (20 mA)
        else:
            return 0 # Highest current range (200 mA)

    def get_next_enabled_current_range(self, desired_currentrange):
        global cv_range_checkboxes
        """Return an enabled current range that best corresponds to a desired current range."""
        range_found = False
        found_currentrange = desired_currentrange
        for i in range(desired_currentrange,-1,-1): # Look for an enabled current range, going up in current range
            if cv_range_checkboxes[i].isChecked():
                found_currentrange = i
                range_found = True
                break
        if not range_found:
            for i in range(desired_currentrange,4): # Look for an enabled current range, going down in current range
                if cv_range_checkboxes[i].isChecked():
                    found_currentrange = i
                    break
        return found_currentrange

    def cd_start(self, cd_parameters):
        global start_stop, cd_charges, cd_currentsetpoint, cd_starttime, cd_currentcycle, cd_time_data, cd_potential_data, cd_current_data, cd_plot_curves, cd_outputfile_raw, cd_outputfile_capacities

        if check_state(self.state, [States.Idle, States.Stationary_Graph, States.Measuring_start]):
            cd_outputfile_raw = open(cd_parameters['filename'], 'w', 1)
            cd_outputfile_raw.write(f"\t  Lower bound (V) = {cd_parameters['lbound']} \r\n\
            Upper bound (V) = {cd_parameters['ubound']} \r\n\
            Charge curent (µA) = {cd_parameters['chargecurrent']} \r\n\
            Discharge current (µA) = {cd_parameters['dischargecurrent']} \r\n\
            Number of half cycles = {cd_parameters['numcycles']} \r\n\
            Samples to average = {cd_parameters['numsamples']} \r\n")
            cd_outputfile_raw.write(
                "Elapsed time(s)\tPotential(V)\tCurrent(A)\n")
            base, extension = os.path.splitext(cd_parameters['filename'])
            cd_outputfile_capacities = open(
                base+'_capacities'+extension, 'w', 1)
            cd_outputfile_capacities.write(
                "Cycle number\tCharge capacity (Ah)\tDischarge capacity (Ah)\n")
            cd_currentcycle = 1
            cd_charges = []
            cd_plot_curves = []
            cd_currentsetpoint = cd_parameters['chargecurrent']
            self.set_current_range()
            self.set_output(1, cd_currentsetpoint)  # Set current to setpoint
            set_control_mode(self.dev, self.main_window,
                             True)  # Galvanostatic control
            time.sleep(.2)  # Allow DAC some time to settle
            cd_starttime = timeit.default_timer()
            # Holds averaged data for elapsed time
            cd_time_data = AverageBuffer(cd_parameters['numsamples'])
            # Holds averaged data for potential
            cd_potential_data = AverageBuffer(cd_parameters['numsamples'])
            # Holds averaged data for current
            cd_current_data = AverageBuffer(cd_parameters['numsamples'])
            set_cell_status(self.dev, self.main_window, True)  # Cell on
            try:  # Set up the plotting area
                legend.scene().removeItem(legend)
            except AttributeError:
                pass
            self.main_window.dynamicPlt.clear()
            self.main_window.dynamicPlt.enableAutoRange()
            self.main_window.dynamicPlt.setLabel(
                'bottom', 'Inserted/extracted charge', units="Ah")
            self.main_window.dynamicPlt.setLabel(
                'left', 'Potential', units="V")
            cd_plot_curves.append(self.main_window.dynamicPlt.plot(pen='y'))
            self.state = States.Measuring_CD

    def cd_update(self, cd_parameters):
        """Add a new data point to the charge/discharge measurement (should be called regularly)."""
        global cd_currentsetpoint, cd_currentcycle
        elapsed_time = timeit.default_timer()-cd_starttime
        # End of charge/discharge measurements
        if cd_currentcycle > cd_parameters['numcycles'] or elapsed_time > 60*3:
            self.cd_stop(interrupted=False)
        else:  # Continue charge/discharge measurement process
            self.read_potential_current()  # Read new potential and current
            cd_time_data.add_sample(elapsed_time)
            cd_potential_data.add_sample(potential)
            cd_current_data.add_sample(1e-3*current)  # Convert mA to A
            # A new average was just calculated
            if len(cd_time_data.samples) == 0 and len(cd_time_data.averagebuffer) > 0:
                cd_outputfile_raw.write("%e\t%e\t%e\n" % (
                    cd_time_data.averagebuffer[-1], cd_potential_data.averagebuffer[-1], cd_current_data.averagebuffer[-1]))  # Write it out
                charge = np.abs(scipy.integrate.cumtrapz(cd_current_data.averagebuffer,
                                                            cd_time_data.averagebuffer, initial=0.)/3600.)  # Cumulative charge in Ah
                # Update the graph
                cd_plot_curves[cd_currentcycle -
                               1].setData(charge, cd_potential_data.averagebuffer)
            # A potential cut-off has been reached
            if (cd_currentsetpoint > 0 and potential > cd_parameters['ubound']) or (cd_currentsetpoint < 0 and potential < cd_parameters['lbound']):
                # Switch from the discharge phase to the charge phase or vice versa
                if cd_currentsetpoint == cd_parameters['chargecurrent']:
                    cd_currentsetpoint = cd_parameters['dischargecurrent']
                else:
                    cd_currentsetpoint = cd_parameters['chargecurrent']
                self.set_current_range()  # Set new current range
                # Set current to setpoint
                self.set_output(1, cd_currentsetpoint)
                # Start a new plot curve and append it to the plot area (keeping the old ones as well)
                cd_plot_curves.append(
                    self.main_window.dynamicPlt.plot(pen='y'))
                cd_charges.append(np.abs(np.trapz(
                    cd_current_data.averagebuffer, cd_time_data.averagebuffer)/3600.))  # Cumulative charge in Ah
                # Write out the charge and discharge capacities after both a charge and discharge phase (i.e. after cycle 2, 4, 6...)
                if cd_currentcycle % 2 == 0:
                    cd_outputfile_capacities.write("%d\t%e\t%e\n" % (
                        cd_currentcycle/2, cd_charges[cd_currentcycle-2], cd_charges[cd_currentcycle-1]))
                # Clear average buffers to prepare them for the next cycle
                for data in [cd_time_data, cd_potential_data, cd_current_data]:
                    data.clear()
                cd_currentcycle += 1  # Next cycle

    def cd_stop(self, interrupted=True):
        """Finish the charge/discharge measurement."""
        # global state
        if check_state(self.state, [States.Measuring_CD]):
            # self.main_window.button_start.setText("Start")
            # state = States.Stationary_Graph
            set_cell_status(self.dev, self.main_window, False)  # Cell off
            cd_outputfile_raw.close()
            cd_outputfile_capacities.close()
            self.state = States.Measuring_start
            # preview_cancel_button.show()

    def cv_sweep(self, time_elapsed, ustart, ustop, ubound, lbound, scanrate, n, cv_type):       
        """Generate the potential profile for a cyclic voltammetry sweep.

        Keyword arguments:
        time_elapsed -- the elapsed time
        ustart -- the start potential
        ustop -- the stop potential
        ubound -- the upper potential bound
        lbound -- the lower potential bound
        scanrate -- the scan rate
        n -- the number of scans
       
        Returns the potential as a function of the elapsed time; if the elapsed time exceeds the end of the CV sweep, returns None.
        """
        if cv_type == CV_MEASURE:
            if scanrate < 0:  # The rest of the function assumes a positive scan rate; a negative one is handled here by recursion
                try:
                    # Re-run the function with inverted potentials and scan rates and invert the result
                    return -self.cv_sweep(time_elapsed, -ustart, -ustop, -lbound, -ubound, -scanrate, n, cv_type)
                except TypeError:
                    return None  # If the result of the inverted function is None, it cannot be inverted, so return None
            # Potential difference to traverse in the initial stage (before potential reaches upper bound)
            srt_0 = ubound-ustart
            # Potential difference to traverse in the "cyclic stage" (repeated scans from upper to lower bound and back)
            srt_1 = (ubound-lbound)*2.*n
            # Potential difference to traverse in the final stage (from upper bound to stop potential)
            srt_2 = abs(ustop-ubound)
            srtime = scanrate*time_elapsed  # Linear potential sweep
            if srtime < srt_0:  # Initial stage
                self.currPotential = ustart+srtime  # Store previous Potential
                return ustart+srtime
            elif srtime < srt_0+srt_1:  # Cyclic stage
                srtime = srtime - srt_0
                self.prevPotential = self.currPotential
                self.currPotential = lbound + abs((srtime) % (2*(ubound-lbound))-(ubound-lbound))
                self.checkCycle()
                # print(f" self.currPotential = {self.currPotential}")
                return lbound + abs((srtime) % (2*(ubound-lbound))-(ubound-lbound))
            elif srtime < srt_0+srt_1+srt_2:  # Final stage
                srtime = srtime - srt_0 - srt_1
                if ustop > ubound:
                    self.prevPotential = self.currPotential
                    self.currPotential = ubound + srtime
                    self.checkCycle()
                    return ubound + srtime
                else:
                    self.prevPotential = self.currPotential
                    self.currPotential = ubound - srtime
                    self.checkCycle()
                    return ubound - srtime
            else:
                return None  # CV finished
        else:
            srtime = scanrate*time_elapsed
            if (ustart > ustop and ustart + srtime < ustop) or (ustart < ustop and ustart + srtime > ustop):
                return None # CV finished
            return ustart + srtime

    def checkCycle(self):
        if self.currentCycle % 2 == 0:
            if self.prevPotential > self.currPotential:
                self.currentCycle += 1
        else:
            if self.prevPotential < self.currPotential:
                self.currentCycle += 1

    

    def charge_from_cv(self, time_arr, current_arr):
        """Integrate current as a function of time to calculate charge between zero crossings."""
        zero_crossing_indices = []
        charge_arr = []
        running_index = 0
        while running_index < len(current_arr):
            counter = 0
            # Iterate over a block of positive currents
            while running_index < len(current_arr) and current_arr[running_index] >= 0.:
                running_index += 1
                counter += 1
            # Check if the block holds at least 10 values (this makes the counting immune to noise around zero crossings)
            if counter >= 10:
                # If so, append the index of the start of the block to the list of zero-crossing indices
                zero_crossing_indices.append(running_index-counter)
            counter = 0
            # Do the same for a block of negative currents
            while running_index < len(current_arr) and current_arr[running_index] <= 0.:
                running_index += 1
                counter += 1
            if counter >= 10:
                zero_crossing_indices.append(running_index-counter)
        for index in range(0, len(zero_crossing_indices)-1):  # Go over all zero crossings
            zc_index1 = zero_crossing_indices[index]  # Start index
            zc_index2 = zero_crossing_indices[index+1]  # End index
            # Integrate current over time using the trapezoid rule, convert coulomb to uAh
            charge_arr.append(np.trapz(
                current_arr[zc_index1:zc_index2], time_arr[zc_index1:zc_index2])*1000./3.6)
        return charge_arr

    def cv_start(self, cv_parameters):
        """Initialize the CV measurement."""
        global cv_time_data, cv_potential_data, cv_current_data, cv_plot_curve, cv_outputfile, skipcounter
        if check_state(self.state, [States.Idle, States.Stationary_Graph, States.Measuring_start]):
            cv_outputfile = open(cv_parameters['filename'], 'w', 1) # 1 means line-buffered
            if cv_parameters == CV_MEASURE:
                cv_outputfile.write(f"\t    Lower bound (V) = {cv_parameters['lbound']} \r\n\
                Upper bound (V) = {cv_parameters['ubound']} \r\n\
                Start potential (V) = {cv_parameters['startpot']} \r\n\
                Stop potential (V) = {cv_parameters['stoppot']} \r\n\
                Scan rate (mV/s) = {cv_parameters['scanrate']} \r\n\
                Number of cycles = {cv_parameters['numcycles']} \r\n\
                Samples to average = {cv_parameters['numsamples']} \r\n")
            else:
                cv_outputfile.write(f"\t    Lower bound (V) = None \r\n\
                Upper bound (V) = None \r\n\
                Start potential (V) = {cv_parameters['startpot']} \r\n\
                Stop potential (V) = {cv_parameters['stoppot']} \r\n\
                Scan rate (mV/s) = {cv_parameters['scanrate']} \r\n\
                Number of cycles = None \r\n\
                Samples to average = {cv_parameters['numsamples']} \r\n")
            cv_outputfile.write("Half Cycle\tPotential Apply(V)\tElapsed time(s)\tPotential(V)\tCurrent(A)\n")
            self.set_output(0, cv_parameters['startpot'])
            set_control_mode(self.dev, self.main_window, False)
            self.main_window.manual_window.current_range_box.setCurrentIndex(0) # Start at highest current range
            self.set_current_range()
            time.sleep(.1) # Allow DAC some time to settle
            # Holds averaged data for elapsed time
            cv_time_data = AverageBuffer(cv_parameters['numsamples']) 
            # Holds averaged data for potential
            cv_potential_data = AverageBuffer(cv_parameters['numsamples']) 
            # Holds averaged data for current
            cv_current_data = AverageBuffer(cv_parameters['numsamples']) 
            set_cell_status(self.dev, self.main_window, True) #Cell on
            time.sleep(.1)  # Allow feedback loop some time to settle
            self.read_potential_current()
            time.sleep(.1)
            # Two reads are necessary because each read actually returns the result of the previous conversion            
            self.read_potential_current()
            self.main_window.manual_window.current_range_box.setCurrentIndex(self.get_next_enabled_current_range(self.current_range_from_current(current))) # Autorange based on the measured current
            self.set_current_range()
            time.sleep(.1)
            self.read_potential_current()
            time.sleep(.1)
            self.read_potential_current()
            self.main_window.manual_window.current_range_box.setCurrentIndex(self.get_next_enabled_current_range(self.current_range_from_current(current))) # Another autorange, just to be sure
            self.set_current_range()
            try: # Set up the plotting area
                legend.scene().removeItem(legend)
            except AttributeError:
                pass
            self.main_window.dynamicPlt.clear()
            self.main_window.dynamicPlt.enableAutoRange()
            self.main_window.dynamicPlt.setLabel(
                'bottom', 'Potential', units="V")
            self.main_window.dynamicPlt.setLabel('left', 'Current', units="A")
            cv_plot_curve = self.main_window.dynamicPlt.plot(pen='y') # Plot CV in yellow
            self.state = States.Measuring_CV
            skipcounter = 2 # Skip first two data points to suppress artifacts
            cv_parameters['starttime'] = timeit.default_timer()

    def cv_update(self, cv_parameters):
        """Add a new data point to the CV measurement (should be called regularly)."""
        global skipcounter
        elapsed_time = timeit.default_timer()-cv_parameters['starttime']
        cv_output = self.cv_sweep(elapsed_time, cv_parameters['startpot'], cv_parameters['stoppot'],
                                  cv_parameters['ubound'], cv_parameters['lbound'], cv_parameters['scanrate'], cv_parameters['numcycles'], cv_parameters["cv_type"])
        if cv_output == None:  # This signifies the end of the CV scan
            self.cv_stop(interrupted=False)
        else:
            self.set_output(0, cv_output)
            self.read_potential_current()  # Read new potential and current
            if skipcounter == 0:  # Process new measurements
                cv_time_data.add_sample(elapsed_time)
                cv_potential_data.add_sample(potential)
                cv_current_data.add_sample(1e-3*current)  # Convert from mA to A
                # Check if a new average was just calculated
                if len(cv_time_data.samples) == 0 and len(cv_time_data.averagebuffer) > 0:
                    cv_outputfile.write("%d\t%e\t%e\t%e\t%e\n" % (
                        self.currentCycle, self.potential_apply, cv_time_data.averagebuffer[-1], cv_potential_data.averagebuffer[-1], cv_current_data.averagebuffer[-1]))  # Write it out
                    cv_plot_curve.setData(
                        cv_potential_data.averagebuffer, cv_current_data.averagebuffer)  # Update the graph
                skipcounter = self.auto_current_range()  # Update the graph
            else:  # Wait until the required number of data points is skipped
                skipcounter -= 1

    def cv_stop(self, interrupted=True):
        """Finish the CV measurement."""
        if check_state(self.state, [States.Measuring_CV]):
            set_cell_status(self.dev, self.main_window, False)      #Cell Off
            cv_outputfile.close()
            self.state = States.Measuring_start

    def rate_start(self, rate_parameters):
        """Initialize the rate testing measurement."""
        global crate_index, rate_halfcycle_countdown, rate_chg_charges, rate_dis_charges, rate_outputfile_raw, rate_outputfile_capacities, rate_starttime, rate_time_data, rate_potential_data, rate_current_data, rate_plot_scatter_chg, rate_plot_scatter_dis, legend
        if check_state(self.state, [States.Idle, States.Stationary_Graph, States.Measuring_start]):
            crate_index = 0  # Index in the list of C-rates
            # Holds amount of remaining half cycles
            rate_halfcycle_countdown = 2*rate_parameters['numcycles']
            rate_chg_charges = []  # List of measured charge capacities
            rate_dis_charges = []  # List of measured discharge capacitiesa
            # Apply positive current for odd half cycles (charge phase) and negative current for even half cycles (discharge phase)
            rate_outputfile_raw = open(rate_parameters['filename'], 'w', 1)
            rate_outputfile_raw.write(f"\t  Lower bound (V) = {rate_outputfile_raw['rate_lbound']} \r\n\
            Upper bound (V) = {rate_outputfile_raw['rate_ubound']} \r\n\
            C (µAh) = {rate_outputfile_raw['rate_one_c_current']} \r\n\
            C-rates = {rate_outputfile_raw['rate_crates']} \r\n\
            Cycles per C-rate = {rate_outputfile_raw['rate_numcycles']} \r\n ")
            rate_outputfile_raw.write(
                "Elapsed time(s)\tPotential(V)\tCurrent(A)\n")
            base, extension = os.path.splitext(rate_parameters['filename'])
            # This file will contain capacity data for each C-rate
            rate_outputfile_capacities = open(
                base+'_capacities'+extension, 'w', 1)
            rate_outputfile_capacities.write(
                "C-rate\tCharge capacity (Ah)\tDischarge capacity (Ah)\n")
            rate_current = rate_parameters['currents'][crate_index] if rate_halfcycle_countdown % 2 == 0 else - \
                rate_parameters['currents'][crate_index]
            self.set_current_range()  # Set new current range
            self.set_output(1, rate_current)  # Set current to setpoint
            set_control_mode(self.dev, self.main_window,
                             True)  # Galvanostatic control
            time.sleep(.2)  # Allow DAC some time to settle
            rate_starttime = timeit.default_timer()
            numsamples = max(
                1, int(36./rate_parameters['crates'][crate_index]))
            # Holds averaged data for elapsed time
            rate_time_data = AverageBuffer(numsamples)
            # Holds averaged data for potential
            rate_potential_data = AverageBuffer(numsamples)
            # Holds averaged data for current
            rate_current_data = AverageBuffer(numsamples)
            set_cell_status(self.dev, self.main_window, True)  # Cell on
            try:  # Set up the plotting area
                legend.scene().removeItem(legend)
            except AttributeError:
                pass
            except NameError:
                pass  # In case a legend has never been created
            self.main_window.dynamicPlt.clear()
            legend = self.main_window.dynamicPlt.addLegend()
            self.main_window.dynamicPlt.enableAutoRange()
            self.main_window.dynamicPlt.setLabel('bottom', 'C-rate')
            self.main_window.dynamicPlt.setLabel(
                'left', 'Inserted/extracted charge', units="Ah")
            # Plot charge capacity as a function of C-rate with red circles
            rate_plot_scatter_chg = self.main_window.dynamicPlt.plot(
                symbol='o', pen=None, symbolPen='r', symbolBrush='r', name='Charge')
            rate_plot_scatter_dis = self.main_window.dynamicPlt.plot(symbol='o', pen=None, symbolPen=(100, 100, 255), symbolBrush=(
                100, 100, 255), name='Discharge')  # Plot discharge capacity as a function of C-rate with blue circles
            self.state = States.Measuring_Rate

    def rate_update(self, rate_parameters):
        """Add a new data point to the rate testing measurement (should be called regularly)."""
        global crate_index, rate_halfcycle_countdown
        elapsed_time = timeit.default_timer()-rate_starttime
        self.read_potential_current()
        rate_time_data.add_sample(elapsed_time)
        rate_potential_data.add_sample(potential)
        rate_current_data.add_sample(1e-3*current)  # Convert mA to A
        # A new average was just calculated
        if len(rate_time_data.samples) == 0 and len(rate_time_data.averagebuffer) > 0:
            rate_outputfile_raw.write("%e\t%e\t%e\n" % (
                rate_time_data.averagebuffer[-1], rate_potential_data.averagebuffer[-1], rate_current_data.averagebuffer[-1]))  # Write it out
        # A potential cut-off has been reached
        if (rate_halfcycle_countdown % 2 == 0 and potential > rate_parameters['ubound']) or (rate_halfcycle_countdown % 2 != 0 and potential < rate_parameters['lbound']):
            rate_halfcycle_countdown -= 1
            if rate_halfcycle_countdown == 1:  # Last charge cycle for this C-rate, so calculate and plot the charge capacity
                charge = np.abs(scipy.integrate.trapz(
                    rate_current_data.averagebuffer, rate_time_data.averagebuffer)/3600.)  # Charge in Ah
                rate_chg_charges.append(charge)
                rate_plot_scatter_chg.setData(
                    rate_parameters['crates'][0:crate_index+1], rate_chg_charges)
            elif rate_halfcycle_countdown == 0:  # Last discharge cycle for this C-rate, so calculate and plot the discharge capacity, and go to the next C-rate
                charge = np.abs(scipy.integrate.trapz(
                    rate_current_data.averagebuffer, rate_time_data.averagebuffer)/3600.)  # Charge in Ah
                rate_dis_charges.append(charge)
                rate_plot_scatter_dis.setData(
                    rate_parameters['crates'][0:crate_index+1], rate_dis_charges)
                rate_outputfile_capacities.write("%e\t%e\t%e\n" % (
                    rate_parameters['crates'][crate_index], rate_chg_charges[-1], rate_dis_charges[-1]))
                # Last C-rate was measured
                if crate_index == len(rate_parameters['crates'])-1:
                    self.rate_stop(interrupted=False)
                    return
                else:  # New C-rate
                    crate_index += 1
                    # Set the amount of remaining half cycles for the new C-rate
                    rate_halfcycle_countdown = 2 * \
                        rate_parameters['numcycles']
                    self.set_output(1, 0.)  # Set zero current while range switching
                    self.set_current_range.setCurrentIndex(self.current_range_from_current(
                        rate_parameters['currents'][crate_index]))  # Determine the proper current range for the new setpoint
                    self.set_current_range()  # Set new current range
                    # Set an appropriate amount of samples to average for the new C-rate; results in approx. 1000 points per curve
                    numsamples = max(
                        1, int(36./rate_parameters['crates'][crate_index]))
                    for data in [rate_time_data, rate_potential_data, rate_current_data]:
                        data.number_of_samples_to_average = numsamples
            # Apply positive current for odd half cycles (charge phase) and negative current for even half cycles (discharge phase)
            rate_current = rate_parameters['currents'][crate_index] if rate_halfcycle_countdown % 2 == 0 else - \
                rate_parameters['currents'][crate_index]
            self.set_output(1, rate_current)  # Set current to setpoint
            # Clear average buffers to prepare them for the next cycle
            for data in [rate_time_data, rate_potential_data, rate_current_data]:
                data.clear()

    def rate_stop(self, interrupted=True):
        """Finish the rate testing measurement."""
        if check_state(self.state, [States.Measuring_Rate]):
            # Keep displaying the last plot until the user clicks a button
            set_cell_status(self.dev, self.main_window, False)      #cell off
            rate_outputfile_raw.close()
            rate_outputfile_capacities.close()
            self.state = States.Measuring_start

    def dpv_start(self, dpv_parameters):
        """Initialize the rate testing measurement."""
        global dpv_outputfile
        if check_state(self.state, [States.Idle, States.Stationary_Graph, States.Measuring_start]):
            if dpv_parameters['direct'] == 0:
                direct = "RAISING"
            else:
                direct = "FALLING"
            dpv_outputfile = open(dpv_parameters['filename'], 'w', 1) # 1 means line-buffered
            dpv_outputfile.write(f"segments = {dpv_parameters['segments']} \r\n\
                direct = {direct} \r\n\
                Init potential (V) = {dpv_parameters['init_potential']} \r\n\
                Upper potential (V) = {dpv_parameters['upper_potential']} \r\n\
                Lower potential (mV/s) = {dpv_parameters['lower_potential']} \r\n\
                Final potential (mV) = {dpv_parameters['final_potential']} \r\n\
                Height dpv (mV)= {dpv_parameters['height_dpv']} \r\n\
                Width dpv (mV)= {dpv_parameters['width_dpv']} \r\n\
                Period dpv (mV)= {dpv_parameters['period_dpv']} \r\n\
                Increment dpv (mV)= {dpv_parameters['increment_dpv']} \r\n\
                Post pulse width = {dpv_parameters['post_pulse_width']} \r\n\
                Pre pulse width = {dpv_parameters['pre_pulse_width']} \r\n")
            dpv_outputfile.write("\tElapsed time(miliSecond)\tPotential(V)\tCurrent(A)\tDeltaCurrent\n")
            set_cell_status(self.dev, self.main_window, True) #Cell on
            send_command(self.dev, self.main_window,b'DPV_MEASURE'    
                            + dpv_parameters['segments'].to_bytes(2, 'big')
                            + dpv_parameters['direct'].to_bytes(2, 'big')
                            + dpv_parameters['init_potential'].to_bytes(2, 'big')
                            + dpv_parameters['upper_potential'].to_bytes(2, 'big')
                            + dpv_parameters['lower_potential'].to_bytes(2, 'big')
                            + dpv_parameters['final_potential'].to_bytes(2, 'big')
                            + dpv_parameters['height_dpv'].to_bytes(2, 'big')
                            + dpv_parameters['width_dpv'].to_bytes(2, 'big')
                            + dpv_parameters['period_dpv'].to_bytes(2, 'big')
                            + dpv_parameters['increment_dpv'].to_bytes(2, 'big')
                            + dpv_parameters['post_pulse_width'].to_bytes(2, 'big')
                            + dpv_parameters['pre_pulse_width'].to_bytes(2, 'big'), b'OK')
            self.state = States.Measuring_DPV
           
    def dpv_update(self, dpv_parameters):
        self.dev.write(0x01,b'DPV_READ') # 0x01 = write address of EP1
        response = bytes(self.dev.read(0x81,USB_SIZE)) # 0x81 = read address of EP1
        if b'DPV_COMPLETE' in response:
            self.dpv_stop(dpv_parameters, interrupted=False)
        if b'DPV_DATA' in response:
            key_len = len(b'DPV_DATA')
            dataLength = response[key_len] +  response[key_len + 1]*10
            if dataLength != 0:
                self.dpv_Data += response[(key_len + 2 ): (key_len + 2 + dataLength)]
                self.dpv_Len += dataLength
                
    def dpv_stop(self, dpv_parameters, interrupted=True):
        """Finish the DPV measurement."""
        global dpv_outputfile, shunt_calibration
        timeStamp = 0
        prevCurr = 0
        fixedTime = 0
        dpv_handle_data = 0
        for count in range(0, self.dpv_Len, 6):
            diffCurr = 0
            writeDiffTime = 0
            # print(f"{hex(self.dpv_Data[count])} {hex(self.dpv_Data[count+1])} {hex(self.dpv_Data[count+2])} {hex(self.dpv_Data[count+3])} {hex(self.dpv_Data[count+4])} {hex(self.dpv_Data[count+5])}")
            raw_potential = twocomplement_to_decimal(self.dpv_Data[count], self.dpv_Data[count+1], self.dpv_Data[count+2])
            raw_current = twocomplement_to_decimal(self.dpv_Data[count+3], self.dpv_Data[count+4], self.dpv_Data[count+5])
            potential_temp = raw_potential/2097152.*13.4 # Calculate potential in V
            current_temp = raw_potential/2097152.*13.4/1000 # Calculate potential in V
            
            # print(f"current_temp = {current_temp} raw_potential = {potential_temp}")
            timeStamp += DPV_TIME_STAMP
            if dpv_handle_data == 0:
                if timeStamp + DPV_TIME_STAMP > fixedTime + dpv_parameters['period_dpv']:
                    fixedTime += dpv_parameters['period_dpv']
                    prevCurr = current_temp
                    dpv_handle_data = 1
            else:
                if timeStamp + DPV_TIME_STAMP > fixedTime + dpv_parameters['width_dpv']:
                    fixedTime += dpv_parameters['width_dpv']
                    diffCurr = current_temp - prevCurr
                    dpv_handle_data = 0
                    writeDiffTime = 1
            if writeDiffTime:
                dpv_outputfile.write("\t%e\t%e\t%e\t%e\n" % (timeStamp, potential_temp, current_temp, diffCurr))  # Write it out
            else:
                dpv_outputfile.write("\t%e\t%e\t%e\n" % (timeStamp, potential_temp, current_temp))
        # print(f"DATA LENGTH = {self.dpv_Len}")
        if check_state(self.state, [States.Measuring_DPV]):
            set_cell_status(self.dev, self.main_window, False)      #Cell Off
            dpv_outputfile.close()
            send_command(self.dev, self.main_window, b'DPV_STOP',b'OK')
            self.dpv_Data = []
            self.dpv_Len = 0
            self.state = States.Measuring_start

        
    def start(self):
        global start_stop, stop
        if self.state == States.NotConnected:
            not_connected_errormessage(self.main_window)
        elif self.state != States.NotConnected and start_stop:
            self.state = States.Measuring_start
            self.main_window.button_start.setText('Stop')
            self.status_Num = 0
            start_stop = 0
        elif stop:
            stop = 0
            self.main_window.button_start.setText('Stop')
            return
        else:
            self.main_window.button_start.setText('Start')
            stop = 1
            start_stop = 1

    def refresh(self):
        global start_stop, stop
        stop = 0
        start_stop = 1
        self.state = States.Idle_Init
        self.status_Num = 0
        self.reset_Status_bar()

    def reset_Status_bar(self):
        for status_bar in self.status_bar:
            status_bar.setStyleSheet('background-color: black;')

    def Status_bar_Blynk(self, pos):
        if time.time() - self.prev_timestamp > 1:
            self.status_State = not self.status_State
            self.prev_timestamp = time.time()
        if pos > 0:
            for count in range(pos):
                self.status_bar[count].setStyleSheet('background-color: yellow;')
        if self.state != States.Stationary_Graph:
            if self.status_State:
                self.status_bar[pos-1].setStyleSheet('background-color: red;')
            else:
                self.status_bar[pos-1].setStyleSheet('background-color: black;')
            
    def isUsbConnected(self):  
        retVal = False
        if self.checkUsbConnection == True:
            usb_vid_string = str(self.main_window.usb_vid.text())
            usb_pid_string = str(self.main_window.usb_pid.text())
            device =  usb.core.find(idVendor=int(usb_vid_string, 0),
                                 idProduct=int(usb_pid_string, 0))
            if device is not None:
                retVal = True
            else:
                QMessageBox.critical(
                    self.main_window, "USB disconnect", "<font color=\"White\">Check Usb connection ")
                self.main_window.setStyleSheet(
                        "color: black;  background-color: black")
                self.connect_disconnect_usb()
                self.checkUsbConnection = False
                retVal = False
        return retVal
    
    def write_to_usb(self, address, data):
        pass