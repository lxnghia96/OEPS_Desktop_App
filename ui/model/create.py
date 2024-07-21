import time
from .frame import Frame
from utils.util import *
from utils.global_var import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5 import uic
import sys
sys.path.append('.')
# from main import Frame


class Edit_Measure(QMainWindow):
    def __init__(self, main_window, _frame):
        global cv_range_checkboxes
        super().__init__()
        uic.loadUi('./ui/sub_window/create_window.ui', self)
        self.main_window = main_window
        self.comboBox.addItems(LIST_TECHNIQUES)
        self.comboBox.setEnabled(False)
        self.button_cancel.clicked.connect(self.exit_window)
        self.button_add.clicked.connect(self.add)
        self.choose_file.clicked.connect(self.choose_file_)
        self.ocp_button.clicked.connect(self.cv_get_ocp)
        self.checkBox_lsv.stateChanged.connect(self.Choose_Lsv)
        self.checkBox_cv.stateChanged.connect(self.Choose_Cv)
        self.raising_cb.stateChanged.connect(self.Choose_Rasing_Dpv)
        self.falling_cb.stateChanged.connect(self.Choose_Faling_Dpv)
        self.cv_numsamples.setText("1")
        self.cv_scanrate.editingFinished.connect(self.cv_scanrate_changed_callback)
        self.isEdit = False
        self.frame_ = Frame(self, self.main_window)
        self.frame_.parameters = _frame.parameters
        self.frame_.name_technique = _frame.name_technique
        self.dest_frame = _frame
        
        self.cd_parameter = {}
        self.cv_parameter = {}
        self.rate_parameter = {}
        self.dpv_parameter = {}

        self.cd_parameter['filename'] = self.frame_.parameters['value']['filename']
        self.cv_parameter['filename'] = self.frame_.parameters['value']['filename']
        self.rate_parameter['filename'] = self.frame_.parameters['value']['filename']
        self.dpv_parameter['filename'] = self.frame_.parameters['value']['filename']
        
        
        cv_range_checkboxes.append(self.checkBox_1)
        cv_range_checkboxes.append(self.checkBox_2)
        cv_range_checkboxes.append(self.checkBox_3)
        cv_range_checkboxes.append(self.checkBox_4)

        self.cv_parameter["cv_type"] = CV_MEASURE
        self.dpv_parameter["direct"] = DPV_RAISING

        self.index = 0
        self.id_ = 0
        self.rate_testing.hide()
        self.cyclic_voltammetry.hide()
        self.Differential_Pulse.hide()
        self.editData()
      

    def Choose_Rasing_Dpv(self):
        if True == self.raising_cb.isChecked():
            self.falling_cb.setCheckState(False)
            self.dpv_parameter["direct"] = DPV_RAISING
        else:
            self.falling_cb.setCheckState(True)
            self.dpv_parameter["direct"] = DPV_FALLING

    def Choose_Faling_Dpv(self):
        if True == self.falling_cb.isChecked():
            self.raising_cb.setCheckState(False)
            self.dpv_parameter["direct"] = DPV_FALLING

        else:
            self.raising_cb.setCheckState(True)
            self.dpv_parameter["direct"] = DPV_RAISING

    def Choose_Lsv(self):
        if True == self.checkBox_lsv.isChecked():
            self.checkBox_cv.setCheckState(False)
            self.cv_parameter["cv_type"] = LSV_MEASURE
        else:
            self.checkBox_cv.setCheckState(True)
            self.cv_parameter["cv_type"] = CV_MEASURE
        self.Show_Infomation_Cv_Lsv()
  
            
    def Choose_Cv(self):
        if True == self.checkBox_cv.isChecked():
            self.checkBox_lsv.setCheckState(False)
            self.cv_parameter["cv_type"] = CV_MEASURE
        else:
            self.checkBox_lsv.setCheckState(True)
            self.cv_parameter["cv_type"] = LSV_MEASURE
        self.Show_Infomation_Cv_Lsv()

    def Show_Infomation_Cv_Lsv(self):
        if self.cv_parameter["cv_type"] == CV_MEASURE:
            self.cv_lbound.show() 
            self.cv_ubound.show()
            self.cv_numcycles.show()
            pass
        else:
            self.cv_lbound.hide()    
            self.cv_ubound.hide()
            self.cv_numcycles.hide()
                
    def lsv_validate_parameters(self):
        if self.cv_parameter['scanrate'] == 0:
            QMessageBox.critical(
                self, "CV error", "<font color=\"White\">The scan rate cannot be zero.")
            return False
        if (self.cv_parameter['scanrate'] > 0) and (self.cv_parameter['stoppot'] < self.cv_parameter['startpot']):
            QMessageBox.critical(
                self, "CV error", "<font color=\"White\">For a positive scan rate, the start potential must be lower than the stop bound.")
            return False
        if (self.cv_parameter['scanrate'] < 0) and (self.cv_parameter['stoppot'] > self.cv_parameter['startpot']):
            QMessageBox.critical(
                self, "CV error", "<font color=\"White\">For a negative scan rate, the start potential must be higher than the stop bound.")
            return False
        return True
    
    def dpv_validate_parameters(self):
        if self.dpv_parameter['init_potential'] > self.dpv_parameter['upper_potential']:
            QMessageBox.critical(self, "DPV error", "<font color=\"White\"> the Init potential must be higher than the upper potential.")
            return False
        if self.dpv_parameter['height_dpv'] > (self.dpv_parameter['upper_potential'] - self.dpv_parameter['init_potential']):
            QMessageBox.critical(self, "DPV error", "<font color=\"White\"> the height potential must be smaller than diference of upper potential sub for init potential.")
            return False
        if self.dpv_parameter['increment_dpv'] > self.dpv_parameter['height_dpv']:
            QMessageBox.critical(self, "DPV error", "<font color=\"White\"> the increment potential must be smaller than the height potential.")
            return False
        return True
    
    def cv_validate_parameters(self):
        if self.cv_parameter['ubound'] < self.cv_parameter['lbound']:
            QMessageBox.critical(
                self, "CV error", "<font color=\"White\">The upper bound cannot be lower than the lower bound.")
            return False
        if self.cv_parameter['scanrate'] == 0:
            QMessageBox.critical(
                self, "CV error", "<font color=\"White\">The scan rate cannot be zero.")
            return False
        if (self.cv_parameter['scanrate'] > 0) and (self.cv_parameter['ubound'] < self.cv_parameter['startpot']):
            QMessageBox.critical(
                self, "CV error", "<font color=\"White\">For a positive scan rate, the start potential must be lower than the upper bound.")
            return False
        if (self.cv_parameter['scanrate'] < 0) and (self.cv_parameter['lbound'] > self.cv_parameter['startpot']):
            QMessageBox.critical(
                self, "CV error", "<font color=\"White\">For a negative scan rate, the start potential must be higher than the lower bound.")
            return False
        if self.cv_parameter['numsamples'] < 1:
            QMessageBox.critical(
                self, "CV error", "<font color=\"White\">The number of samples to average must be at least 1.")
            return False
        return True

    def cd_validate_parameters(self):
        """Check if the chosen charge/discharge parameters make sense. If so, return True."""
        if self.cd_parameter['ubound'] < self.cd_parameter['lbound']:
            QMessageBox.critical(self, "Charge/discharge error",
                                       "<font color=\"White\">The upper bound cannot be lower than the lower bound.")
            return False
        if self.cd_parameter['chargecurrent'] == 0.:
            QMessageBox.critical(
                self, "Charge/discharge error", "<font color=\"White\">The charge current cannot be zero.")
            return False
        if self.cd_parameter['dischargecurrent'] == 0.:
            QMessageBox.critical(
                self, "Charge/discharge error", "<font color=\"White\">The discharge current cannot be zero.")
            return False
        if self.cd_parameter['chargecurrent']*self.cd_parameter['dischargecurrent'] > 0:
            QMessageBox.critical(self, "Charge/discharge error",
                                       "<font color=\"White\">Charge and discharge current must have opposite sign.")
            return False
        if self.cd_parameter['numcycles'] <= 0:
            QMessageBox.critical(self, "Charge/discharge error",
                                       "<font color=\"White\">The number of half cycles must be positive and non-zero.")
            return False
        if self.cd_parameter['numsamples'] < 1:
            QMessageBox.critical(self, "Charge/discharge error",
                                       "<font color=\"White\">The number of samples to average must be at least 1.")
            return False
        return True

    def rate_validate_parameters(self):
        """Check if the chosen charge/discharge parameters make sense. If so, return True."""
        if self.rate_parameter['ubound'] < self.rate_parameter['lbound']:
            QMessageBox.critical(self, "Rate testing error",
                                       "<font color=\"White\">The upper bound cannot be lower than the lower bound.")
            return False
        if 0. in self.rate_parameter['currents']:
            QMessageBox.critical(
                self, "Rate testing error", "<font color=\"White\">The charge/discharge current cannot be zero.")
            return False
        if self.rate_parameter['numcycles'] <= 0:
            QMessageBox.critical(self, "Charge/discharge error",
                                       "<font color=\"White\">The number of half cycles must be positive and non-zero.")
            return False
        return True

    def choose_file_(self):
        """Open a file dialog and write the path of the selected file to a given entry field."""
        filedialog = QFileDialog()
        self.setStyleSheet("color: white;  background-color: black")
        if self.index == 0:
            tuple_file = filedialog.getSaveFileName(
                self, "Choose where to save the charge/discharge measurement data", "", "ASCII data (*.txt)", options=QFileDialog.DontConfirmOverwrite)
            file_name = tuple_file[0]
            self.cd_parameter['filename'] = file_name
            self.save_path.setText(self.cd_parameter['filename'])
        elif self.index == 1:
            tuple_file = filedialog.getSaveFileName(
                self, "Choose where to save the rate testing measurement data", "", "ASCII data (*.txt)", options=QFileDialog.DontConfirmOverwrite)
            file_name = tuple_file[0]
            self.rate_parameter['filename'] = file_name
            self.save_path.setText(self.rate_parameter['filename'])
        elif self.index == 2:
            tuple_file = filedialog.getSaveFileName(
                self, "Choose where to save the CV measurement data", "", "ASCII data (*.txt)", options=QFileDialog.DontConfirmOverwrite)
            file_name = tuple_file[0]
            self.cv_parameter['filename'] = file_name
            self.save_path.setText(self.cv_parameter['filename'])
        # file_entry_field.setText(file_name)
        self.setStyleSheet("color: black;  background-color: black")

        # return file_name

    def show_measure(self, index):
        if (index == 0):
            self.rate_testing.hide()
            self.cyclic_voltammetry.hide()
            self.Differential_Pulse.hide()
            self.charge_disch.show()
            self.index = index
        elif (index == 1):
            self.charge_disch.hide()
            self.cyclic_voltammetry.hide()
            self.Differential_Pulse.hide()
            self.rate_testing.show()
            self.index = index
        elif (index == 2):
            self.charge_disch.hide()
            self.rate_testing.hide()
            self.Differential_Pulse.hide()
            self.cyclic_voltammetry.show()
            self.index = index        
        else:
            self.charge_disch.hide()
            self.rate_testing.hide()
            self.cyclic_voltammetry.hide()
            self.Differential_Pulse.show()
            self.index = index

    def get_para(self, index):
        if index == 0:
            try:
                self.cd_parameter['lbound'] = float(self.cd_lbound.text())
                self.cd_parameter['ubound'] = float(self.cd_ubound.text())
                self.cd_parameter['chargecurrent'] = float(
                    self.cd_chargecurrent.text())/1e3
                self.cd_parameter['dischargecurrent'] = float(
                    self.cd_dischargecurrent.text())/1e3
                self.cd_parameter['numcycles'] = int(self.cd_numcycles.text())
                self.cd_parameter['numsamples'] = int(
                    self.cd_numsamples.text())
                # self.cd_parameter['filename'] = choose_file(
                #     "Choose where to save the charge/discharge measurement data")
                if self.cd_validate_parameters() and validate_file(self.main_window, self.cd_parameter['filename']):
                    parameters = {'id': self.id_, 'type': 'cd',
                                  'value': self.cd_parameter}
                    return parameters
                else:
                    return False
            except ValueError:
                QMessageBox.critical(
                self, "Cd error", "<font color=\"White\">Input parameter is not correct.")
                return False
        elif index == 1:
            try:
                self.rate_parameter['lbound'] = float(self.rate_lbound.text())
                self.rate_parameter['ubound'] = float(self.rate_ubound.text())
                self.rate_parameter['one_c_current'] = float(
                    self.rate_one_c_current.text())/1e3
                self.rate_parameter['numcycles'] = int(
                    self.rate_numcycles.text())
                self.rate_parameter['crates'] = [
                    float(x) for x in self.rate_crates.text().split(",")]
                self.rate_parameter['currents'] = [
                    self.rate_parameter['one_c_current']*rc for rc in self.rate_parameter['crates']]
                self.rate_parameter['numsamples'] = 1
                # self.rate_parameter['filename'] = choose_file(
                #     "Choose where to save the rate testing measurement data")
                if self.rate_validate_parameters() and validate_file(self.main_window, self.rate_parameter['filename']):
                    parameters = {'id': self.id_, 'type': 'rate',
                                  'value': self.rate_parameter}
                    return parameters
                else:
                    return False
            except ValueError:
                QMessageBox.critical(
                self, "rate error", "<font color=\"White\">Input parameter is not correct.")
                return False
        elif index == 2:
            try:
                if self.cv_parameter["cv_type"] == CV_MEASURE:
                    self.cv_parameter['lbound'] = float(self.cv_lbound.text())
                    self.cv_parameter['ubound'] = float(self.cv_ubound.text())
                    self.cv_parameter['startpot'] = float(self.cv_startpot.text())
                    self.cv_parameter['stoppot'] = float(self.cv_stoppot.text())
                    self.cv_parameter['scanrate'] = float(self.cv_scanrate.text())/1e3
                    self.cv_parameter['numcycles'] = int(self.cv_numcycles.text())
                    self.cv_parameter['numsamples'] = int(self.cv_numsamples.text())
                    if self.cv_validate_parameters() and validate_file(self.main_window, self.cv_parameter['filename']):
                        parameters = {'id': self.id_, 'type': 'cv',
                                    'value': self.cv_parameter}
                        return parameters
                    else:
                        return False
                else:
                    self.cv_parameter['lbound'] = 0
                    self.cv_parameter['ubound'] = 0
                    self.cv_parameter['startpot'] = float(self.cv_startpot.text())
                    self.cv_parameter['stoppot'] = float(self.cv_stoppot.text())
                    self.cv_parameter['scanrate'] = float(
                        self.cv_scanrate.text())/1e3
                    self.cv_parameter['numcycles'] = 0
                    self.cv_parameter['numsamples'] = int(
                        self.cv_numsamples.text())
                    if self.lsv_validate_parameters() and validate_file(self.main_window, self.cv_parameter['filename']):
                        parameters = {'id': self.id_, 'type': 'cv',
                                    'value': self.cv_parameter}
                        return parameters
                    else:
                        return False
            except ValueError:
                QMessageBox.critical(
                self, "Cv error", "<font color=\"White\">Input parameter is not correct.")
        elif index == 3:
            try:
                self.dpv_parameter['segments'] = int(self.segments.text())
                self.dpv_parameter['init_potential'] = int(self.init_potential.text())
                self.dpv_parameter['upper_potential'] = int(self.upper_potential.text())
                self.dpv_parameter['lower_potential'] = int(self.lower_potential.text())
                self.dpv_parameter['final_potential'] = int(self.final_potential.text())
                self.dpv_parameter['height_dpv'] = int(self.height_dpv.text())
                self.dpv_parameter['width_dpv'] = int(self.width_dpv.text())
                self.dpv_parameter['period_dpv'] = int(self.period_dpv.text())
                self.dpv_parameter['increment_dpv'] = int(self.increment_dpv.text())
                self.dpv_parameter['post_pulse_width'] = int(self.post_pulse_width.text())
                self.dpv_parameter['pre_pulse_width'] = int(self.pre_pulse_width.text())
                if self.dpv_validate_parameters() and validate_file(self.main_window, self.dpv_parameter['filename']):
                    parameters = {'id': self.id_, 'type': 'dpv',
                                'value': self.dpv_parameter}
                    return parameters
                else:
                    return False
            except ValueError:
                QMessageBox.critical(
                self, "DPV error", "<font color=\"White\">Input parameter is not correct.")
                return False
            
    def set_para(self, index):
        if index == 0:
            self.cd_lbound.setText(str(self.frame_.parameters['value']['lbound']))
            self.cd_ubound.setText(str(self.frame_.parameters['value']['ubound']))
            self.cd_chargecurrent.setText(str(self.frame_.parameters['value']['chargecurrent']*1e3))
            self.cd_dischargecurrent.setText(str(self.frame_.parameters['value']['dischargecurrent']*1e3))
            self.cd_numcycles.setText(str(self.frame_.parameters['value']['numcycles']))
            self.cd_numsamples.setText(str(self.frame_.parameters['value']['numsamples']))
        elif index == 1:
            self.rate_lbound.setText(str(self.frame_.parameters['value']['lbound']))
            self.rate_ubound.setText(str(self.frame_.parameters['value']['ubound']))
            self.rate_one_c_current.setText(str(self.frame_.parameters['value']['one_c_current']*1e3))
            self.rate_numcycles.setText(str(self.frame_.parameters['value']['numcycles']))
            self.rate_crates.setText(str(self.frame_.parameters['value']['crates']))
            self.rate_currents.setText(str(self.frame_.parameters['value']['currents']))
            self.cd_numsamples.setText(str(self.frame_.parameters['value']['numsamples']))
        elif index == 2:
            if self.frame_.parameters['value']['cv_type'] == 0 :
                self.cv_lbound.setText(str(self.frame_.parameters['value']['lbound']))
                self.cv_ubound.setText(str(self.frame_.parameters['value']['ubound']))
                self.cv_startpot.setText(str(self.frame_.parameters['value']['startpot']))
                self.cv_stoppot.setText(str(self.frame_.parameters['value']['stoppot']))
                self.cv_scanrate.setText(str(self.frame_.parameters['value']['scanrate']))
                self.cv_numcycles.setText(str(self.frame_.parameters['value']['numcycles']))
                self.cv_numsamples.setText(str(self.frame_.parameters['value']['numsamples']))
            else:
                self.cv_lbound.setText("0")
                self.cv_ubound.setText("0")
                self.cv_startpot.setText(str(self.frame_.parameters['value']['startpot']))
                self.cv_stoppot.setText(str(self.frame_.parameters['value']['stoppot']))
                self.cv_scanrate.setText(str(self.frame_.parameters['value']['scanrate']))
                self.cv_numcycles.setText("0")
                self.cv_numsamples.setText(str(self.frame_.parameters['value']['numsamples']))
        elif index == 3:
            self.segments.setText(str(self.frame_.parameters['value']['segments']))
            self.init_potential.setText(str(self.frame_.parameters['value']['init_potential']))
            self.upper_potential.setText(str(self.frame_.parameters['value']['upper_potential']))
            self.lower_potential.setText(str(self.frame_.parameters['value']['lower_potential']))
            self.final_potential.setText(str(self.frame_.parameters['value']['final_potential']))
            self.height_dpv.setText(str(self.frame_.parameters['value']['height_dpv']))
            self.width_dpv.setText(str(self.frame_.parameters['value']['width_dpv']))
            self.period_dpv.setText(str(self.frame_.parameters['value']['period_dpv']))
            self.increment_dpv.setText(str(self.frame_.parameters['value']['increment_dpv']))
            self.post_pulse_width.setText(str(self.frame_.parameters['value']['post_pulse_width']))
            self.pre_pulse_width.setText(str(self.frame_.parameters['value']['pre_pulse_width']))
            if self.frame_.parameters["value"]['direct'] == DPV_RAISING:
                self.raising_cb.setCheckState(True)
                self.falling_cb.setCheckState(False)
            else:
                self.raising_cb.setCheckState(False)
                self.falling_cb.setCheckState(True)
            
    def cv_get_ocp(self):
        """Insert the currently measured (open-circuit) potential into the start potential input field."""
        try:
            self.cv_startpot.setText('%5.3f' % last_potential_values[-1])
        except:
            self.cv_startpot.setText('0')
    def cv_scanrate_changed_callback(self):
        pass
        """Calculate a suggested number of samples to average based on the entered value for the CV scan rate."""
        try:
            cv_scanrate = float(self.cv_scanrate.text())
            numsamples = int(20./abs(cv_scanrate))+1 # Aims for approx. one (averaged) measurement every 2 to 4 mV for scan rates up to 20 mV/s
            self.cv_numsamples.setText("%d"%numsamples)
        except:
            pass # Don't do anything in case the entered scan rate value is invalid

    def exit_window(self):
        self.close()

    def add(self):
        global listFrame
        self.frame_.parameters = self.get_para(self.index)
        if self.frame_.parameters:
            self.dest_frame.parameters = self.frame_.parameters

    def init_Value_Dpv(self):
        self.segments.setText("2")
        self.init_potential.setText("0000")
        self.upper_potential.setText("2000")
        self.lower_potential.setText("500")
        self.final_potential.setText("1000")
        self.height_dpv.setText("50")
        self.width_dpv.setText("100")
        self.period_dpv.setText("100")
        self.increment_dpv.setText("10")
        self.pre_pulse_width.setText("10")
        self.post_pulse_width.setText("50")
    
    def init_Value_CV(self):
        self.cv_lbound.setText("1")
        self.cv_ubound.setText("3")
        self.cv_startpot.setText("0")
        self.cv_stoppot.setText("1")
        self.cv_scanrate.setText("100")
        self.cv_numcycles.setText("1")
        self.cv_numsamples.setText("1")
    pass

    def editData(self):
        idx = 0
        if self.frame_.parameters['type'] == "cd":
            idx = 0
        elif self.frame_.parameters['type'] == "rate":
            idx= 1
        elif self.frame_.parameters['type'] == "cv":
            idx = 2
        elif self.frame_.parameters['type'] == "dpv":
            idx = 3
        self.comboBox.setCurrentIndex(idx)
        self.name_measure.setText(self.frame_.name_technique)
        self.save_path.setText(self.frame_.parameters['value']['filename'])
        self.show_measure(idx)
        self.set_para(idx)


