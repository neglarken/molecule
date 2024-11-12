"""
This module contains classes that are part of OVITO's data pipeline system.

**Pipelines:**

  * :py:class:`Pipeline` - a sequence of data input and processing steps (a data *source* followed by *modifiers*)
  * :py:class:`Modifier` - base class of all built-in data modification and processing algorithms of OVITO
  * :py:class:`ModifierInterface` - abstract base class for :ref:`user-defined modifiers <writing_custom_modifiers>`
  * :py:class:`PipelineNode` - base class for all types of pipeline steps
  * :py:class:`ModificationNode` - a pipeline step that processes some input data by applying a given modifier algorithm

**Pipeline data sources:**

  * :py:class:`FileSource` - loads input data from an external file
  * :py:class:`StaticSource` - passes an existing :py:class:`~ovito.data.DataCollection` object to the pipeline as input
  * :py:class:`PythonSource` - encapsulates a :py:class:`PipelineSourceInterface` or :ref:`user-defined pipeline source function <manual:data_source.python_script>`
  * :py:class:`PipelineSourceInterface` - abstract base class for user-defined dynamic data sources

"""

__all__ = ['Pipeline', 'Modifier', 'StaticSource', 'FileSource', 'PythonSource', 'ModifierInterface', 'PipelineSourceInterface', 'PipelineNode', 'ModificationNode', 'ModifierGroup']