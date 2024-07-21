import os
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5 import uic, QtOpenGL, QtGui
import yaml


def validate_file(main_window, filename):
    """Check if a filename can be written to. If so, return True."""
    main_window.setStyleSheet("color: white;  background-color: black")
    if os.path.isfile(filename):
        if QMessageBox.question(main_window, "File exists", "<font color=\"White\">The specified output file already exists. Do you want to overwrite it?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No) != QMessageBox.Yes:
            main_window.setStyleSheet("color: black;  background-color: black")
            return False
    try:
        tryfile = open(filename, 'w', 1)
        tryfile.close()
        main_window.setStyleSheet("color: black;  background-color: black")
        return True
    except IOError:
        QMessageBox.critical(
            main_window, "File error", "<font color=\"White\">The specified output file path is not valid.")
        main_window.setStyleSheet("color: black;  background-color: black")
        return False


def get_config(config_path):
    with open(config_path, 'r') as stream:
        return yaml.load(stream, Loader=yaml.FullLoader)
