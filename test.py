import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLabel

app = QApplication(sys.argv)

# Create a QWidget
widget = QWidget()

# Create a QLabel and set its text
label = QLabel("Hello, PyQt5!")

# Add the QLabel to the QWidget
label.setParent(widget)

# Set the position of the QLabel
label.setGeometry(100, 100, 200, 50)  # Set X, Y, width, and height

# Show the QWidget
widget.setGeometry(100, 100, 400, 300)  # Set the geometry (position and size) of the QWidget
widget.show()

sys.exit(app.exec_())
