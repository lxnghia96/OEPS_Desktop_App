from utils.global_var import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import QCursor
import sys
from PyQt5 import uic
sys.path.append('.')


class Frame(QLabel):
    optionEmit = pyqtSignal(int)
    def __init__(self, createWindow, main_window):
        global idx_frame
        super().__init__()
        self.createWindow = createWindow
        self.main_window = main_window
        self.check_move = 0
        self.check_stack = 0  # Check frame is on stack list or not
        self.index_table = 0
        self.index_line = 0
        self.setMouseTracking(True)
        self.parameters = {}
        self.setWordWrap(True)
        self.setAlignment(Qt.AlignCenter)
        self.setFrameShape(QFrame.Box)
        self.setFrameShadow(QFrame.Raised)
        self.checkSelect = 0
        self.isInQueue = False
        self.frame_idx = None

    def mousePressEvent(self, event):
        if self.isInQueue == False:
            self.check_move = 1
            for frame in listFrame:      
                frame.isSelected(DE_ACTIVE)
            self.isSelected(ACTIVE)

    def isSelected(self, isSelect):
        if isSelect == ACTIVE:
            self.checkSelect = 1
            self.setStyleSheet(f"background-color:{COLOR_TABLE[self.index_measure]};"
                            "border :2px solid ;"
                            "border-top-color : yellow; "
                            "border-left-color :yellow;"
                            "border-right-color :yellow;"
                            "border-bottom-color : yellow")
            self.setText(self.name_technique)
        else:
            self.checkSelect = 0
            self.setStyleSheet(f"background-color:{COLOR_TABLE[self.index_measure]};")
            self.setText(self.name_technique)        

    def mouseReleaseEvent(self, e):
        global queue_measure, x_axis, y_axis
        if (self.main_window.frame_20.pos().y()-50< self.pos().y() < self.main_window.frame_20.pos().y() + 50) and self.check_stack == 0:
            self.check_move = 0
            self.check_stack = 1
            pos_x_line = self.main_window.button_refresh.pos(
            ).x() + self.main_window.button_refresh.width()
            pos_y_line = self.main_window.frame_20.pos().y()
            self.resize(120, self.main_window.frame_20.height())
            self.move(int(pos_x_line + self.main_window.status_line*120), int(pos_y_line))
            self.main_window.status_line += 1
            self.index_line = self.main_window.status_line
            if self.parameters:
                queue_measure.append(self.parameters)
                self.isSelected(DE_ACTIVE)
                self.isInQueue = True
        else:
            if self.parameters:
                for queue_measure_ in queue_measure:
                    if queue_measure_['id'] == self.parameters['id']:
                        queue_measure.remove(queue_measure_)
                self.check_move = 0
                self.check_stack = 0
                self.isInQueue = False
                self.resize(80, 61)
                if self.index_line:
                    self.main_window.status_line -= 1
                    self.index_line = 0
                self.move(int(x_axis[int(self.index_table % ADD_TABLE_SIZE[1])]),
                          int(y_axis[int(self.index_table / ADD_TABLE_SIZE[1])]))
            else:
                self.check_move = 0
                self.check_stack = 0
                self.isInQueue = False
                self.resize(80, 61)
                if self.index_line:
                    self.main_window.status_line -= 1
                    self.index_line = 0
                self.move(int(x_axis[int(self.index_table % ADD_TABLE_SIZE[1])]),
                          int(y_axis[int(self.index_table / ADD_TABLE_SIZE[1])]))

    def frame_refresh(self):
        global x_axis, y_axis
        self.isInQueue = False
        self.check_move = 0
        self.check_stack = 0
        self.resize(80, 61)
        if self.index_line:
            self.main_window.status_line -= 1
            self.index_line = 0
        # self.setStyleSheet("background-color: #181818;")
        self.move(int(x_axis[int(self.index_table % ADD_TABLE_SIZE[1])]),
                  int(y_axis[int(self.index_table / ADD_TABLE_SIZE[1])]))
        
