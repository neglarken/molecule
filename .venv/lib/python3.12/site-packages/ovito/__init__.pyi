"""This module defines the :py:class:`Scene` class, which serves as a "universe" or context for all actions
performed by a script. The global scene object is accessible as module-level variable :py:data:`ovito.scene`.
The scene manages a list of :py:class:`Pipeline` objects, which will be visible in images and videos
when rendering the scene through a :py:class:`Viewport`. Furthermore, you can save the entire
scene definition including all pipelines to a :file:`.ovito` session state file, which can be opened in the graphical OVITO application."""
__all__ = ['version', 'version_string', 'scene', 'Scene', 'enable_logging']
from __future__ import annotations
from typing import Tuple, Optional, MutableSequence, Any, Iterable, Union
import ovito.pipeline
import numpy.typing
ArrayLike = Union[numpy.typing.NDArray[Any], Iterable[Any]]

class Scene:
    """This class encompasses all data of an OVITO program session (basically everything that gets saved in a ``.ovito`` state file). It manages the list of objects (i.e. :py:class:`Pipeline` instances) that are part of the three-dimensional scene and which will show up in rendered images. 

From a script's point of view, there exists exactly one universal instance of this class at any time, which is accessible through the :py:data:`ovito.scene` module-level variable. A script cannot create another :py:class:`Scene` instance by itself."""

    def __init__(self) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""
        self.selected_pipeline: Optional[ovito.pipeline.Pipeline]
        'The :py:class:`Pipeline` currently selected in the OVITO Pro desktop application,\nor ``None`` if no pipeline is selected. Typically, this is the last pipeline that was added to the scene using\n`Pipeline.add_to_scene()`.\n\nThis field can be useful for macro scripts running in the context of an interactive OVITO Pro session,\nwhich want to perform some operation on the currently selected pipeline, e.g. inserting a new modifier.'

    @property
    def pipelines(self) -> MutableSequence[ovito.pipeline.Pipeline]:
        """The list of :py:class:`Pipeline` objects that are currently part of the three-dimensional scene.
Only pipelines in this list will display their output data in the viewports and in rendered images. You can add or remove a pipeline either by calling
its :py:meth:`add_to_scene` or :py:meth:`remove_from_scene` methods or by directly manipulating this
list using the standard Python ``append()`` and ``del`` statements:

```python
  from ovito import scene
  from ovito.io import import_file
  
  pipeline = import_file('input/simulation.dump')
  
  # Insert the pipeline into the visualization scene.
  pipeline.add_to_scene()
  # It's now part of the 'scene.pipelines' list.
  assert pipeline in scene.pipelines
  # If needed, we can take it out again.
  pipeline.remove_from_scene()
```"""
        ...

    def save(self, filename: str) -> None:
        """Saves current the scene to a :file:`.ovito` session state file on disk. The scene comprises all pipelines
in the :py:attr:`Scene.pipelines` list. This function works like the :ref:`'Save Session State As' function
of the OVITO desktop application <manual:usage.saving_loading_scene>`.

  Only :py:class:`Pipeline` objects for which `add_to_scene()`
  has been called will be included in the session state file. Independent pipelines in Python variables that have not been added to
  the scene's :py:attr:`~Scene.pipelines` list will be left out.

The saved scene may be restored again from disk by

    * calling the :py:meth:`Scene.load` method,
    * using the :command:`-o` command line option of the :program:`ovitos` interpreter, or
    * opening the saved state file with the OVITO Pro desktop application.

When the state file is loaded back from disk, the global :py:attr:`Scene.pipelines` list will contain again all pipelines
that were part of the scene at the time it was saved, including all modifiers and their settings.
See also the section :py:ref:`saving_loading_pipelines`."""
        ...

    def load(self, filename: str) -> None:
        """Loads all pipelines stored in a .ovito session state file.
This function works like the :ref:`'Load Session State' function of the desktop application <manual:usage.saving_loading_scene>`.
It can load session state files that were produced with the *OVITO Pro* desktop application or which have been written by the
:py:meth:`Scene.save` method. **It cannot load session files created with the OVITO Basic desktop application.**

After the state file has been loaded, the :py:attr:`pipelines` list will be populated with exact copies of the data pipelines
that were part of the scene at the time it was saved. See also :pythis section for more information."""
        ...

def enable_logging() -> None:
    """You can call this function at the beginning of your Python script to enable logging of otherwise unnoticeable operations performed by OVITO.
Whenever OVITO performs long-running work or computations, it will print informational messages to ``stderr`` to indicate the current activity,
e.g. file I/O, modifier execution, and image rendering."""
    ...

def init_qt_app(support_gui: bool) -> None:
    ...
version: Tuple[int, int, int]
'A module-level attribute reporting the OVITO program version number.'
version_string: str
'Module-level attribute reporting the OVITO program version (as a string).'
scene: Scene
'This module-level variable points to the global :py:class:`~ovito.Scene` object,\nwhich serves as context for all operations performed by the script. The :py:class:`~ovito.Scene` object\nrepresents the program state and provides access to the contents of the visualization scene'