class Create(QMainWindow):
    def __init__(self, main_window):
        global cv_range_checkboxes
        super().__init__()
        uic.loadUi('./ui/sub_window/create_window.ui', self)
        self.main_window = main_window
        self.comboBox.addItems(LIST_TECHNIQUES)
        self.button_cancel.clicked.connect(self.exit_window)
        self.button_add.clicked.connect(self.add)
        self.choose_file.clicked.connect(self.choose_file_)
        self.ocp_button.clicked.connect(self.cv_get_ocp)
        self.checkBox_lsv.stateChanged.connect(self.Choose_Lsv)
        self.checkBox_cv.stateChanged.connect(self.Choose_Cv)
        self.raising_cb.stateChanged.connect(self.Choose_Rasing_Dpv)
        self.falling_cb.stateChanged.connect(self.Choose_Faling_Dpv)
        self.cv_scanrate.editingFinished.connect(self.cv_scanrate_changed_callback)
        self.frame_ = Frame(self, self.main_window)

       
        cv_range_checkboxes.append(self.checkBox_1)
        cv_range_checkboxes.append(self.checkBox_2)
        cv_range_checkboxes.append(self.checkBox_3)
        cv_range_checkboxes.append(self.checkBox_4)

        self.cd_parameter = {}
        self.cv_parameter = {}
        self.rate_parameter = {}

        self.cv_parameter["cv_type"] = CV_MEASURE

        self.dpv_parameter = {}
        self.dpv_parameter["direct"] = DPV_RAISING

        self.cd_parameter['filename'] = './save/{}_{}.txt'.format(
            'cd', str(time.time()))
        self.cv_parameter['filename'] = './save/{}_{}.txt'.format(
            'cv', str(time.time()))
        self.rate_parameter['filename'] = './save/{}_{}.txt'.format(
            'rate', str(time.time()))
        self.dpv_parameter['filename'] = './save/{}_{}.txt'.format(
            'dpv', str(time.time()))
        self.index = 0
        self.id_ = 0
        self.rate_testing.hide()
        self.cyclic_voltammetry.hide()
        self.Differential_Pulse.hide()
        self.save_path.setText(self.cd_parameter['filename'])
        self.comboBox.activated.connect(self.do_something)
        self.init_Value_Dpv()
        self.init_Value_CV()
        self.init_Value_charge_disch()
        self.init_Rate()


    def Choose_Rasing_Dpv(self):
        if True == self.raising_cb.isChecked():
            self.falling_cb.setCheckState(False)
            self.dpv_parameter["direct"] = DPV_RAISING
        else:
            self.falling_cb.setCheckState(True)
            self.dpv_parameter["direct"] = DPV_FALLING

    def Choose_Faling_Dpv(self):
        if True == self.falling_cb.isChecked():
            self.raising_cb.setCheckState(False)
            self.dpv_parameter["direct"] = DPV_FALLING

        else:
            self.raising_cb.setCheckState(True)
            self.dpv_parameter["direct"] = DPV_RAISING

    def Choose_Lsv(self):
        if True == self.checkBox_lsv.isChecked():
            self.checkBox_cv.setCheckState(False)
            self.cv_parameter["cv_type"] = LSV_MEASURE
        else:
            self.checkBox_cv.setCheckState(True)
            self.cv_parameter["cv_type"] = CV_MEASURE
        self.Show_Infomation_Cv_Lsv()
  
            
    def Choose_Cv(self):
        if True == self.checkBox_cv.isChecked():
            self.checkBox_lsv.setCheckState(False)
            self.cv_parameter["cv_type"] = CV_MEASURE
        else:
            self.checkBox_lsv.setCheckState(True)
            self.cv_parameter["cv_type"] = LSV_MEASURE
        self.Show_Infomation_Cv_Lsv()


    def Show_Infomation_Cv_Lsv(self):
        if self.cv_parameter["cv_type"] == CV_MEASURE:
            self.cv_lbound.show() 
            self.cv_ubound.show()
            self.cv_numcycles.show()
            pass
        else:
            self.cv_lbound.hide()    
            self.cv_ubound.hide()
            self.cv_numcycles.hide()
                
    def lsv_validate_parameters(self):
        if self.cv_parameter['scanrate'] == 0:
            QMessageBox.critical(
                self, "CV error", "<font color=\"White\">The scan rate cannot be zero.")
            return False
        if (self.cv_parameter['scanrate'] > 0) and (self.cv_parameter['stoppot'] < self.cv_parameter['startpot']):
            QMessageBox.critical(
                self, "CV error", "<font color=\"White\">For a positive scan rate, the start potential must be lower than the stop bound.")
            return False
        if (self.cv_parameter['scanrate'] < 0) and (self.cv_parameter['stoppot'] > self.cv_parameter['startpot']):
            QMessageBox.critical(
                self, "CV error", "<font color=\"White\">For a negative scan rate, the start potential must be higher than the stop bound.")
            return False
        return True
    
    def dpv_validate_parameters(self):
        if self.dpv_parameter['init_potential'] > self.dpv_parameter['upper_potential']:
            QMessageBox.critical(self, "DPV error", "<font color=\"White\"> the Init potential must be higher than the upper potential.")
            return False
        if self.dpv_parameter['height_dpv'] > (self.dpv_parameter['upper_potential'] - self.dpv_parameter['init_potential']):
            QMessageBox.critical(self, "DPV error", "<font color=\"White\"> the height potential must be smaller than diference of upper potential sub for init potential.")
            return False
        if self.dpv_parameter['increment_dpv'] > self.dpv_parameter['height_dpv']:
            QMessageBox.critical(self, "DPV error", "<font color=\"White\"> the increment potential must be smaller than the height potential.")
            return False
        return True
    
    def cv_validate_parameters(self):
        if self.cv_parameter['ubound'] < self.cv_parameter['lbound']:
            QMessageBox.critical(
                self, "CV error", "<font color=\"White\">The upper bound cannot be lower than the lower bound.")
            return False
        if self.cv_parameter['scanrate'] == 0:
            QMessageBox.critical(
                self, "CV error", "<font color=\"White\">The scan rate cannot be zero.")
            return False
        if (self.cv_parameter['scanrate'] > 0) and (self.cv_parameter['ubound'] < self.cv_parameter['startpot']):
            QMessageBox.critical(
                self, "CV error", "<font color=\"White\">For a positive scan rate, the start potential must be lower than the upper bound.")
            return False
        if (self.cv_parameter['scanrate'] < 0) and (self.cv_parameter['lbound'] > self.cv_parameter['startpot']):
            QMessageBox.critical(
                self, "CV error", "<font color=\"White\">For a negative scan rate, the start potential must be higher than the lower bound.")
            return False
        if self.cv_parameter['numsamples'] < 1:
            QMessageBox.critical(
                self, "CV error", "<font color=\"White\">The number of samples to average must be at least 1.")
            return False
        return True

    def cd_validate_parameters(self):
        """Check if the chosen charge/discharge parameters make sense. If so, return True."""
        if self.cd_parameter['ubound'] < self.cd_parameter['lbound']:
            QMessageBox.critical(self, "Charge/discharge error",
                                       "<font color=\"White\">The upper bound cannot be lower than the lower bound.")
            return False
        if self.cd_parameter['chargecurrent'] == 0.:
            QMessageBox.critical(
                self, "Charge/discharge error", "<font color=\"White\">The charge current cannot be zero.")
            return False
        if self.cd_parameter['dischargecurrent'] == 0.:
            QMessageBox.critical(
                self, "Charge/discharge error", "<font color=\"White\">The discharge current cannot be zero.")
            return False
        if self.cd_parameter['chargecurrent']*self.cd_parameter['dischargecurrent'] > 0:
            QMessageBox.critical(self, "Charge/discharge error",
                                       "<font color=\"White\">Charge and discharge current must have opposite sign.")
            return False
        if self.cd_parameter['numcycles'] <= 0:
            QMessageBox.critical(self, "Charge/discharge error",
                                       "<font color=\"White\">The number of half cycles must be positive and non-zero.")
            return False
        if self.cd_parameter['numsamples'] < 1:
            QMessageBox.critical(self, "Charge/discharge error",
                                       "<font color=\"White\">The number of samples to average must be at least 1.")
            return False
        return True

    def rate_validate_parameters(self):
        """Check if the chosen charge/discharge parameters make sense. If so, return True."""
        if self.rate_parameter['ubound'] < self.rate_parameter['lbound']:
            QMessageBox.critical(self, "Rate testing error",
                                       "<font color=\"White\">The upper bound cannot be lower than the lower bound.")
            return False
        if 0. in self.rate_parameter['currents']:
            QMessageBox.critical(
                self, "Rate testing error", "<font color=\"White\">The charge/discharge current cannot be zero.")
            return False
        if self.rate_parameter['numcycles'] <= 0:
            QMessageBox.critical(self, "Charge/discharge error",
                                       "<font color=\"White\">The number of half cycles must be positive and non-zero.")
            return False
        return True

    def choose_file_(self):
        """Open a file dialog and write the path of the selected file to a given entry field."""
        filedialog = QFileDialog()
        self.setStyleSheet("color: white;  background-color: black")
        if self.index == 0:
            tuple_file = filedialog.getSaveFileName(
                self, "Choose where to save the charge/discharge measurement data", "", "ASCII data (*.txt)", options=QFileDialog.DontConfirmOverwrite)
            file_name = tuple_file[0]
            self.cd_parameter['filename'] = file_name
            self.save_path.setText(self.cd_parameter['filename'])
        elif self.index == 1:
            tuple_file = filedialog.getSaveFileName(
                self, "Choose where to save the rate testing measurement data", "", "ASCII data (*.txt)", options=QFileDialog.DontConfirmOverwrite)
            file_name = tuple_file[0]
            self.rate_parameter['filename'] = file_name
            self.save_path.setText(self.rate_parameter['filename'])
        elif self.index == 2:
            tuple_file = filedialog.getSaveFileName(
                self, "Choose where to save the CV measurement data", "", "ASCII data (*.txt)", options=QFileDialog.DontConfirmOverwrite)
            file_name = tuple_file[0]
            self.cv_parameter['filename'] = file_name
            self.save_path.setText(self.cv_parameter['filename'])
        # file_entry_field.setText(file_name)
        self.setStyleSheet("color: black;  background-color: black")

        # return file_name

    def do_something(self, index):
        if (index == 0):
            self.rate_testing.hide()
            self.cyclic_voltammetry.hide()
            self.Differential_Pulse.hide()
            self.charge_disch.show()
            self.index = index
            self.save_path.setText(self.cd_parameter['filename'])
        elif (index == 1):
            self.charge_disch.hide()
            self.cyclic_voltammetry.hide()
            self.Differential_Pulse.hide()
            self.rate_testing.show()
            self.index = index
            self.save_path.setText(self.rate_parameter['filename'])
        elif (index == 2):
            self.charge_disch.hide()
            self.rate_testing.hide()
            self.Differential_Pulse.hide()
            self.cyclic_voltammetry.show()
            self.index = index
            self.save_path.setText(self.cv_parameter['filename'])
        else:
            self.charge_disch.hide()
            self.rate_testing.hide()
            self.cyclic_voltammetry.hide()
            self.Differential_Pulse.show()
            self.index = index
            self.save_path.setText(self.dpv_parameter['filename'])
        self.name_measure.setText(LIST_TECHNIQUES[index] + " " +str(INDEX_TECHNIQUES[index]))

    def get_para(self, index):
        if index == 0:
            try:
                self.cd_parameter['lbound'] = float(self.cd_lbound.text())
                self.cd_parameter['ubound'] = float(self.cd_ubound.text())
                self.cd_parameter['chargecurrent'] = float(
                    self.cd_chargecurrent.text())/1e3
                self.cd_parameter['dischargecurrent'] = float(
                    self.cd_dischargecurrent.text())/1e3
                self.cd_parameter['numcycles'] = int(self.cd_numcycles.text())
                self.cd_parameter['numsamples'] = int(
                    self.cd_numsamples.text())
                # self.cd_parameter['filename'] = choose_file(
                #     "Choose where to save the charge/discharge measurement data")
                if self.cd_validate_parameters() and validate_file(self.main_window, self.cd_parameter['filename']):
                    parameters = {'id': self.id_, 'type': 'cd',
                                  'value': self.cd_parameter}
                    return parameters
                else:
                    return False
            except ValueError:
                QMessageBox.critical(
                self, "Cd error", "<font color=\"White\">Input parameter is not correct.")
                return False
        elif index == 1:
            try:
                self.rate_parameter['lbound'] = float(self.rate_lbound.text())
                self.rate_parameter['ubound'] = float(self.rate_ubound.text())
                self.rate_parameter['one_c_current'] = float(
                    self.rate_one_c_current.text())/1e3
                self.rate_parameter['numcycles'] = int(
                    self.rate_numcycles.text())
                self.rate_parameter['crates'] = [
                    float(x) for x in self.rate_crates.text().split(",")]
                self.rate_parameter['currents'] = [
                    self.rate_parameter['one_c_current']*rc for rc in self.rate_parameter['crates']]
                self.rate_parameter['numsamples'] = 1
                # self.rate_parameter['filename'] = choose_file(
                #     "Choose where to save the rate testing measurement data")
                if self.rate_validate_parameters() and validate_file(self.main_window, self.rate_parameter['filename']):
                    parameters = {'id': self.id_, 'type': 'rate',
                                  'value': self.rate_parameter}
                    return parameters
                else:
                    return False
            except ValueError:
                QMessageBox.critical(
                self, "rate error", "<font color=\"White\">Input parameter is not correct.")
                return False
        elif index == 2:
            try:
                if self.cv_parameter["cv_type"] == CV_MEASURE:
                    self.cv_parameter['lbound'] = float(self.cv_lbound.text())
                    self.cv_parameter['ubound'] = float(self.cv_ubound.text())
                    self.cv_parameter['startpot'] = float(self.cv_startpot.text())
                    self.cv_parameter['stoppot'] = float(self.cv_stoppot.text())
                    self.cv_parameter['scanrate'] = float(self.cv_scanrate.text())/1e3
                    self.cv_parameter['numcycles'] = int(self.cv_numcycles.text())
                    self.cv_parameter['numsamples'] = int(self.cv_numsamples.text())
                    if self.cv_validate_parameters() and validate_file(self.main_window, self.cv_parameter['filename']):
                        parameters = {'id': self.id_, 'type': 'cv',
                                    'value': self.cv_parameter}
                        return parameters
                    else:
                        return False
                else:
                    self.cv_parameter['lbound'] = 0
                    self.cv_parameter['ubound'] = 0
                    self.cv_parameter['startpot'] = float(self.cv_startpot.text())
                    self.cv_parameter['stoppot'] = float(self.cv_stoppot.text())
                    self.cv_parameter['scanrate'] = float(
                        self.cv_scanrate.text())/1e3
                    self.cv_parameter['numcycles'] = 0
                    self.cv_parameter['numsamples'] = int(
                        self.cv_numsamples.text())
                    if self.lsv_validate_parameters() and validate_file(self.main_window, self.cv_parameter['filename']):
                        parameters = {'id': self.id_, 'type': 'cv',
                                    'value': self.cv_parameter}
                        return parameters
                    else:
                        return False
            except ValueError:
                QMessageBox.critical(
                self, "Cv error", "<font color=\"White\">Input parameter is not correct.")
        elif index == 3:
            try:
                self.dpv_parameter['segments'] = int(self.segments.text())
                self.dpv_parameter['init_potential'] = int(self.init_potential.text())
                self.dpv_parameter['upper_potential'] = int(self.upper_potential.text())
                self.dpv_parameter['lower_potential'] = int(self.lower_potential.text())
                self.dpv_parameter['final_potential'] = int(self.final_potential.text())
                self.dpv_parameter['height_dpv'] = int(self.height_dpv.text())
                self.dpv_parameter['width_dpv'] = int(self.width_dpv.text())
                self.dpv_parameter['period_dpv'] = int(self.period_dpv.text())
                self.dpv_parameter['increment_dpv'] = int(self.increment_dpv.text())
                self.dpv_parameter['post_pulse_width'] = int(self.post_pulse_width.text())
                self.dpv_parameter['pre_pulse_width'] = int(self.pre_pulse_width.text())
            
                if self.dpv_validate_parameters() and validate_file(self.main_window, self.dpv_parameter['filename']):
                    parameters = {'id': self.id_, 'type': 'dpv',
                                'value': self.dpv_parameter}
                    return parameters
                else:
                    return False
            except ValueError:
                QMessageBox.critical(
                self, "DPV error", "<font color=\"White\">Input parameter is not correct.")
                return False

    def cv_get_ocp(self):
        """Insert the currently measured (open-circuit) potential into the start potential input field."""
        try:
            self.cv_startpot.setText('%5.3f' % last_potential_values[-1])
        except:
            self.cv_startpot.setText('0')
    def cv_scanrate_changed_callback(self):
        pass
        """Calculate a suggested number of samples to average based on the entered value for the CV scan rate."""
        try:
            cv_scanrate = float(self.cv_scanrate.text())
            numsamples = int(20./abs(cv_scanrate))+1 # Aims for approx. one (averaged) measurement every 2 to 4 mV for scan rates up to 20 mV/s
            self.cv_numsamples.setText("%d"%numsamples)
        except:
            pass # Don't do anything in case the entered scan rate value is invalid

    def exit_window(self):
        self.close()

    def add(self):
        global listFrame, status_table, idx_frame
        self.frame_.index_measure = self.comboBox.currentIndex()
        self.frame_.parameters = self.get_para(self.frame_.index_measure)
        if self.frame_.parameters:
            self.id_ += 1
            self.frame_.frame_idx = idx_frame
            idx_frame += 1
            self.frame_.name_technique = self.name_measure.text()
            self.frame_.setParent(self.main_window.main_widget)
            INDEX_TECHNIQUES[self.frame_.index_measure] += 1
            status_table = len(listFrame)
            self.frame_.index_table = status_table
            listFrame.append(self.frame_)
            self.frame_.setStyleSheet("background-color: %s;" %
                                COLOR_TABLE[self.frame_.index_measure])
            self.frame_.setText(self.frame_.name_technique)
            self.frame_.resize(80, 60)
            self.frame_.move((x_axis[int(self.frame_.index_table % ADD_TABLE_SIZE[1])]),
                        int(y_axis[int(self.frame_.index_table / ADD_TABLE_SIZE[1])]))
            self.frame_.show()
            # print(self.frame_.parameters)
        self.exit_window()
     

    def init_Value_Dpv(self):
        self.segments.setText("2")
        self.init_potential.setText("0000")
        self.upper_potential.setText("2000")
        self.lower_potential.setText("500")
        self.final_potential.setText("1000")
        self.height_dpv.setText("50")
        self.width_dpv.setText("100")
        self.period_dpv.setText("100")
        self.increment_dpv.setText("10")
        self.pre_pulse_width.setText("10")
        self.post_pulse_width.setText("50")
    
    def init_Value_CV(self):
        self.cv_lbound.setText("1")
        self.cv_ubound.setText("3")
        self.cv_startpot.setText("0")
        self.cv_stoppot.setText("1")
        self.cv_scanrate.setText("100")
        self.cv_numcycles.setText("1")
        self.cv_numsamples.setText("1")

    def init_Value_charge_disch(self):
        self.cd_lbound.setText("1")
        self.cd_ubound.setText("2")
        self.cd_chargecurrent.setText("100")
        self.cd_dischargecurrent.setText("-100")
        self.cd_numcycles.setText("1")
        self.cd_numsamples.setText("1")
        self.name_measure.setText(LIST_TECHNIQUES[0] + " " +str(INDEX_TECHNIQUES[0]))

    def init_Rate(self):
        self.rate_lbound.setText("1")
        self.rate_one_c_current.setText("2")
        self.rate_ubound.setText("1000")
        self.rate_crates.setText("1, 2, 5, 10, 20, 50, 100")
        self.rate_numcycles.setText("2")
