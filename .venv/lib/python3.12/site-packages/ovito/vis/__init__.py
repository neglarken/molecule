"""
This module contains classes related to :ref:`data visualization and rendering <rendering_intro>`.

**Rendering:**

  * :py:class:`Viewport`

**Rendering engines:**

  * :py:class:`OpenGLRenderer`
  * :py:class:`TachyonRenderer`
  * :py:class:`OSPRayRenderer`
  * :py:class:`AnariRenderer`

**Data visualization elements:**

  * :py:class:`DataVis` (base class for all visual elements)
  * :py:class:`BondsVis`
  * :py:class:`DislocationVis`
  * :py:class:`ParticlesVis`
  * :py:class:`SimulationCellVis`
  * :py:class:`SurfaceMeshVis`
  * :py:class:`LinesVis`
  * :py:class:`TriangleMeshVis`
  * :py:class:`VectorVis`
  * :py:class:`VoxelGridVis`

**Viewport overlays:**

  * :py:class:`ViewportOverlay` (base class for all built-in overlay types)
  * :py:class:`ViewportOverlayInterface` (abstract base class for user-defined viewport overlays)
  * :py:class:`ColorLegendOverlay`
  * :py:class:`CoordinateTripodOverlay`
  * :py:class:`PythonViewportOverlay`
  * :py:class:`TextLabelOverlay`

"""
__all__ = ['Viewport', 'OpenGLRenderer', 'DataVis',
        'CoordinateTripodOverlay', 'PythonViewportOverlay', 'TextLabelOverlay', 'ViewportOverlay',
        'TriangleMeshVis', 'ViewportOverlayInterface']
