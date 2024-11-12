import sys
import os
import warnings

# This is the ovito.plugins Python package. It hosts the C++ extension modules of OVITO.

# First, check if the user accidentally installed the PyPI package via 'pip install'
# in an Anaconda environment. Warn if this is the case, because the PySide6 loading
# will probably fail due to conflicting versions of the Qt framework C++ libraries.
#
# Using method from https://stackoverflow.com/questions/47608532/how-to-detect-from-within-python-whether-packages-are-managed-with-conda/47610844#47610844
# to detect Anaconda environment:
if os.path.exists(os.path.join(sys.prefix, 'conda-meta')):
    warnings.warn("Did you accidentally install the OVITO package from the PyPI repository in an Anaconda/Miniconda Python interpreter using the 'pip' command? "
        "This will likely lead to conflicts with existing libraries in the Anaconda environment, and import of the OVITO module may fail with an error related to the Qt framework. "
        "To fix this, please uninstall the ovito pip package by running 'pip uninstall -y ovito PySide6' and then "
        "install the OVITO Anaconda package provided by OVITO GmbH. Visit https://docs.ovito.org/python/introduction/installation.html for further instructions. "
        "If you would rather like to ignore this warning message, add the following code to the top of your Python script:\n\n"
        "  import warnings\n"
        "  warnings.filterwarnings('ignore', message='.*OVITO.*PyPI')\n",
        stacklevel=3)

# Check if an incompatible version of the Qt framework has already been imported.
# If so, warn because Qt5 and Qt6 cannot both be used at the same time within the same application process.
if sys.modules.get("PyQt5.QtCore") or sys.modules.get("PySide2.QtCore"):
    warnings.warn("Incompatible version of the Qt cross-platform framework detected!\nThis version of the OVITO Python module is based on Qt6 (loaded via the PySide6 bindings module), "
        "but bindings for old Qt5 are already loaded at this point (through PyQt5 or PySide2 imports preceding the import of OVITO). To avoid library version conflicts, please make sure the rest of "
        "your application uses Qt6 too instead of Qt5. "
        "\n\n"
        "To fix this warning, replace any PySide2 import statements in your script with PySide6 (or PyQt5 imports with PyQt6). "
        "In addition, it may help to set the environment variable QT_API=pyside6 to force third-party packages (e.g. matplotlib) to load Qt6 instead of Qt5. "
        "If you have any questions, please contact support@ovito.org.\n")

# Load all the Qt bindings first before OVITO's own C++ modules get loaded.
# This ensures that the right Qt shared libraries needed by OVITO are already loaded into the process when running in a system Python interpreter.
from ovito.qt_compat import QtCore
from ovito.qt_compat import QtGui
from ovito.qt_compat import QtWidgets
from ovito.qt_compat import QtNetwork
from ovito.qt_compat import QtXml
from ovito.qt_compat import QtOpenGLWidgets
from ovito.qt_compat import QtOpenGL

# Install an import hook that will guard against incompatible Qt imports.
# Loading both Qt 5.x and 6.x into the same process leads to runtime errors.
import importlib.abc
class ImportDenier(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path, target=None):
        if path:
            return
        if fullname in ("PySide2", "PyQt5"):
            raise ImportError(f"The ovito package you imported ealier requires PySide6 (the Python bindings for Qt6). Importing {fullname}, which provides bindings for the incompatible Qt5 framework, "
                "is forbidden, because it leads to library version conflicts. You should update the import statements in your script to load PySide6 instead. If you have any questions, please contact support@ovito.org.")
sys.meta_path.insert(0, ImportDenier())

# Preload DLLs needed by the ovito_bindings module to make sure they are found and loaded from the right location.
# In particular the rkcommon.dll will not automatically be found otherwise.
# See also discussion at https://matsci.org/t/windows-installation-and-dll-names/58371
if sys.platform.startswith('win32'):
    import ctypes
    _preloaded_dlls = [
        ctypes.WinDLL(__path__[0] + '\\zlib.dll'),
        ctypes.WinDLL(__path__[0] + '\\hdf5_hl.dll'),
        ctypes.WinDLL(__path__[0] + '\\hdf5.dll'),
        ctypes.WinDLL(__path__[0] + '\\netcdf.dll'),
        ctypes.WinDLL(__path__[0] + '\\tbb12.dll'),
        ctypes.WinDLL(__path__[0] + '\\tbbmalloc.dll'),
        ctypes.WinDLL(__path__[0] + '\\anari.dll'),
        ctypes.WinDLL(__path__[0] + '\\libcrypto-3-x64.dll'),
        ctypes.WinDLL(__path__[0] + '\\libssl-3-x64.dll'),
        ctypes.WinDLL(__path__[0] + '\\ssh.dll'),
        ctypes.WinDLL(__path__[0] + '\\embree4.dll'),
        ctypes.WinDLL(__path__[0] + '\\rkcommon.dll'),
        ctypes.WinDLL(__path__[0] + '\\OpenImageDenoise_core.dll'),
        ctypes.WinDLL(__path__[0] + '\\OpenImageDenoise_device_cpu.dll'),
        ctypes.WinDLL(__path__[0] + '\\OpenImageDenoise.dll'),
        ctypes.WinDLL(__path__[0] + '\\ospray.dll'),
        ctypes.WinDLL(__path__[0] + '\\ospray_module_cpu.dll'),
        ctypes.WinDLL(__path__[0] + '\\ospray_module_denoiser.dll'),
    ]

# Load the C++ extension module containing the OVITO bindings.
import ovito.plugins.ovito_bindings
