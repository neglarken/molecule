from __future__ import annotations
import ovito.io
from ..data import DataCollection
import abc
import os
import traits.api
from typing import Any, Optional, Generator, Union
import collections.abc

class FileReaderInterface(traits.api.HasTraits):
    """
    Base: :py:class:`traits.has_traits.HasTraits`

    Abstract base class for :ref:`Python-based file readers <writing_custom_file_readers>`.

    When deriving from this class, you must implement the methods :py:meth:`detect` and :py:meth:`parse`.
    Implementing the :py:meth:`scan` method is only necessary for file formats that can store more than
    one trajectory frame per file.

    .. versionadded:: 3.9.0
    """

    # Method that must be implemented by all sub-classes:
    @abc.abstractmethod
    def parse(self, data: DataCollection, *, filename: str, url: str, frame_index: int, frame_info: Any, is_new_file: bool, **kwargs: Any):
        """
        The main work function, which is called by OVITO to have the file reader parse a dataset or one trajectory frame from the given file.

        :param data: Container in which the file reader should store any data it loads from the file.
        :param filename: The local filesystem path the system is requesting to load.
        :param url: The URL the file originally came from. This may be a remote location (e.g. https:// or sftp:// URL). In any case, the file reader should use *filename* to access the local copy of the file.
        :param frame_index: The zero-based index of the frame to load from the trajectory.
        :param frame_info: If the input file contains multiple trajectory frames, this argument is the parser-specific indexing information obtained by your :py:meth:`scan` method implementation,
                           helping :py:meth:`parse` seek to the requested frame in the file (e.g. a byte offset or line number).
        :param is_new_file: Indicates that the user newly opened this trajectory in the OVITO application and the file reader should discard any existing objects in the data collection (e.g. leftovers from another file reader).
                            Will be ``True`` only during the first call to :py:meth:`parse` after your file reader was newly associated with a :py:class:`~ovito.pipeline.FileSource`.
        :param kwargs: Any further arguments that may be passed in by the system. This parameter should always be part of the function signature for forward compatibility with future versions of OVITO,
                       which may provide additional keyword arguments.
        """
        raise NotImplementedError("Abstract method parse() must be implemented by the FileReaderInterface derived class.")

    # Define the optional methods only when generating the Sphinx documentation for the OVITO module.
    if os.environ.get('OVITO_SPHINX_BUILD', False):

        @abc.abstractmethod
        def detect(self, filename: str) -> bool:
            """
            This method is called by the system to let the file reader inspect the given file and determine whether it is in a format that can be
            read by the class' :py:meth:`parse` method.

            For best performance, your implementation of this method should try to determine as efficiently as possible whether the given file uses a supported
            format by reading and inspecting just the file's header -- not the entire file.

            :param filename: The local filesystem path of the input file.
            :return: ``True`` if this file reader would like to load the given file. The system will invoke :py:meth:`scan` or :py:meth:`parse` next.
                     ``False`` if this class cannot handle the file's format.
            """
            raise NotImplementedError

        @abc.abstractmethod
        def scan(self, filename: str, register_frame: collections.abc.Callable[[Any, Optional[str]], None]):
            """
            Optional method called by the system to let the file reader discover and index the trajectory frames stored in the given file.
            Only file readers for formats that allow storing multiple frames per file need to implement this method.

            :param filename: The local filesystem path of the input file to scan.
            :param register_frame: A callback function provided by the system, which must be called exactly once for every trajectory
                                   frame found in the input file during the scan process.

            The *register_frame()* callback function has the following signature::

                register_frame(frame_info: Any = None, label: Optional[str] = None)

            The *frame_info* value and the *label* text describe one trajectory frame discovered by your scan method
            and the system stores the information until later when :py:meth:`parse` is invoked by the system to request loading of
            an individual frame. Then the *frame_info* value will be available for the file reader to quickly seek to the requested frame
            in the input file and load its contents.

            See :ref:`example_custom_file_reader_FR1` for a simple implementation of the :py:meth:`scan` method.
            See :ref:`example_custom_file_reader_FR2` for a well-behaved implementation yielding best performance.
            """
            raise NotImplementedError

ovito.io.FileReaderInterface = FileReaderInterface
