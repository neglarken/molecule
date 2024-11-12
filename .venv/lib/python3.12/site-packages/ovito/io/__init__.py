"""
This module provides two high-level functions for reading and data files:

    * :py:func:`import_file`
    * :py:func:`export_file`

Furthermore, it contains the base class for :ref:`custom file readers <writing_custom_file_readers>`:

    * :py:class:`FileReaderInterface`

"""

__all__ = ['import_file', 'export_file', 'FileReaderInterface']