from __future__ import annotations
import ovito
import ovito.pipeline
from ..data import DataCollection
import abc
import os
import traits.api
from typing import Any

class PipelineSourceInterface(traits.api.HasTraits):
    """
    Base: :py:class:`traits.has_traits.HasTraits`

    .. versionadded:: 3.9.1

    Abstract base class for :ref:`custom pipeline sources <manual:data_source.python_script>` in Python.
    Implementations of the interface must at least provide the :py:meth:`create` method.

    **Example:**

    .. literalinclude:: ../example_snippets/pipeline_source_interface.py
        :lines: 5-15

    Next, you can build a new :py:class:`Pipeline` using this pipeline source by wrapping it in a :py:class:`~ovito.pipeline.PythonSource` object:

    .. literalinclude:: ../example_snippets/pipeline_source_interface.py
        :lines: 20-23

    """

    # Event trait is is fired whenver the number of trajectory frames the source generates changes.
    _trajectory_length_changed_event = traits.api.Event(descr='Requests recomputation of the number of animation frames')

    def notify_trajectory_length_changed(self):
        """
        Notifies the pipeline system that the number of output animation frames this source can generate has changed.
        The class should call this method whenever the return value of its :py:meth:`compute_trajectory_length` method
        changes, for example, as a consequence of a parameter change.
        """
        # Trigger event trait to notify OVITO pipeline system.
        self._trajectory_length_changed_event = 1

    # Abstract method that must be implemented by all sub-classes:
    @abc.abstractmethod
    def create(self, data: DataCollection, *, frame: int, **kwargs: Any):
        """
        The generator function which gets called by the pipeline system to let the source do its thing and produce a data collection.

        :param data: Data collection which should be populated by the function. It may already contain data from previous runs.
        :param frame: Zero-based trajectory frame number.
        :param kwargs: Any further arguments that may be passed in by the pipeline system. This parameter should always be part of the function signature for forward compatibility with future versions of OVITO.
        """
        raise NotImplementedError("Abstract method create() must be implemented by the PipelineSourceInterface derived class.")

    # Define the optional methods only when generating the Sphinx documentation for the OVITO module.
    if os.environ.get('OVITO_SPHINX_BUILD', False):

        @abc.abstractmethod
        def compute_trajectory_length(self, **kwargs: Any) -> int:
            """
            A source that would like to control the number of trajectory frames shown in the timeline of OVITO should implement this method to communicate
            the number of frames it is able to generate.

            :param kwargs: Captures any arguments that may be passed in by the pipeline system in the future.
            :returns: The number of animation frames this source can generate.

            An implementation of :py:meth:`compute_trajectory_length` must return a positive integer. The value will serve as timeline length,
            which will be used by OVITO for animation rendering and such. The pipeline system will subsequently invoke your class' :py:meth:`create` method with
            *frame* parameter values ranging from 0 to the trajectory length minus 1.

            If you do not implement the :py:meth:`compute_trajectory_length` method, the pipeline system will assume your source can generate just one
            static configuration (frame 0).

            **Example:**

            .. literalinclude:: ../example_snippets/pipeline_source_interface_anim.py
               :lines: 5-30

            .. seealso:: :py:attr:`PipelineNode.num_frames`
            """
            raise NotImplementedError

ovito.pipeline.PipelineSourceInterface = PipelineSourceInterface