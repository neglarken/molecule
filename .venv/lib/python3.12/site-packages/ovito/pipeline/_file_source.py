from __future__ import annotations
import ovito
from . import FileSource
from ..nonpublic import FileImporter, PipelineStatus, PythonFileImporter
from ..io._file_reader_interface import FileReaderInterface
import collections.abc as collections
import os
from typing import Any, Union, Optional

# This is the table of import file formats used by the import_file() function
# to look up the right importer class for a file format.
# Plugins can register their importer class by inserting a new entry in this dictionary.
FileImporter._format_table = {}


# Helper function used in freestanding import_file() and FileSource.load():
def _create_file_importer(
    location: Union[str, os.PathLike, collections.Sequence[str]],
    params: dict,
    existing_importer: Optional[FileImporter] = None,
):
    # Process input parameter
    if isinstance(location, (str, os.PathLike)):
        location_list = [location]
    elif isinstance(location, collections.Sequence):
        location_list = list(location)
    else:
        raise TypeError(
            "Invalid input file location. Expected str, os.PathLike, or sequence thereof."
        )
    first_location = location_list[0]

    # Did the caller specify the format of the input file explicitly?
    if "input_format" in params:
        format = params.pop("input_format")

        # Did the user specify a FileReaderInterface class or object?
        if isinstance(format, FileReaderInterface):
            importer = PythonFileImporter()
            importer.delegate = format
        elif isinstance(format, type) and issubclass(format, FileReaderInterface):
            importer = PythonFileImporter()
            importer.delegate = format()
        else:
            # Look up the registered importer class from the format name.
            available_formats = FileImporter._format_table
            if not format in available_formats:
                raise ValueError(
                    f"Unknown input format: '{format}'. Supported formats are: {sorted(list(available_formats.keys()))}"
                )
            # Create an instance of the importer class. It will be configured below.
            importer = available_formats[format]()
    else:
        # Auto-detect the file's format if caller did not specify the format explicitly.
        importer = FileImporter.autodetect_format(first_location)
        if not importer:
            raise RuntimeError(
                "Could not detect the file format. The format might not be supported."
            )

    # Re-use existing importer if it is compatible.
    if existing_importer and type(existing_importer) is type(importer):
        if not isinstance(importer, PythonFileImporter) or type(
            importer.delegate
        ) is type(existing_importer.delegate):
            importer = existing_importer

    # Forward user parameters to the file importer object.
    importer_object = (
        importer.delegate if isinstance(importer, PythonFileImporter) else importer
    )
    for key, value in params.items():
        if not hasattr(importer_object, key):
            raise KeyError(
                f"Invalid keyword parameter. File reader {importer_object!r} doesn't support parameter '{key}'."
            )
        importer_object.__setattr__(key, value)

    return importer, location_list


# Implementation of FileSource.load() method:
def _FileSource_load(self, location: Union[str, os.PathLike, collections.Sequence[str]], **params: Any):
    """Sets a new input file, from which this pipeline source will retrieve its data.

    The function accepts additional keyword arguments, which are forwarded to the format-specific file reader
    managed internally by the :py:class:`FileSource`.
    For further information, please see the documentation of the :py:func:`~ovito.io.import_file` function,
    which has the same call interface as this method.

    :param location: The local file(s) or remote URL to load.
    :param params: Additional keyword parameters to be passed to the file reader.
    """

    # Create a FileImporter object for the specified input file(s).
    importer, location_list = _create_file_importer(location, params, self.importer)

    # Load new data file.
    self.set_source(location_list, importer, False, False)

    # Block execution until data file has been loaded.
    self.wait_until_ready(
        0
    )  # Requesting frame 0 here, because full list of frames is not loaded yet at this point.

    # Raise Python error if loading failed.
    if self.status.type == PipelineStatus.Type.Error:
        raise RuntimeError(self.status.text)

    # Block until list of animation frames has been loaded
    self.wait_for_frames_list()

FileSource.load = _FileSource_load


# Implementation of FileSource.source_path property.
def _get_FileSource_source_path(self) -> Union[str, collections.Sequence[str]]:
    """This read-only attribute returns the path(s) or URL(s) of the file(s) where this :py:class:`!FileSource` retrieves its input data from.
    You can change the source path by calling :py:meth:`.load`."""
    path_list = self.get_source_paths()
    if len(path_list) == 1:
        return path_list[0]
    elif len(path_list) == 0:
        return ""
    else:
        return path_list

FileSource.source_path = property(_get_FileSource_source_path)


def _set_playback_ratio(self, ratio: str):
    if ":" in ratio:
        split = ratio.split(":")
    elif "/" in ratio:
        split = ratio.split("/")
    else:
        raise ValueError("Invalid playback ratio format. Expected 'a:b' or 'a/b'.")

    if len(split) != 2:
        raise ValueError("Invalid playback ratio format. Expected 'a:b' or 'a/b'.")

    num, den = split
    self.playback_speed_numerator = int(num)
    self.playback_speed_denominator = int(den)


def _get_playback_ratio(self) -> str:
    """Controls the :ref:`trajectory playback ratio <manual:scene_objects.file_source.configure_trajectory_playback>` of the animation.
    This property controls how snapshots loaded from the file source are mapped to OVITO's animation timeline.
    You can change the default 1:1 mapping to either a 1:n mapping, in which case each trajectory frame is replicated
    and rendered n times, or to an n:1 mapping, where only every n-th trajectory frame will be rendered.

    Input has to be provided as a string in the form "a:b" or "a/b", where a and b are integers.

    :param str ratio: New playback ratio.
    :return: The current playback ratio as a string in the form "a:b".
    :default: ``"1:1"``

    .. versionadded:: 3.11.0
    """
    return f"{self.playback_speed_numerator}:{self.playback_speed_denominator}"


def _del_playback_ratio(self):
    self.playback_speed_numerator = 1
    self.playback_speed_denominator = 1


FileSource.playback_ratio = property(
    fget=_get_playback_ratio, fset=_set_playback_ratio, fdel=_del_playback_ratio
)
