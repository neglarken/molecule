from __future__ import annotations
import ovito
import ovito.pipeline
from ..data import DataCollection
from ..modifiers import PythonModifier
import abc
import os
import traits.api
from typing import Any, Union
import collections.abc

class ModifierInterface(traits.api.HasTraits):
    """
    Base: :py:class:`traits.has_traits.HasTraits`

    .. versionadded:: 3.8.0

    Abstract base class for :ref:`Python-based modifiers <writing_custom_modifiers>` that follow the :ref:`advanced programming interface <writing_custom_modifiers.advanced_interface>`.

    .. seealso:: :ref:`example_custom_time_average`
    """

    # Import the InputSlot helper class defined by the C++ code into the namespace of this class.
    class InputSlot(PythonModifier.InputSlot):
        """
        Represents the upstream pipeline generating the input data for a custom modifier implementation.
        """

        # Define these members only when generating the Sphinx documentation for the OVITO module.
        if os.environ.get('OVITO_SPHINX_BUILD', False):
            @property
            def num_frames(self) -> int:
                """
                The number of trajectory frames that the upstream pipeline connected to this input slot
                can produce. This field's value is the same as :py:attr:`input_node.num_frames <PipelineNode.num_frames>`.
                """
                return super().num_frames

            @property
            def input_node(self) -> ovito.pipeline.PipelineNode:
                """
                The :py:class:`PipelineNode` that forms outlet of the (upstream) pipeline connected to this modifier input slot.

                .. versionadded:: 3.10.0
                """
                return super().input_node

            def compute(self, frame: int) -> DataCollection:
                """
                Computes the results of the upstream pipeline connected to this input slot.

                *frame* specifies the trajectory frame to retrieve, which must be in the range 0 to (:py:attr:`num_frames`-1).

                The slot uses a caching mechanism to keep the data for one or more frames in memory. Thus, invoking :py:meth:`!compute`
                repeatedly to retrieve the same frame will typically be very fast.

                :param frame: The trajectory frame to retrieve from the upstream pipeline.
                """
                return super().compute(frame)

    # Event trait is is fired whenver the number of trajectory frames the modifier generates changes.
    _trajectory_length_changed_event = traits.api.Event(descr='Requests recomputation of the number of output animation frames')

    def notify_trajectory_length_changed(self):
        """
        Notifies the pipeline system that the number of output animation frames this modifier can compute has changed.
        The modifier class should call this method whenever the return value of its :py:meth:`compute_trajectory_length` method
        changes, for example, as a consequence of a parameter change.

        .. versionadded:: 3.9.1
        """
        # Trigger event trait to notify OVITO pipeline system.
        self._trajectory_length_changed_event = 1

    # Abstract method that must be implemented by all sub-classes:
    @abc.abstractmethod
    def modify(self,
               data: DataCollection,
               *,
               frame: int,
               input_slots: collections.abc.Mapping[str, ModifierInterface.InputSlot],
               data_cache: DataCollection,
               pipeline_node: ovito.pipeline.ModificationNode,
               **kwargs: Any):
        """
        The actual :ref:`work function <writing_custom_modifiers.advanced_interface.modify>` which gets called by the pipeline system to let the modifier do its thing.

        :param data: Data snapshot which should be modified by the modifier function in place.
        :param frame: Zero-based trajectory frame number.
        :param input_slots: One or more :py:class:`InputSlot` objects representing the :ref:`upstream data pipeline(s) connected to this modifier <writing_custom_modifiers.advanced_interface.additional_input_slots>`.
        :param data_cache: A data container (initially empty) which may be used by the modifier function to :ref:`store intermediate results <writing_custom_modifiers.advanced_interface.output_data_cache>`.
        :param pipeline_node: An object representing the use of this modifier in the pipeline that is currently being evaluated.
        :param kwargs: Any further arguments that may be passed in by the pipeline system. This parameter should always be part of the function signature for forward compatibility with future versions of OVITO.
        """
        raise NotImplementedError("Abstract method modify() must be implemented by the ModifierInterface derived class.")

    # Define the optional methods only when generating the Sphinx documentation for the OVITO module.
    if os.environ.get('OVITO_SPHINX_BUILD', False):

        @abc.abstractmethod
        def input_caching_hints(self,
                                frame: int,
                                *,
                                input_slots: collections.abc.Mapping[str, InputSlot],
                                pipeline_node: ovito.pipeline.ModificationNode,
                                **kwargs: Any) -> Union[collections.abc.Sequence[int], collections.abc.Mapping[InputSlot, Union[int, collections.abc.Sequence[int]]]]:
            """
            User-defined modifiers that :ref:`access multiple trajectory frames <writing_custom_modifiers.advanced_interface.trajectory>` in their :py:meth:`modify` method
            should implement this method to communicate the list of frames going to be needed. The pipeline system will keep the data of these trajectory frames
            in an internal cache to avoid unnecessary I/O and compute operations. See :ref:`writing_custom_modifiers.advanced_interface.caching`.

            :param frame: Zero-based trajectory frame number.
            :param input_slots: One or more :py:class:`InputSlot` objects representing the upstream data pipeline(s) connected to this modifier.
            :param pipeline_node: An object representing the use of this modifier in the pipeline that is currently being evaluated.
            :param kwargs: Any further arguments that may be passed in by the pipeline system. This parameter should always be part of the function signature for forward compatibility with future versions of OVITO.

            If your modifier defines :ref:`additional input slots <writing_custom_modifiers.advanced_interface.additional_input_slots>`, the function must
            return a dictionary that specifies for each input slot, including the standard *upstream* slot, which input frame(s) should be cached. For example::

                extra_slot = ovito.traits.OvitoObject(FileSource)

                def input_caching_hints(self, frame, **kwargs):
                    return {
                        'upstream': frame,
                        'extra_slot': 0
                    }

            If your modifier does *not* define :ref:`additional input slots <writing_custom_modifiers.advanced_interface.additional_input_slots>`, i.e.
            it only uses data produced by the upstream pipeline at certain frames, it is sufficient to return a list of frame numbers to
            be cached by the pipeline system::

                def input_caching_hints(self, frame, **kwargs):
                    # Cache current input frame and preceding frame:
                    return [frame, frame - 1]

            .. note::

                This method is supposed to be implemented as part of a :ref:`user-defined modifier class <writing_custom_modifiers.advanced_interface>`
                but it should not be called by user code. The pipeline system will automatically invoke this method whenever necessary.

            .. seealso:: :ref:`example_calculate_displacement_vectors`
            """
            raise NotImplementedError

        @abc.abstractmethod
        def compute_trajectory_length(self,
                                      *,
                                      input_slots: collections.abc.Mapping[str, InputSlot],
                                      data_cache: DataCollection,
                                      pipeline_node: ovito.pipeline.ModificationNode,
                                      **kwargs: Any) -> int:
            """
            A modifier that would like to control the number of trajectory frames shown in the timeline of OVITO should implement this method to communicate
            the number of frames it is able to compute. For example, your modifier could take a static configuration as input (a single frame)
            and produce multiple output frames from it by synthesizing a trajectory. OVITO's :py:class:`~ovito.modifiers.LoadTrajectoryModifier`
            and :py:class:`~ovito.modifiers.SmoothTrajectoryModifier` are examples for modifiers offering this special capability.

            :param input_slots: One or more :py:class:`InputSlot` objects representing the upstream data pipeline(s) connected to this modifier.
            :param data_cache: A data container (initially empty) which may be used by the modifier function to :ref:`store intermediate results <writing_custom_modifiers.advanced_interface.output_data_cache>`.
            :param pipeline_node: An object representing the use of this modifier in the pipeline whose trajectory length is being computed.
            :param kwargs: Any other arguments that may be passed in by the pipeline system.
            :returns: The number of animation frames this modifier can generate.

            An implementation of :py:meth:`compute_trajectory_length` must return a positive integer. The value will serve as new timeline length,
            which will be used by OVITO for animation rendering and such. The pipeline system will invoke your modifier's :py:meth:`modify` method with
            *frame* parameter values ranging from 0 to the new trajectory length minus 1, and any subsequent modifiers in the downstream pipeline
            will see the new trajectory length.

            If you do not implement the :py:meth:`compute_trajectory_length` method, the pipeline system will assume that the number of output
            frames of the modifier is equal to the number of input trajectory frames coming from the upstream pipeline.

            **Examples:**

            This modifier filters out every other frame of the input trajectory:

            .. literalinclude:: ../example_snippets/modifier_interface_skip_frames.py
               :lines: 5-16

            The following modifier takes a static configuration as input and synthesizes animation frames to produce
            a turntable animation (similar to :ref:`this tutorial <manual:tutorials.turntable_animation>`).
            The length of the animation is controlled by the adjustable modifier parameter `duration`.
            We must call :py:meth:`notify_trajectory_length_changed` whenever the value of this parameter changes,
            because it means the return value of :py:meth:`compute_trajectory_length` changes too.

            .. literalinclude:: ../example_snippets/modifier_interface_turntable_anim.py
               :lines: 5-30

            .. versionadded:: 3.9.1
            """
            raise NotImplementedError

ovito.pipeline.ModifierInterface = ModifierInterface