"""
This module imports the right Qt bindings, which are compatible 
with the version of the Qt framework OVITO has been built against.
"""

import os

# Import Shiboken module first to preload shiboken6.dll, which is needed by the Qt DLLs.
import shiboken6 as shiboken 

from PySide6 import QtCore, QtGui, QtWidgets, QtNetwork, QtXml

# The QtOpenGLWidgets module is not included in the embedded PySide6 installation of OVITO Pro 3.7,
# but it should be loaded when using the PyPI version of PySide6.
try:
    from PySide6 import QtOpenGLWidgets
    from PySide6 import QtOpenGL
except ImportError: pass

# Try to tell other Python modules (e.g. matplotlib) to use the same Qt bindings as OVITO.
# Typically, this is done through the environment variable QT_API.
if not 'QT_API' in os.environ:
    os.environ['QT_API'] = 'pyside6'

# Map DeprecationWarning methods
QtCore.QCoreApplication.exec_ = QtCore.QCoreApplication.exec
QtCore.QEventLoop.exec_ = QtCore.QEventLoop.exec
QtCore.QThread.exec_ = QtCore.QThread.exec
