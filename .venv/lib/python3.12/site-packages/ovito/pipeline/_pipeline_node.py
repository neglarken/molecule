from typing import Optional
from . import PipelineNode
from ..nonpublic import PipelineStatus
from ..data import DataCollection

def _PipelineNode_compute(self, frame: Optional[int] = None) -> DataCollection:
    """ Requests the results from this pipeline node. Calling this function may implicitly lead to an evaluation of
        all preceding pipeline nodes in the pipeline, if necessary. The function returns a new :py:class:`~ovito.data.DataCollection` object containing the
        result data for a single trajectory frame.

        The optional *frame* parameter determines the frame to compute, which must be in the range 0 through (:py:attr:`num_frames`-1).
        If you don't specify a frame number, the current time slider position of the OVITO GUI will be used
        (always frame 0 if called from a non-interactive Python script).

        The pipeline node uses a caching mechanism, keeping the output data for one or more trajectory frames in memory. Thus, invoking :py:meth:`!compute`
        repeatedly to retrieve the same frame will typically be very fast.

        :param frame: The trajectory frame to retrieve or compute.
        :return: A new :py:class:`~ovito.data.DataCollection` containing the frame's data.
    """
    state = self._evaluate(frame)
    if state.status.type == PipelineStatus.Type.Error:
        raise RuntimeError(f"Data source evaluation failed: {state.status.text}")
    if state.data is None:
        raise RuntimeError("Data pipeline did not yield any output DataCollection.")

    return state.mutable_data

PipelineNode.compute = _PipelineNode_compute