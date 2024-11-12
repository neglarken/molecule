"""This module contains classes related to data visualization and rendering.

Rendering:

  * :py:class:`Viewport`

Rendering engines:

  * :py:class:`OpenGLRenderer`
  * :py:class:`TachyonRenderer`
  * :py:class:`OSPRayRenderer`
  * :py:class:`AnariRenderer`

Data visualization elements:

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

Viewport overlays:

  * :py:class:`ViewportOverlay` (base class for all built-in overlay types)
  * :py:class:`ViewportOverlayInterface` (abstract base class for user-defined viewport overlays)
  * :py:class:`ColorLegendOverlay`
  * :py:class:`CoordinateTripodOverlay`
  * :py:class:`PythonViewportOverlay`
  * :py:class:`TextLabelOverlay`"""
__all__ = ['Viewport', 'OpenGLRenderer', 'DataVis', 'CoordinateTripodOverlay', 'PythonViewportOverlay', 'TextLabelOverlay', 'ViewportOverlay', 'TriangleMeshVis', 'ViewportOverlayInterface', 'AnariRenderer', 'LinesVis', 'SimulationCellVis', 'TrajectoryLinesVis', 'ColorLegendOverlay', 'SurfaceMeshVis', 'VoxelGridVis', 'ParticlesVis', 'VectorVis', 'BondsVis', 'TrajectoryVis', 'DislocationVis', 'OSPRayRenderer', 'TachyonRenderer']
from __future__ import annotations
from typing import Tuple, Optional, Any, Union, Sequence, MutableSequence, Callable, Generator, Literal
import enum
from numpy.typing import NDArray
import numpy
from dataclasses import dataclass
from contextlib import contextmanager
import ovito
import ovito.modifiers
import ovito.pipeline
import ovito.data
import PySide6.QtCore
import PySide6.QtGui
import PySide6.QtWidgets
import ipywidgets
import matplotlib.figure
Color = Tuple[float, float, float]
Vector3 = Tuple[float, float, float]

class ViewportOverlayInterface:
    """Base: :py:class:`traits.has_traits.HasTraits`

Abstract base class for custom viewport overlays written in Python.

When you write a new viewport overlay, you must implement the :py:meth:`render` method, which gets called by the system each time a
:py:class:`Viewport` window is being rendered:

```python
  from ovito.vis import ViewportOverlayInterface
  
  class MyOverlay(ViewportOverlayInterface):
      def render(self, canvas: ViewportOverlayInterface.Canvas, **kwargs):
          canvas.draw_text("Hello world", pos=(0.5, 0.5))
```

If you are working with OVITO Pro, you can add your overlay to one of the interactive viewport windows.
If you are writing a standalone Python program to render images or movies using the :py:meth:`Viewport.render_image` and :py:meth:`Viewport.render_anim`
methods, you need to add your overlay to the viewport's :py:attr:`~Viewport.overlays` or :py:attr:`~Viewport.underlays` lists.

When adding your overlay to one of these lists, the instance must be wrapped in a :py:class:`PythonViewportOverlay` object as follows:

```python
  from ovito.vis import Viewport, PythonViewportOverlay
  
  vp = Viewport()
  vp.overlays.append( PythonViewportOverlay( delegate=MyOverlay() ) )
```"""

    class Canvas:
        """The system passes an instance if this class to the :py:meth:`ViewportOverlayInterface.render` method. It provides various painting functions
for drawing 2d graphics on top of (or under) the 3d scene."""

        @property
        def is_perspective(self) -> bool:
            ...

        @property
        def field_of_view(self) -> float:
            ...

        @property
        def logical_size(self) -> tuple[int, int]:
            ...

        @property
        def physical_size(self) -> tuple[int, int]:
            ...

        @property
        def device_pixel_ratio(self) -> float:
            ...

        @property
        def view_tm(self) -> NDArray[numpy.float64]:
            ...

        @property
        def projection_tm(self) -> NDArray[numpy.float64]:
            ...

        @property
        def preferred_qimage_format(self) -> PySide6.QtGui.QImage.Format:
            ...

        def project_location(self, world_xyz: Vector3) -> Optional[NDArray[numpy.float64]]:
            ...

        def project_length(self, world_xyz: Vector3, length: float) -> float:
            ...

        def draw_image(self, image: PySide6.QtGui.QImage, pos: tuple[float, float]=(0.0, 0.0), size: Optional[tuple[float, float]]=(1.0, 1.0), anchor: Literal['center', 'north west', 'west', 'south west', 'south', 'south east', 'east', 'north east', 'north']='south west') -> None:
            """Draws a pixel-based image onto the canvas. The image must be provided as PySide6 `QImage <https://doc.qt.io/qtforpython/PySide6/QtGui/QImage.html>`__.
If it includes an alpha channel, the pixel colors will be combined with the canvas' existing contents using *source over* blending mode.

The location and size at which to draw the image are both specified in reduced coordinates (relative to the :py:attr:`logical_size` of the canvas).
If you specify ``None`` as size, it gets calculated automatically by the method such that each pixel of the image corresponds to one (logical) pixel of the
canvas framebuffer. The *anchor* parameter controls how the image is laid out relative to the anchor position.

:param image: `QImage <https://doc.qt.io/qtforpython/PySide6/QtGui/QImage.html>`__ to paint onto the canvas.
:param pos: Position of the anchor point within the bounds of the canvas in reduced (fractional) coordinates. The origin (0,0) is in the lower left corner of the canvas, (1,1) in the upper right.
:param size: Size of the destination rectangle in reduced (fractional) coordinates.
:param anchor: Position of the anchor point relative to the image. Must be one of ``"center"``, ``"north west"``, ``"west"``, ``"south west"``, ``"south"``, ``"south east"``, ``"east"``, ``"north east"``, ``"north"``.

.. tip::

    The `QImage <https://doc.qt.io/qtforpython/PySide6/QtGui/QImage.html>`__ class supports `several pixel formats <https://doc.qt.io/qtforpython-6/PySide6/QtGui/QImage.html#PySide6.QtGui.QImage.Format>`__.
    For best performance, create an QImage using :py:attr:`preferred_qimage_format`.

Example

```python
  from ovito.vis import ViewportOverlayInterface
  from ovito.qt_compat import QtGui
  
  class ImageOverlay(ViewportOverlayInterface):
      def render(self, canvas: ViewportOverlayInterface.Canvas, **kwargs):
          image = QtGui.QImage(320, 240, canvas.preferred_qimage_format)
          image.fill(QtGui.QColor.fromRgbF(1.0, 0.0, 0.0, 0.3))
          canvas.draw_image(image, pos=(0.5, 0.5), size=(0.5, 0.5), anchor="center")
```"""
            ...

        def draw_text(self, text: str, pos: tuple[float, float], font_size: float=0.05, anchor: Literal['center', 'north west', 'west', 'south west', 'south', 'south east', 'east', 'north east', 'north']='south west', color: Color=(0.0, 0.0, 0.0), alpha: float=1.0, outline_width: float=0.0, outline_color: Color=(1.0, 1.0, 1.0), tight_layout: bool=False, rotation: float=0.0) -> None:
            """Draws a text string onto the canvas.

The location where to draw the text on the canvas is specified in reduced coordinates (relative to the :py:attr:`logical_size` of the canvas).
The *anchor* parameter controls how the text is laid out relative to the anchor position.

The text string can include HTML markup elements which control the format, e.g., to produce special notations such as superscripts or subscripts.
See :ref:`manual:viewport_layers.text_label.text_formatting` for further information.

:param text: The text to draw.
:param pos: Position of the anchor point on the canvas in reduced (fractional) coordinates. The origin (0,0) is in the lower left corner of the canvas, (1,1) in the upper right.
:param font_size: The size of the text font specified as a fraction of the height of the viewport canvas.
:param anchor: Position of the anchor point relative to the text bounds. This controls the alignment of the text. Must be one of ``"center"``, ``"north west"``, ``"west"``, ``"south west"``, ``"south"``, ``"south east"``, ``"east"``, ``"north east"``, ``"north"``.
:param color: Color of the text. RGB components must be in the range 0-1.
:param alpha: Alpha component of the text color. A value below 1.0 makes the text semi-transparent.
:param outline_width: Width of the outline to draw around the glyphs in units of logical pixels.
:param outline_color: Color of the text outline. RGB components must be in the range 0-1.
:param tight_layout: Controls whether the true (pixel-precise) bounds of the text are used when laying it out with respect to the anchor position.
                     The default mode is to use a more extended bounding box, which is based on the general ascent and descent (line height) of the font.
:param rotation: Rotation of the text in radians around the anchor point.

.. seealso:: :py:meth:`text_bounds`"""
            ...

        def text_bounds(self, text: str, pos: tuple[float, float]=(0.0, 0.0), font_size: float=0.05, anchor: Literal['center', 'north west', 'west', 'south west', 'south', 'south east', 'east', 'north east', 'north']='south west', outline_width: float=0.0, tight_layout: bool=False, rotation: float=0.0) -> tuple[tuple[float, float], tuple[float, float]]:
            """Calculates the axis-aligned bounding box of a text as if it were drawn by :py:meth:`draw_text`.
The parameters have the same meaning and default values as in the :py:meth:`draw_text` method.

:param text: The text for which to compute the bounding box.
:param pos: Position of the anchor point on the canvas in reduced (fractional) coordinates. The origin (0,0) is in the lower left corner of the canvas, (1,1) in the upper right.
:param font_size: The size of the text font specified as a fraction of the height of the viewport canvas.
:param anchor: Position of the anchor point relative to the text bounds. This controls the alignment of the text. Must be one of ``"center"``, ``"north west"``, ``"west"``, ``"south west"``, ``"south"``, ``"south east"``, ``"east"``, ``"north east"``, ``"north"``.
:param outline_width: Width of the outline to draw around the glyphs in units of logical pixels.
:param tight_layout: Controls whether the true (pixel-precise) bounds of the text are used when laying it out with respect to the anchor position.
                     The default mode is to use a more extended bounding box, which is based on the general ascent and descent (line height) of the font.
:param rotation: Rotation of the text in radians around the anchor point.
:return: A tuple containing the coordinates of the lower left corner of the bounding box and its size (all in reduced canvas coordinates)."""
            ...

        @contextmanager
        def qt_painter(self) -> Generator[PySide6.QtGui.QPainter, None, None]:
            """Creates a `QPainter <https://doc.qt.io/qtforpython/PySide6/QtGui/QPainter.html>`__ object providing advanced
drawing methods. The painter lets you `paint complex graphics <https://doc.qt.io/qtforpython-6/PySide6/QtGui/QPainter.html#more>`__ onto the viewport canvas.

The method returns a Python context manager, which must be used in a ``with`` statement to obtain the actual `QPainter <https://doc.qt.io/qtforpython/PySide6/QtGui/QPainter.html>`__:

```python
  from ovito.vis import ViewportOverlayInterface
  from ovito.qt_compat import QtGui
  
  class PainterOverlay(ViewportOverlayInterface):
      def render(self, canvas: ViewportOverlayInterface.Canvas, **kwargs):
  
          with canvas.qt_painter() as painter:
              pen = QtGui.QPen(QtGui.QColor(255,0,0))
              brush = QtGui.QBrush(QtGui.QGradient(QtGui.QGradient.OrangeJuice))
              painter.setPen(pen)
              painter.setBrush(brush)
              painter.drawEllipse(painter.window())
```

The QPainter's `window rect <https://doc.qt.io/qtforpython-6/PySide6/QtGui/QPainter.html#PySide6.QtGui.QPainter.window>`__ is configured
to match the canvas' :py:attr:`logical_size`. The QPainter's `viewport rect <https://doc.qt.io/qtforpython-6/PySide6/QtGui/QPainter.html#PySide6.QtGui.QPainter.viewport>`__ is configured
to match the canvas' :py:attr:`physical_size`. See `Window-Viewport Conversion <https://doc.qt.io/qtforpython-6/overviews/coordsys.html#window-viewport-conversion>`__.

Internally, the method creates a temporary `QImage <https://doc.qt.io/qtforpython/PySide6/QtGui/QImage.html>`__ for the
`QPainter <https://doc.qt.io/qtforpython/PySide6/QtGui/QPainter.html>`__ to draw into. When leaving the ``with`` block,
that image gets copied to the canvas using the :py:meth:`draw_image` method."""
            ...

        @contextmanager
        def mpl_figure(self, pos: tuple[float, float]=(0.5, 0.5), size: tuple[float, float]=(0.5, 0.5), anchor: Literal['center', 'north west', 'west', 'south west', 'south', 'south east', 'east', 'north east', 'north']='center', font_scale: float=1.0, alpha: float=0.0, tight_layout: bool=False) -> Generator[matplotlib.figure.Figure, None, None]:
            """A context manager for creating and rendering a `Matplotlib <https://matplotlib.org>`__ figure onto the canvas.

This method creates a Matplotlib figure and renders it onto the viewport canvas. Inside a `with` statement, you can add various types of plots
to the Matplotlib figure. The figure is then drawn onto the canvas.

:param pos: Position of the anchor point for placing the figure on the canvas. The origin (0,0) is in the lower left corner of the canvas, (1,1) in the upper right.
:param size: Size of the figure in relative viewport canvas coordinates, specified as a tuple *(width, height)*.
:param anchor: Position of the anchor point relative to the figure bounds. Must be one of ``"center"``, ``"north west"``, ``"west"``, ``"south west"``, ``"south"``, ``"south east"``, ``"east"``, ``"north east"``, ``"north"``.
:param font_scale: Scaling factor applied to the fonts in the figure. Useful for adjusting the text size of axis labels.
:param alpha: Transparency level of the figure background. A value of 0.0 makes the background fully transparent, while 1.0 makes it opaque.
:param tight_layout: Controls whether to automatically adjust subplot parameters for a "tight" layout.
:return: A generator yielding a `Matplotlib figure <https://matplotlib.org/stable/api/figure_api.html#matplotlib.figure.Figure>`__. The figure is automatically closed and copied to the canvas after the generator exits.

Example

Create a Matplotlib figure, plot some data dynamically calculated by a :py:class:`HistogramModifier` as part of a data pipeline,
and render it onto the viewport canvas:

```python
  from ovito.vis import ViewportOverlayInterface
  from ovito.data import DataCollection
  
  class HistogramOverlay(ViewportOverlayInterface):
      def render(self, canvas: ViewportOverlayInterface.Canvas, data: DataCollection, **kwargs):
          with canvas.mpl_figure(pos=(0,1), size=(0.4,0.4), anchor="north west", alpha=1, tight_layout=True) as fig:
              ax = fig.subplots()
              ax.set_title('Potential energy distribution')
              distribution = data.tables['histogram[Potential Energy]'].xy()
              ax.plot(distribution[:,0], distribution[:,1])
```

To use the :py:meth:`mpl_figure` method, you first need to install the `matplotlib` Python module.
    See :ref:`ovitos_install_modules`.

.. seealso:: :ref:`example_data_plot_overlay`"""
            ...

    @abc.abstractmethod
    def render(self, canvas: Canvas, *, data: ovito.data.DataCollection, pipeline: Optional[ovito.pipeline.Pipeline], interactive: bool, frame: int, **kwargs: Any) -> None:
        """Abstract method to implement custom rendering of viewport overlays.

This method must be overridden in subclasses of :py:class:`ViewportOverlayInterface` to define the custom rendering behavior for the overlay.
When the viewport window is being rendered, this method is called by the system to generate the overlay's visual content.

:param canvas: An object provided by the system, which offers various painting functions for drawing 2D graphics on top of the 3D scene.
:param data: The data collection produced by the overlay's associated :py:attr:`~PythonViewportOverlay.pipeline`. It contains the dynamically computed data that can be used for rendering the overlay.
:param pipeline: The overlay's associated :py:attr:`~PythonViewportOverlay.pipeline`.
:param interactive: A boolean flag indicating whether the rendering happens in an interactive context (in a GUI environment) or off-screen (e.g., for generating images and animations). Your overlay can use this to perform a long-running computation only in a non-interactive context and render a placeholder instead in the interactive viewports of the OVITO desktop app.
:param frame: The animation frame number currently being rendered.
:param kwargs: Captures any additional arguments that may be passed in by the system."""
        ...

@dataclass(kw_only=True)
class OpenGLRenderer:
    """This is the default rendering backend used by the :py:meth:`Viewport.render_image` and :py:meth:`Viewport.render_anim` functions.
It also serves in the OVITO desktop application for the real-time display of the 3d scene in the interactive viewport windows.
The OpenGL renderer uses your computer's GPU graphics hardware to accelerate the generation of images.
See the corresponding user manual page for more information.

Enabling OpenGL support

This rendering backend requires an environment where OpenGL graphics support is available. Standalone Python scripts typically
run in a headless environment, e.g. a text-based terminal without graphics support. This prevents the :py:class:`OpenGLRenderer` from
initializing an OpenGL context and an offscreen framebuffer to render into. A call to :py:meth:`Viewport.render_image` will raise an error in this case, and
you have to take one of the following steps to enable OpenGL graphics support -- or altogether avoid the problem by
using one of the software-based rendering backends instead.

The ``ovito`` Python module, if imported by a Python script running in an external Python interpreter, sets up a headless environment by default, in which OpenGL rendering
is *not* available. A proper graphics environment can be explicitly requested in two ways (starting with OVITO 3.7.10):

#. Setting the environment variable ``OVITO_GUI_MODE=1`` prior to importing the ``ovito`` package or any of its sub-modules:

   You can set the variable either externally, before or while launching your Python script program:

   .. code-block:: shell-session

     OVITO_GUI_MODE=1 python3 <your_script.py>

   or within the Python program itself by including the following lines *before* the first ``import ovito`` statement at the top of your .py file::

      import os
      os.environ['OVITO_GUI_MODE'] = '1' # Request a session with OpenGL support

#. Create a Qt application object with GUI support before importing the ``ovito`` module::

      import PySide6.QtWidgets
      app = PySide6.QtWidgets.QApplication() # This sets up an environment with GUI support

      from ovito.vis import *
      vp = Viewport()
      vp.render_image(renderer=OpenGLRenderer())

        Other Python packages imported by your Python script may also be using the Qt cross-platform toolkit
     (e.g. `Matplotlib's Qt backend <https://matplotlib.org/stable/users/explain/backends.html>`__). That means such a third-party package may
     also set up a global Qt application object, which will subsequently be shared with the ovito module. Furthermore, if you are executing
     your Python script in a graphical IDE such as *Spyder*, which `itself is based on the Qt framework <https://docs.spyder-ide.org/current/workshops/qt_fundamentals.html>`__, then
     a global application instance may already be present at the time the Python script is launched.

**Linux/Unix systems (including WSL2)**

On Linux/Unix systems, an X11 or Wayland display server is required for OpenGL graphics. When you request a graphics session
with one of the methods described above, the Qt framework will attempt to establish a connection to the X11/Wayland server.
If this fails, e.g., because the `DISPLAY environment variable <https://stackoverflow.com/questions/20947681/understanding-linux-display-variable>`__
is not set correctly, Qt reports an error and the program will quit with the following message:

.. code-block:: shell-session

  qt.qpa.xcb: could not connect to display
  qt.qpa.plugin: Could not load the Qt platform plugin "xcb" in "" even though it was found.
  This application failed to start because no Qt platform plugin could be initialized. Reinstalling the application may fix this problem.

Remote servers and HPC clusters, which are typically accessed via SSH terminals, often do not provide a running graphical desktop environment
that would allow the use of OpenGL functions by OVITO. In such a headless environment it may still be possible to
provide a `virtual X server <https://en.wikipedia.org/wiki/Xvfb>`__ to the Python application,
e.g., using the `xvfb-run <https://manpages.ubuntu.com/manpages/xenial/man1/xvfb-run.1.html>`__ wrapper command:

.. code-block:: shell-session

  OVITO_GUI_MODE=1 xvfb-run python3 <your_script.py>"""
    antialiasing_level: int = 3
    'antialiasing_level() -> int\n\nA positive integer controlling the level of supersampling. If 1, no supersampling is performed. For larger values, the image in rendered at a higher resolution and then scaled back to the output size to reduce aliasing artifacts.\n\nDefault: ``3``'
    order_independent_transparency: bool = False
    'order_independent_transparency() -> bool\n\nControls how semi-transparent objects are rendered when they occlude each other. \n\nAny OpenGL-based rendering technique for semi-transparent objects represents an approximation of how a true rendition of semi-transparent objects would look like.\n\nThe default back-to-front ordered rendering technique used by the OpenGL renderer gives correct results if there is only one kind of semi-transparent object in the scene, e.g. just particles, but likely fails to render a mixture of different semi-transparent objects correctly, e.g. semi-transparent particles combined with semi-transparent surface meshes or bonds. \n\n`Weighted Blended Order-Independent Transparency <https://jcgt.org/published/0002/02/09/>`__, which can be selecting by setting this parameter to ``True``, is an alternative method more suitable for overlapping semi-transparent objects of different kinds. But it delivers only a rough approximation of translucency.\n\nDefault: ``False``'

    @staticmethod
    def is_available() -> bool:
        ...

@dataclass(kw_only=True)
class TachyonRenderer:
    """This is one of the software-based rendering backends of OVITO. Tachyon is an open-source raytracing engine integrated into OVITO.

An instance of this class can be passed to the :py:meth:`Viewport.render_image` or :py:meth:`Viewport.render_anim` methods. 

Tachyon can render scenes with ambient occlusion lighting, semi-transparent objects, and depth-of-field focal blur. See the corresponding user manual page for more information on this rendering backend."""
    ambient_occlusion: bool = True
    'ambient_occlusion() -> bool\n\nEnables ambient occlusion shading. Enabling this lighting technique mimics some of the effects that occur under conditions of omnidirectional diffuse illumination, e.g. outdoors on an overcast day.\n\nDefault: ``True``'
    ambient_occlusion_brightness: float = 0.8
    'ambient_occlusion_brightness() -> float\n\nControls the brightness of the sky light source used for ambient occlusion.\n\nDefault: ``0.8``'
    ambient_occlusion_samples: int = 12
    'ambient_occlusion_samples() -> int\n\nAmbient occlusion is implemented using a Monte Carlo technique. This parameters controls the number of samples to compute. A higher sample count leads to a more even shading, but requires more computation time.\n\nDefault: ``12``'
    antialiasing: bool = True
    'antialiasing() -> bool\n\nEnables supersampling to reduce aliasing effects.\n\nDefault: ``True``'
    antialiasing_samples: int = 12
    'antialiasing_samples() -> int\n\nThe number of supersampling rays to generate per pixel to reduce aliasing effects.\n\nDefault: ``12``'
    aperture: float = 0.01
    'aperture() -> float\n\nControls the aperture of the camera, which is used for depth-of-field rendering.\n\nDefault: ``0.01``'
    depth_of_field: bool = False
    'depth_of_field() -> bool\n\nThis flag enables depth-of-field rendering.\n\nDefault: ``False``'
    direct_light: bool = True
    'direct_light() -> bool\n\nEnables the parallel light source, which is positioned at an angle behind the camera.\n\nDefault: ``True``'
    direct_light_intensity: float = 0.9
    'direct_light_intensity() -> float\n\nControls the brightness of the directional light source.\n\nDefault: ``0.9``'
    focal_length: float = 40.0
    'focal_length() -> float\n\nControls the focal length of the camera, which is used for depth-of-field rendering.\n\nDefault: ``40.0``'
    shadows: bool = True
    'shadows() -> bool\n\nEnables cast shadows for the directional light source.\n\nDefault: ``True``'
    max_ray_recursion: int = 50
    'max_ray_recursion() -> int\n\nMaximum number of overlapping semi-transparent surfaces that are considered by the renderer. This is the maximum recursion depth of the ray-tracing algorithm. \n\nDefault: ``50``\n\n.. versionadded: 3.11.0'

@dataclass(kw_only=True)
class OSPRayRenderer:
    """This is one of the software-based rendering backends of OVITO, which can generate images with higher fidelity than the standard :py:class:`OpenGLRenderer`. Typically, you create an instance of this class and pass it to the :py:meth:`Viewport.render_image` or :py:meth:`Viewport.render_anim` methods. 

OSPRay can render scenes with ambient occlusion lighting, semi-transparent objects, and depth-of-field focal blur. For technical details of the supported rendering algorithms and parameters, see the `www.ospray.org <https://www.ospray.org>`__ website. 

See also the corresponding user manual page for further information."""
    ambient_brightness: float = 0.8
    'ambient_brightness() -> float\n\nControls the radiance of the ambient light. \n\nDefault: ``0.8``'
    ambient_light_enabled: bool = True
    'ambient_light_enabled() -> bool\n\nEnables the ambient light, which surrounds the scene and illuminates it from infinity with constant radiance. \n\nDefault: ``True``'
    aperture: float = 0.5
    'aperture() -> float\n\nThe aperture radius controls how blurred objects will appear that are out of focus if :py:attr:`dof_enabled` is set. \n\nDefault: ``0.5``'
    denoising_enabled: bool = True
    'denoising_enabled() -> bool\n\nEnables the application of a denoising filter to the rendered image to reduce Monte Carlo noise inherent to stochastic ray tracing methods like path tracing. \n\nDefault: ``True``'
    direct_light_angular_diameter: float = numpy.radians(10.0)
    'direct_light_angular_diameter() -> float\n\nSpecifies the apparent size (angle in radians) of the default directional light source. Setting the angular diameter to a value greater than zero yields soft shadow. \n\nDefault: ``numpy.radians(10.0)``'
    direct_light_enabled: bool = True
    'direct_light_enabled() -> bool\n\nEnables the default directional light source that is positioned behind the camera and is pointing roughly along the viewing direction. The brightness of the light source is controlled by the :py:attr:`direct_light_intensity` parameter. \n\nDefault: ``True``'
    direct_light_intensity: float = 1.0
    'direct_light_intensity() -> float\n\nThe intensity of the default directional light source. The light source must be enabled by setting :py:attr:`direct_light_enabled`. \n\nDefault: ``1.0``'
    dof_enabled: bool = False
    'dof_enabled() -> bool\n\nEnables the depth-of-field effect (focal blur). Only objects exactly at the distance from the camera specified by the :py:attr:`focal_length` will appear sharp when depth-of-field rendering is enabled. Objects closer to or further from the camera will appear blurred. The strength of the effect is controlled by the :py:attr:`aperture` parameter. \n\nDefault: ``False``'
    focal_length: float = 40.0
    'focal_length() -> float\n\nOnly objects exactly at this distance from the camera will appear sharp when :py:attr:`dof_enabled` is set. Objects closer to or further from the camera will appear blurred. \n\nDefault: ``40.0``'
    material_shininess: float = 10.0
    'material_shininess() -> float\n\nSpecular Phong exponent value for the default material. Usually in the range between 2.0 and 10,000. \n\nDefault: ``10.0``'
    material_specular_brightness: float = 0.02
    'material_specular_brightness() -> float\n\nControls the specular reflectivity of the default material. \n\nDefault: ``0.02``'
    max_ray_recursion: int = 10
    'max_ray_recursion() -> int\n\nThe maximum number of recursion steps during ray-tracing. Normally, 1 or 2 is enough, but when rendering semi-transparent objects, a larger recursion depth is needed. This parameter specifies the maximum number of overlapping semi-transparent surfaces that are considered by the renderer. \n\nDefault: ``10``'
    max_scattering_events: int = 20
    'max_scattering_events() -> int\n\nMaximum number of non-specular (i.e., diffuse and glossy) bounces computed by the path-tracing renderer. \n\nDefault: ``20``\n\n.. versionadded: 3.11.0'
    refinement_iterations: int = 4
    'refinement_iterations() -> int\n\nThe OSPRay renderer supports a feature called adaptive accumulation, which is a progressive rendering method. During each rendering pass, the rendered image is progressively refined. This parameter controls the number of iterations until the refinement stops. \n\nDefault: ``4``'
    roulette_depth: int = 5
    'roulette_depth() -> int\n\nRay recursion depth at which to start Russian roulette termination in the path-tracing algorithm. \n\nDefault: ``5``\n\n.. versionadded: 3.11.0'
    samples_per_pixel: int = 8
    'samples_per_pixel() -> int\n\nThe number of ray-tracing samples computed per pixel. Larger values can help to reduce aliasing artifacts but take longer to compute. \n\nDefault: ``8``'
    sky_albedo: float = 0.3
    'sky_albedo() -> float\n\nControls the ground reflectance affecting the sky-sun light source. The light source must be enabled first by setting :py:attr:`sky_light_enabled`. Valid parameter range is [0.0 - 1.0].\n\nDefault: ``0.3``'
    sky_brightness: float = 2.0
    'sky_brightness() -> float\n\nThe intensity of the sky-sun light source. The light source must be enabled first by setting :py:attr:`sky_light_enabled`. \n\nDefault: ``2.0``'
    sky_light_enabled: bool = False
    'sky_light_enabled() -> bool\n\nEnables the sky/sun light source that mimics the light coming from the sky and the sun in an outdoor scene. The brightness of the sky is controlled by the :py:attr:`sky_brightness` parameter. \n\nDefault: ``False``'
    sky_turbidity: float = 3.0
    'sky_turbidity() -> float\n\nControls atmospheric turbidity due to particles affecting the sky-sun light source. The light source must be enabled first by setting :py:attr:`sky_light_enabled`. Valid parameter range is [1.0 - 10.0].\n\nDefault: ``3.0``'

@dataclass(kw_only=True)
class AnariRenderer:
    """Scientific visualization renderer based on the NVIDIA OptiX™ Ray Tracing Engine, which runs on CUDA-capable devices
(`VisRTX <https://github.com/NVIDIA/VisRTX>`__).
The renderer offers hardware accelerated ray-tracing and can generate high-fidelity
scene renderings including global illumination effects and shadows.

Please see :ref:`manual:rendering.visrtx_renderer` in the OVITO user manual for further information.
The class name :py:class:`AnariRenderer` derives from the fact that OVITO uses the `Khronos ANARI <https://www.khronos.org/anari>`__
interface to communicate with NVIDIA's VisRTX backend. Future versions of OVITO may support additional ANARI-compliant
rendering backends from other vendors.

 In case your system has multiple CUDA-capable devices, you can select a specific one for rendering using the `CUDA_VISIBLE_DEVICES <https://developer.nvidia.com/blog/cuda-pro-tip-control-gpu-visibility-cuda_visible_devices/>`__ environment variable."""
    samples_per_pixel: int = 16
    'samples_per_pixel() -> int\n\nThe number of ray-tracing samples computed per pixel. Larger values can help to reduce aliasing artifacts. \n\nDefault: ``16``'
    denoising_enabled: bool = True
    'denoising_enabled() -> bool\n\nEnables the application of a denoising filter to the rendered image to reduce image noise inherent to stochastic ray-tracing methods.\n\nDefault: ``True``'
    ambient_occlusion_samples: int = 8
    'ambient_occlusion_samples() -> int\n\nThe number of ambient light occlusion samples computed per pixel. Larger values can help to reduce visual artifacts.\n\nDefault: ``8``'
    ambient_light_radiance: float = 0.7
    'ambient_light_radiance() -> float\n\nRadiance of the ambient light source. The brightness is proportional to the radiance of the light source.\n\nDefault: ``0.7``'
    ambient_occlusion_distance: float = 20.0
    'ambient_occlusion_distance() -> float\n\nCutoff range for the ambient occlusion (AO) calculation. Distant objects beyond this range will not contribute to the computed occlusion factor. Decreasing this parameter will typically brighten up the inside of dark cavities that are otherwise fully occluded. Increasing the parameter value will make the AO effect stronger and lead to more brightness contrasts. \n\nDefault: ``30.0``'
    direct_light_latitude: float = 0.174532925199433
    "direct_light_latitude() -> float\n\nLatitude (north-south) position of the direct light source relative to the current camera viewing direction. Upon camera rotation, this light source will move with the camera, maintaining a constant relative direction. A value of ``0.0`` places the light source in line with the camera's view direction. Input is expected in radians, the valid parameter range is :math:`[-\\pi/2, +\\pi/2]`.\n\nDefault: ``numpy.deg2rad(10.0)``"
    direct_light_longitude: float = -0.174532925199433
    "direct_light_longitude() -> float\n\nLongitude (east-west) position of the direct light source relative to the current camera viewing direction. Upon camera rotation, this light source will move with the camera, maintaining a constant relative direction. A value of ``0.0`` places the light source in line with the camera's view direction. Input is expected in radians, the valid parameter range is :math:`[-\\pi, +\\pi]`.\n\nDefault: ``numpy.deg2rad(-10.0)``"
    direct_light_irradiance: float = 0.4
    'direct_light_irradiance() -> float\n\nIrradiance of the direct light source. The brightness of the light source is proportional to the irradiance. \n\nDefault: ``0.4``'
Renderer = Union[OpenGLRenderer, TachyonRenderer, OSPRayRenderer, AnariRenderer]

@dataclass(kw_only=True)
class ViewportOverlay:
    """Abstract base class for viewport :py:attr:`overlays` and :py:attr:`underlays`, which render two-dimensional graphics on top of (or behind) the three-dimensional scene. Examples are :py:class:`CoordinateTripodOverlay`, :py:class:`TextLabelOverlay` and :py:class:`ColorLegendOverlay`. You can also implement your own viewport overlay in Python by using the :py:class:`PythonViewportOverlay` class."""
    enabled: bool = True
    'enabled() -> bool\n\nControls whether the overlay gets rendered. An overlay can be hidden by setting its :py:attr:`enabled` property to ``False``. \n\nDefault: ``True``'

@dataclass(kw_only=True)
class ColorLegendOverlay(ViewportOverlay):
    """Base: :py:class:`ovito.vis.ViewportOverlay`

This layer renders a color legend over the viewport image, which helps your audience to recognize the meaning of depicted object colors.
You should add this :py:class:`ViewportOverlay` to the :py:attr:`Viewport.overlays` or :py:attr:`Viewport.underlays` list of the viewport
you use for rendering:

```python
  from ovito.vis import ColorLegendOverlay, Viewport
  from ovito.qt_compat import QtCore
  
  vp = Viewport(type=Viewport.Type.Top)
  
  legend = ColorLegendOverlay(
      title = 'Potential energy per atom',
      alignment = QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignTop,
      orientation = QtCore.Qt.Orientation.Vertical,
      offset_y = -0.04,
      font_size = 0.12,
      format_string = '%.2f eV')
  vp.overlays.append(legend)
```

Specifying the source of the displayed color map

Most importantly, you need to specify which color mapping the legend is supposed to display. There currently are three kinds of color map sources one can select for a legend:

  * The color map of a :py:class:`ColorCodingModifier`, which has been inserted into a data pipeline.
  * The color map of a visual element that supports pseudo-color mapping, e.g. :py:class:`SurfaceMeshVis`, :py:class:`VoxelGridVis`, :py:class:`LinesVis`, or :py:class:`VectorVis`.
  * The discrete colors of a typed property representing different particle types, bond types, etc.

To display the color map of a color coding modifier, including text labels indicating the corresponding numeric value range,
set the legend's :py:attr:`.modifier` field to point to the :py:class:`ColorCodingModifier`:

```python
  modifier = ColorCodingModifier(property='peatom')
  pipeline.modifiers.append(modifier)
  
  legend.modifier = modifier
```

If you have set up a visual element in your scene that supports pseudo-color mapping, e.g. a :py:class:`VoxelGridVis`
visualizing some grid property using pseudo-colors, then you can associate it with the color legend by
assigning it to the :py:attr:`color_mapping_source` field:

```python
  # Load a VASP volumetric charge density file:
  pipeline = import_file('input/CHGCAR.nospin.gz')
  pipeline.add_to_scene()
  
  # Configure the VoxelGridVis element responsible for displaying the charge density grid:
  grid_vis = pipeline.compute().grids['charge-density'].vis
  grid_vis.enabled = True
  grid_vis.color_mapping_property = 'Charge density' # Grid property to visualize using pseudo-colors
  grid_vis.color_mapping_interval = (0.02186, 0.05465)
  
  # Use the VoxelGridVis as color map source for the legend:
  legend.color_mapping_source = grid_vis
```

To display the discrete colors of a typed :py:class:`Property`, specify the source particle or bond property as follows:

```python
  legend.property = 'particles/Particle Type'
```

See the documentation of the :py:attr:`property` parameter for more information.

In all cases, if you have multiple pipelines in your scene, you may have to additionally specify the correct source pipeline
by setting the legend's :py:attr:`.pipeline` field."""
    alignment: PySide6.QtCore.Qt.Alignment = PySide6.QtCore.Qt.AlignHCenter ^ PySide6.QtCore.Qt.AlignBottom
    'alignment() -> PySide6.QtCore.Qt.Alignment\n\n\nSelects the corner of the viewport where the color bar is displayed (anchor position). This must be a valid `Qt.AlignmentFlag value <https://doc.qt.io/qtforpython-6/PySide6/QtCore/Qt.html#PySide6.QtCore.Qt.AlignmentFlag>`__ as shown in the code example above. \n\nDefault: ``QtCore.Qt.AlignmentFlag.AlignHCenter | QtCore.Qt.AlignmentFlag.AlignBottom``'
    aspect_ratio: float = 8.0
    'aspect_ratio() -> float\n\nThe aspect ratio of the color bar. Larger values make it more narrow. \n\nDefault: ``8.0``'
    border_color: Color = (0.0, 0.0, 0.0)
    'border_color() -> tuple[float, float, float]\n\nThe line color of the border painted around the color map. This is used only if :py:attr:`border_enabled` is set.\n\nDefault: ``(0.0, 0.0, 0.0)``'
    border_enabled: bool = False
    'border_enabled() -> bool\n\nEnables the painting of a border line around color map. \n\nDefault: ``False``'
    font: str = ''
    "font() -> str\n\nA string with comma-separated parameter values describing the font to be used for rendering the text labels of the viewport layer. The string must follow the specific form understood by the `QFont.fromString() <https://doc.qt.io/qtforpython-6/PySide6/QtGui/QFont.html#PySide6.QtGui.QFont.fromString>`__ method, for example ``'Arial,10,-1,5,75,0,0,0,0,0,Bold'``. \n\nNote that the font size parameter (10 in the example specification above) will be ignored by the viewport layer, because the size of text labels is already controlled by the :py:attr:`font_size` parameter."
    font_size: float = 0.1
    'font_size() -> float\n\nThe relative size of the font used for text labels.\n\nDefault: ``0.1``'
    label_size: float = 0.6
    'label_size() -> float\n\nThe relative size of the font used for the tick labels. Size given relative to :py:attr:`font_size`.\n\nDefault: ``0.6``'
    format_string: str = '%g'
    "format_string() -> str\n\nThe format string used with the `sprintf() <https://en.cppreference.com/w/cpp/io/c/fprintf>`__ function to generate the text representation of floating-point values. You can change this format string to control the number of displayed decimal places. \n\nLiteral text may be incorporated into the format string to include physical units, for example, and :ref:`manual:viewport_layers.text_label.text_formatting` is supported.\n\nDefault: ``'%g'``"
    label1: str = ''
    "label1() -> str\n\nSets the text string displayed at the upper end of the bar. If empty, the :py:attr:`end_value` of the :py:class:`ColorCodingModifier` is used. \n\nThe label supports :ref:`manual:viewport_layers.text_label.text_formatting`.\n\nDefault: ``''``"
    label2: str = ''
    "label2() -> str\n\nSets the text string displayed at the lower end of the bar. If empty, the :py:attr:`start_value` of the :py:class:`ColorCodingModifier` is used. \n\nThe label supports :ref:`manual:viewport_layers.text_label.text_formatting`.\n\nDefault: ``''``"
    legend_size: float = 0.3
    'legend_size() -> float\n\nControls the overall size of the color bar relative to the output image size. \n\nDefault: ``0.3``'
    modifier: Optional[ovito.modifiers.ColorCodingModifier] = None
    'modifier() -> Optional[ovito.modifiers.ColorCodingModifier]\n\nThe :py:class:`ColorCodingModifier` for which the color legend should be rendered.'
    offset_x: float = 0.0
    'offset_x() -> float\n\nThis parameter allows to displace the color bar horizontally from its anchor position. The offset is specified as a fraction of the output image width.\n\nDefault: ``0.0``'
    offset_y: float = 0.0
    'offset_y() -> float\n\nThis parameter allows to displace the color bar vertically from its anchor position. The offset is specified as a fraction of the output image height.\n\nDefault: ``0.0``'
    orientation: PySide6.QtCore.Qt.Orientation = PySide6.QtCore.Qt.Horizontal
    'orientation() -> PySide6.QtCore.Qt.Orientation\n\nSelects the orientation of the color bar. This must be a valid `Qt.Orientation value <https://doc.qt.io/qtforpython-6/PySide6/QtCore/Qt.html#PySide6.QtCore.Qt.Orientation>`__ as shown in the code example above. \n\nDefault: ``QtCore.Qt.Orientation.Horizontal``'
    outline_color: Color = (1.0, 1.0, 1.0)
    'outline_color() -> tuple[float, float, float]\n\nThe text outline color. This is used only if :py:attr:`outline_enabled` is set.\n\nDefault: ``(1.0, 1.0, 1.0)``'
    outline_enabled: bool = False
    'outline_enabled() -> bool\n\nEnables the painting of a font outline to make the text easier to read.\n\nDefault: ``False``'
    pipeline: Optional[ovito.pipeline.Pipeline] = None
    "pipeline() -> Optional[ovito.pipeline.Pipeline]\n\nThe :py:class:`Pipeline` in which the legend looks for the color map to be displayed. \n\nIf your visualization scene contains more than one data pipeline, you should set this field to select the right source pipeline. If you don't specify a pipeline, the legend will look for the color mapping in the first pipeline of the current scene. \n\nDefault: ``None``"
    text_color: Color = (0.0, 0.0, 0.0)
    'text_color() -> tuple[float, float, float]\n\nThe RGB color used for text labels.\n\nDefault: ``(0.0, 0.0, 0.0)``'
    title: str = ''
    "title() -> str\n\nThe text displayed next to the color bar. If this string is empty, the title of the source :py:class:`Property` object is used. \n\nThe title label supports :ref:`manual:viewport_layers.text_label.text_formatting`.\n\nDefault: ``''``"
    property: str = ''
    "property() -> str\n\nSpecifies the path to the typed :py:class:`Property` for which a discrete color legend should be rendered.\n\nThe specified path tells the legend where to find the particle or bond property whose discrete :py:attr:`types` it should\ndisplay. Generally, the selected property may be dynamically produced by the current data :py:attr:`.pipeline` and may\nnot exist yet at the point when you set up the :py:class:`ColorLegendOverlay`. That's why you have to reference it by name\ninstead of specifying a :py:class:`Property` object directly.\n\nThe path specifies where to find the selected property within the nested containers that make up the\n:py:class:`DataCollection` produced by the selected :py:attr:`.pipeline`. It consists of a sequence of `DataObject.identifier` strings separated by slashes. The last entry in the path is simply the name of the :py:class:`Property` to be displayed\nby the legend.\n\nExamples:\n\n```python\n  # Display the different structural types identified by PolyhedralTemplateMatchingModifier:\n  legend.property = 'particles/Structure Type'\n  \n  # Display the list of bond types in the system:\n  legend.property = 'particles/bonds/Bond Type'\n```\n\nIn case there are multiple data pipelines in the scene, you may have to explicitly specify the right source pipeline by setting\nthe legend's :py:attr:`pipeline` field.\n\nDefault: ``''``"
    color_mapping_source: Optional[DataVis] = None
    "color_mapping_source() -> Optional[ovito.vis.DataVis]\n\nThe :py:class:`DataVis` element to be used as color map source by this viewport layer. Set this to the :py:class:`SurfaceMeshVis`, :py:class:`VoxelGridVis`, :py:class:`LinesVis`, or :py:class:`VectorVis` element whose color map the legend should display. \n\nExample:\n\n```python\n  # Add modifier to the pipeline which generates particle trajectory lines:\n  modifier = GenerateTrajectoryLinesModifier(only_selected=False)\n  pipeline.modifiers.append(modifier)\n  \n  # Configure the modifier's LinesVis element to apply a color mapping to the lines:\n  modifier.vis.color_mapping_property = 'Time'\n  modifier.vis.color_mapping_interval = (0, pipeline.num_frames-1)\n  \n  # Add a color legend and link it to the LinesVis element to display its color map.\n  vp.overlays.append(ColorLegendOverlay(color_mapping_source=modifier.vis))\n```\n\nDefault: ``None``"
    ticks_enabled: bool = False
    'ticks_enabled() -> bool\n\nEnables the painting of tick marks and labels on the color map. \n\nDefault: ``False``'
    ticks_spacing: float = 0.0
    'ticks_spacing() -> float\n\nDefines the tick spacing along the (continuous) color scale. Requires :py:attr:`ticks_enabled` to be set. The standard value of 0 activates automatic tick placement based on the input value range.\n\nDefault: ``0.0``'
    rotate_title: bool = False
    "rotate_title() -> bool\n\nEnables the vertical orientation of the title, i.e. text orientation parallel to the color legend, if the legend's :py:attr:`orientation` is set to `QtCore.Qt.Vertical`. Otherwise this option is ignored and the title text will be rendered horizontally.\n\nDefault: ``False``"
    background_enabled: bool = False
    'background_enabled() -> bool\n\nEnables the painting of a color legend background. A filled panel will be drawn behind the legend to better distinguish the legend from the cluttered 3d scene in the background.\n\nDefault: ``False``'
    background_color: Color = (1.0, 1.0, 1.0)
    'background_color() -> tuple[float, float, float]\n\nThe color of the background panel. Only used if :py:attr:`background_enabled` is set.\n\nDefault: ``(1.0, 1.0, 1.0)``'

@dataclass(kw_only=True)
class CoordinateTripodOverlay(ViewportOverlay):
    """Base: :py:class:`ovito.vis.ViewportOverlay`

Displays a coordinate tripod in rendered images. You can attach an instance of this class to a viewport by adding it to the viewport's :py:attr:`overlays` collection:

```python
  from ovito.vis import CoordinateTripodOverlay, Viewport
  from ovito.qt_compat import QtCore
  
  # Create the overlay.
  tripod = CoordinateTripodOverlay()
  tripod.size = 0.07
  tripod.alignment = QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignBottom
  
  # Attach overlay to a newly created viewport.
  viewport = Viewport(type=Viewport.Type.Perspective, camera_dir=(1,2,-1))
  viewport.overlays.append(tripod)
```"""

    class Style(enum.Enum):
        """"""
        Flat = enum.auto()
        Solid = enum.auto()
    alignment: PySide6.QtCore.Qt.Alignment = PySide6.QtCore.Qt.AlignLeft ^ PySide6.QtCore.Qt.AlignBottom
    'alignment() -> PySide6.QtCore.Qt.Alignment\n\nSelects the corner of the viewport where the tripod is displayed (anchor position). This must be a valid `Qt.AlignmentFlag value <https://doc.qt.io/qtforpython-6/PySide6/QtCore/Qt.html#PySide6.QtCore.Qt.AlignmentFlag>`__ value as shown in the example above.\n\nDefault: ``QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignBottom``'
    axis1_color: Color = (1.0, 0.0, 0.0)
    'axis1_color() -> tuple[float, float, float]\n\nRGB display color of the first axis.\n\nDefault: ``(1.0, 0.0, 0.0)``'
    axis1_dir: Vector3 = (1.0, 0.0, 0.0)
    'axis1_dir() -> tuple[float, float, float]\n\nVector specifying direction and length of first axis, expressed in the global Cartesian coordinate system.\n\nDefault: ``(1.0, 0.0, 0.0)``'
    axis1_enabled: bool = True
    'axis1_enabled() -> bool\n\nEnables the display of the first axis.\n\nDefault: ``True``'
    axis1_label: str = 'x'
    'axis1_label() -> str\n\nText label for the first axis. Supports formatted text.\n\nDefault: ``"x"``'
    axis2_color: Color = (0.0, 0.8, 0.0)
    'axis2_color() -> tuple[float, float, float]\n\nRGB display color of the second axis.\n\nDefault: ``(0.0, 0.8, 0.0)``'
    axis2_dir: Vector3 = (0.0, 1.0, 0.0)
    'axis2_dir() -> tuple[float, float, float]\n\nVector specifying direction and length of second axis, expressed in the global Cartesian coordinate system.\n\nDefault: ``(0.0, 1.0, 0.0)``'
    axis2_enabled: bool = True
    'axis2_enabled() -> bool\n\nEnables the display of the second axis.\n\nDefault: ``True``'
    axis2_label: str = 'y'
    'axis2_label() -> str\n\nText label for the second axis. Supports formatted text.\n\nDefault: ``"y"``'
    axis3_color: Color = (0.2, 0.2, 1.0)
    'axis3_color() -> tuple[float, float, float]\n\nRGB display color of the third axis.\n\nDefault: ``(0.2, 0.2, 1.0)``'
    axis3_dir: Vector3 = (0.0, 0.0, 1.0)
    'axis3_dir() -> tuple[float, float, float]\n\nVector specifying direction and length of third axis, expressed in the global Cartesian coordinate system.\n\nDefault: ``(0.0, 0.0, 1.0)``'
    axis3_enabled: bool = True
    'axis3_enabled() -> bool\n\nEnables the display of the third axis.\n\nDefault: ``True``'
    axis3_label: str = 'z'
    'axis3_label() -> str\n\nText label for the third axis. Supports formatted text.\n\nDefault: ``"z"``'
    axis4_color: Color = (1.0, 0.0, 1.0)
    'axis4_color() -> tuple[float, float, float]\n\nRGB display color of the fourth axis.\n\nDefault: ``(1.0, 0.0, 1.0)``'
    axis4_dir: Vector3 = (0.7071, 0.7071, 0.0)
    'axis4_dir() -> tuple[float, float, float]\n\nVector specifying direction and length of fourth axis, expressed in the global Cartesian coordinate system.\n\nDefault: ``(0.7071, 0.7071, 0.0)``'
    axis4_enabled: bool = False
    'axis4_enabled() -> bool\n\nEnables the display of the fourth axis.\n\nDefault: ``False``'
    axis4_label: str = 'w'
    'axis4_label() -> str\n\nLabel for the fourth axis. Supports formatted text.\n\nDefault: ``"w"``'
    font: str = ''
    "font() -> str\n\nA string with comma-separated parameter values describing the font to be used for rendering the text labels of the viewport layer. The string must follow the specific form understood by the `QFont.fromString() <https://doc.qt.io/qtforpython-6/PySide6/QtGui/QFont.html#PySide6.QtGui.QFont.fromString>`__ method, for example ``'Arial,10,-1,5,75,0,0,0,0,0,Bold'``. \n\nNote that the font size parameter (10 in the example specification above) will be ignored by the viewport layer, because the size of text labels is already controlled by the :py:attr:`font_size` parameter."
    font_size: float = 0.4
    'font_size() -> float\n\nThe font size for rendering the text labels of the tripod. The font size is specified in terms of the tripod size.\n\nDefault: ``0.4``'
    line_width: float = 0.06
    'line_width() -> float\n\nControls the width of axis arrows. The line width is specified relative to the tripod size.\n\nDefault: ``0.06``'
    offset_x: float = 0.0
    'offset_x() -> float\n\nThis parameter allows to displace the tripod horizontally. The offset is specified as a fraction of the output image width.\n\nDefault: ``0.0``'
    offset_y: float = 0.0
    'offset_y() -> float\n\nThis parameter allows to displace the tripod vertically. The offset is specified as a fraction of the output image height.\n\nDefault: ``0.0``'
    outline_color: Color = (1.0, 1.0, 1.0)
    'outline_color() -> tuple[float, float, float]\n\nThe outline color for text labels. This is used only if :py:attr:`outline_enabled` is set.\n\nDefault: ``(1.0, 1.0, 1.0)``'
    outline_enabled: bool = False
    'outline_enabled() -> bool\n\nEnables the painting of a font outline to make the axis labels easier to read.\n\nDefault: ``False``'
    size: float = 0.075
    'size() -> float\n\nScaling factor controlling the overall size of the tripod. The size is specified as a fraction of the output image height.\n\nDefault: ``0.075``'
    style: CoordinateTripodOverlay.Style = Style.Flat
    'style() -> CoordinateTripodOverlay.Style\n\nSelects the visual style of the coordinate axis tripod.\nSupported values are:\n\n   * ``CoordinateTripodOverlay.Style.Flat`` (default) \n   * ``CoordinateTripodOverlay.Style.Solid``\n\n\n.. deprecated:: 3.9.2'
    perspective_distortion: bool = False
    'perspective_distortion() -> bool\n\nControls whether perspective distortion is applied to the tripod. If set to ``False``, the tripod will always be rendered using orthographic projection, even in a :py:class:`Viewport` using perspective projection. \n\nDefault: ``False``'

@dataclass(kw_only=True)
class PythonViewportOverlay(ViewportOverlay):
    """Base: :py:class:`ovito.vis.ViewportOverlay`

This type of viewport overlay calls a custom Python script every time an
image of the viewport is being rendered. The user-defined script can paint arbitrary graphics on top of the
three-dimensional scene.

For more information, see the class :py:class:`ViewportOverlayInterface`.

.. tip::

   Instead of using a :py:class:`PythonViewportOverlay` it is also possible to directly manipulate the
   `QImage` returned by the :py:meth:`Viewport.render_image` method before saving the image to disk.
   A :py:class:`PythonViewportOverlay` is only necessary when rendering animations or
   if you want to use the overlay interactively in the OVITO Pro desktop application."""

    class Arguments:
        """Data structure passed to legacy ``render()`` functions by the system. Modern overlay implementations, which are based on the :py:class:`ViewportOverlayInterface`, should NOT use this class. The structure provides access to the :py:attr:`painter` object, which can be used to issue drawing commands. 

.. deprecated:: 3.9.1"""

        @property
        def fov(self) -> float:
            """The field of view of the viewport’s camera. For perspective projections, this is the frustum angle in the vertical direction (in radians). For orthogonal projections this is the visible range in the vertical direction (in world units)."""
            ...

        @property
        def frame(self) -> int:
            """The animation frame number being rendered (0-based)."""
            ...

        @property
        def is_perspective(self) -> bool:
            """Flag indicating whether the viewport uses a perspective projection or parallel projection."""
            ...

        @property
        def painter(self) -> PySide6.QtGui.QPainter:
            """The `QPainter <https://doc.qt.io/qtforpython/PySide6/QtGui/QPainter.html>`__ object, which provides painting methods for drawing on top of the image canvas."""
            ...

        @property
        def proj_tm(self) -> NDArray[numpy.float64]:
            """The projection matrix. This 4x4 matrix transforms points from camera space to screen space."""
            ...

        @property
        def view_tm(self) -> NDArray[numpy.float64]:
            """The affine camera transformation matrix. This 3x4 matrix transforms points/vectors from world space to camera space."""
            ...

        @property
        def scene(self) -> ovito.Scene:
            """The current three-dimensional :py:class:`~ovito.Scene` being rendered. Provides access to all visible data pipelines."""
            ...

        @property
        def size(self) -> Tuple[int, int]:
            """A tuple containing the width and height of the viewport image being rendered (in pixels). This may be a sub-region of the output image when rendering a multi-viewport layout."""
            ...

        @property
        def viewport(self) -> Viewport:
            ...

        def project_point(self, world_xyz: Vector3) -> Optional[Tuple[float, float]]:
            """Projects a point, given in world-space coordinates, to screen space. This method can be used to determine where a 3d point would appear in the rendered image."""
            ...

        def project_size(self, world_xyz: Vector3, r: float) -> float:
            """Projects a size from 3d world space to 2d screen space. This method can be used to determine how large a 3d object, for example a sphere with the given radius *r*, would appear in the rendered image."""
            ...
    function: Callable[[PythonViewportOverlay.Arguments], Optional[Generator[str | float, None, None]]] | None = None
    'function() -> Optional[collections.abc.Callable]\n\nA reference to the Python function to be called every time the viewport is repainted or when an output image is rendered.\n\nThe user-defined function must accept exactly one argument as shown in the example above. The system will pass an :py:class:`.Arguments` object to the function, providing various contextual information on the current frame being rendered. \n\nDefault: ``None``\n\n\n.. deprecated:: 3.9.1'
    delegate: Optional[ViewportOverlayInterface] = None
    'delegate() -> Optional[ViewportOverlayInterface]\n\nA :py:class:`ViewportOverlayInterface` object implementing the logic of the user-defined viewport overlay. \n\nDefault: ``None``'
    pipeline: Optional[ovito.pipeline.Pipeline] = None
    "pipeline() -> ovito.pipeline.Pipeline\n\nThe :py:class:`Pipeline`, which gets automatically evaluated by the system to produce the :py:class:`DataCollection` being passed to the :py:meth:`ViewportOverlayInterface.render` method during rendering. \n\nWhen you first insert the :py:class:`PythonViewportOverlay` into a viewport's :py:attr:`~Viewport.overlays` or :py:attr:`~Viewport.underlays` lists, the system automatically sets this field to the first data pipeline found in the current visualization :py:class:`~ovito.Scene`. \n\nIf your visualization scene contains multiple data pipelines, you should set this field explicitly to select the pipeline whose output data is to used by your overlay."

@dataclass(kw_only=True)
class TextLabelOverlay(ViewportOverlay):
    """Base: :py:class:`ovito.vis.ViewportOverlay`

Displays a text label in a viewport and in rendered images. You can attach an instance of this class to a viewport by adding it to the viewport's :py:attr:`overlays` collection:

```python
  from ovito.vis import TextLabelOverlay, Viewport
  from ovito.qt_compat import QtCore
  
  # Create the overlay:
  overlay = TextLabelOverlay(
      text = 'Some text',
      alignment = QtCore.Qt.AlignmentFlag.AlignHCenter | QtCore.Qt.AlignmentFlag.AlignBottom,
      offset_y = 0.1,
      font_size = 0.03,
      text_color = (0,0,0))
  
  # Attach the overlay to a newly created viewport:
  viewport = Viewport(type = Viewport.Type.Top)
  viewport.overlays.append(overlay)
```

Text labels can display dynamically computed values. See the :py:attr:`text` property for an example."""
    alignment: PySide6.QtCore.Qt.Alignment = PySide6.QtCore.Qt.AlignLeft ^ PySide6.QtCore.Qt.AlignTop
    'alignment() -> PySide6.QtCore.Qt.Alignment\n\nSelects the corner of the viewport where the text is displayed (anchor position). This must be a valid `Qt.AlignmentFlag value <https://doc.qt.io/qtforpython-6/PySide6/QtCore/Qt.html#PySide6.QtCore.Qt.AlignmentFlag>`__ as shown in the example above. \n\nDefault: ``QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignTop``'
    font: str = ''
    "font() -> str\n\nA string with comma-separated parameter values describing the font to be used for rendering the text labels of the viewport layer. The string must follow the specific form understood by the `QFont.fromString() <https://doc.qt.io/qtforpython-6/PySide6/QtGui/QFont.html#PySide6.QtGui.QFont.fromString>`__ method, for example ``'Arial,10,-1,5,75,0,0,0,0,0,Bold'``. \n\nNote that the font size parameter (10 in the example specification above) will be ignored by the viewport layer, because the size of text labels is already controlled by the :py:attr:`font_size` parameter."
    font_size: float = 0.02
    'font_size() -> float\n\nThe font size, which is specified as a fraction of the output image height.\n\nDefault: ``0.02``'
    format_string: str = '%.6g'
    "format_string() -> str\n\nThe format string used with the `sprintf() <https://en.cppreference.com/w/cpp/io/c/fprintf>`__ function to generate the text representation of global attributes (only floating-point values). You can change this format string to control the number of decimal places shown and switch between exponential and regular notation, for example. \n\nDefault: ``'%.6g'``"
    offset_x: float = 0.0
    'offset_x() -> float\n\nThis parameter allows to displace the label horizontally from its anchor position. The offset is specified as a fraction of the output image width.\n\nDefault: ``0.0``'
    offset_y: float = 0.0
    'offset_y() -> float\n\nThis parameter allows to displace the label vertically from its anchor position. The offset is specified as a fraction of the output image height.\n\nDefault: ``0.0``'
    outline_color: Color = (1.0, 1.0, 1.0)
    'outline_color() -> tuple[float, float, float]\n\nThe text outline color. This is used only if :py:attr:`outline_enabled` is set.\n\nDefault: ``(1.0, 1.0, 1.0)``'
    outline_enabled: bool = False
    'outline_enabled() -> bool\n\nEnables the painting of a font outline to make the text easier to read.\n\nDefault: ``False``'
    pipeline: Optional[ovito.pipeline.Pipeline] = None
    'pipeline() -> Optional[ovito.pipeline.Pipeline]\n\nThe :py:class:`Pipeline` to be queried to obtain the attributes referenced in the text string. See the :py:attr:`text` property for more information.'
    text: str = 'Text label'
    'text() -> str\n\nThe text string to be rendered.\n\nThe string can contain placeholder references to dynamically computed attributes of the form ``[attribute]``, which will be replaced by their actual value before rendering the text label. Attributes are taken from the pipeline output of the :py:class:`Pipeline` assigned to the overlay\'s :py:attr:`pipeline` property. \n\nThe following example demonstrates how to insert a text label that displays the number of currently selected particles: \n\n```python\n  from ovito.io import import_file\n  from ovito.vis import TextLabelOverlay, Viewport\n  from ovito.modifiers import ExpressionSelectionModifier\n  \n  # Import a simulation dataset and select some atoms based on their potential energy:\n  pipeline = import_file("input/simulation.dump")\n  pipeline.add_to_scene()\n  pipeline.modifiers.append(ExpressionSelectionModifier(expression="peatom > -4.2"))\n  \n  # Create the overlay. Note that the text string contains a reference\n  # to an output attribute of the ExpressionSelectionModifier.\n  overlay = TextLabelOverlay(text="Number of selected atoms: [ExpressionSelection.count]")\n  # Specify the source of dynamically computed attributes.\n  overlay.pipeline = pipeline\n  \n  # Attach overlay to a newly created viewport:\n  viewport = Viewport(type=Viewport.Type.Top)\n  viewport.overlays.append(overlay)\n```\n\n.. tip::\n\n  You can embed HTML and CSS markup elements in the string to further control the formatting and styling of the text.\n\nDefault: ``"Text label"``'
    text_color: Color = (0.0, 0.0, 0.5)
    'text_color() -> tuple[float, float, float]\n\nThe text rendering color.\n\nDefault: ``(0.0, 0.0, 0.5)``'

@dataclass(kw_only=True)
class DataVis:
    """Abstract base class for visualization elements that are responsible for the visual appearance of data objects in the visualization. Some `DataObjects` are associated with a corresponding :py:class:`DataVis` element (see `DataObject.vis` property), making them *visual* data objects that appear in the viewports and in rendered images. 

See the :py:mod:`ovito.vis` module for the list of visual element types available in OVITO."""
    enabled: bool = True
    'enabled() -> bool\n\nBoolean flag controlling the visibility of the data. If set to ``False``, the data will not be visible in the viewports or in rendered images.\n\nDefault: ``True``'
    title: str = ''
    "title() -> str\n\nA custom title string assigned to the visual element, which will show in the pipeline editor of OVITO. \n\nDefault: ``''``"

@dataclass(kw_only=True)
class SimulationCellVis(DataVis):
    """Base: :py:class:`ovito.vis.DataVis`

Controls the visual appearance of the simulation cell. 
An instance of this class is attached to the :py:class:`SimulationCell` object 
and can be accessed through its :py:attr:`vis` field. 
See also the corresponding user manual page for this visual element. 

The following example script demonstrates how to change the display line width and rendering color of the simulation cell 
loaded from an input simulation file:

```python
  from ovito.io import import_file
  
  pipeline = import_file("input/simulation.dump")
  pipeline.add_to_scene()
  
  cell_vis = pipeline.source.data.cell.vis
  cell_vis.line_width = 1.3
  cell_vis.rendering_color = (0.0, 0.0, 0.8)
```"""
    line_width: float = 0.0
    'line_width() -> float\n\nThe width of the simulation cell line (in simulation units of length).\n\nDefault: 0.14% of the simulation box diameter'
    render_cell: bool = True
    "render_cell() -> bool\n\nBoolean flag controlling the cell's visibility in rendered images. If ``False``, the cell will only be visible in the interactive viewports. \n\nDefault: ``True``"
    rendering_color: Color = (0.0, 0.0, 0.0)
    'rendering_color() -> tuple[float, float, float]\n\nThe RGB line color used when rendering the cell.\n\nDefault: ``(0.0, 0.0, 0.0)``'

@dataclass(kw_only=True)
class ParticlesVis(DataVis):
    """Base: :py:class:`ovito.vis.DataVis`

This type of visual element is responsible for rendering particles and is attached to every :py:class:`Particles` data object. 
You can access the element through the :py:attr:`vis` field of the data object and adjust its parameters to control the visual
appearance of particles in rendered images:

```python
  from ovito.io import import_file
  from ovito.vis import ParticlesVis
  
  pipeline = import_file("input/simulation.dump")
  pipeline.add_to_scene()
  
  vis_element = pipeline.compute().particles.vis
  vis_element.shape = ParticlesVis.Shape.Square
```

See also the corresponding user manual page for more information on this visual element."""

    class Shape(enum.Enum):
        """"""
        Unspecified = enum.auto()
        Sphere = enum.auto()
        Box = enum.auto()
        Circle = enum.auto()
        Square = enum.auto()
        Cylinder = enum.auto()
        Spherocylinder = enum.auto()
        Mesh = enum.auto()
    radius: float = 1.2
    'radius() -> float\n\nThe standard display radius of particles. This value is only used if no per-particle or per-type radii have been set. A per-type radius can be set via `ParticleType.radius`. An individual display radius can be assigned to each particle by setting the ``Radius`` particle property, e.g. using the :py:class:`ComputePropertyModifier`. \n\nDefault: ``1.2``'
    scaling: float = 1.0
    'scaling() -> float\n\nGlobal scaling factor that is applied to every particle being rendered. \n\nDefault: ``1.0``'
    shape: ParticlesVis.Shape = Shape.Sphere
    'shape() -> ParticlesVis.Shape\n\nThe kind of shape to use when rendering the particles. Supported modes are:\n\n   * ``ParticlesVis.Shape.Sphere`` (default) \n   * ``ParticlesVis.Shape.Box``\n   * ``ParticlesVis.Shape.Circle``\n   * ``ParticlesVis.Shape.Square``\n   * ``ParticlesVis.Shape.Cylinder``\n   * ``ParticlesVis.Shape.Spherocylinder``\n\n\nMode ``Sphere`` includes ellipsoid and superquadric particle geometries, which are activated by the presence of the ``Aspherical Shape`` and ``Superquadric Roundness`` particle properties. Mode ``Box`` renders cubic as well as non-cubic boxes depending on the presence of the ``Aspherical Shape`` particle property. \n\nNote that this parameter controls the standard shape to be used for all particles. You can override this default setting on a per-particle type basis by setting the `ParticleType.shape` property to a different value.'

@dataclass(kw_only=True)
class BondsVis(DataVis):
    """Base: :py:class:`ovito.vis.DataVis`

A visualization element that renders cylindrical bonds between particles. 
An instance of this class is attached to every :py:class:`Bonds` data object 
and controls the visual appearance of the bonds in rendered images. 

See also the corresponding user manual page for this visual element. 
If you import a simulation file containing bonds, you can subsequently access the :py:class:`BondsVis` element 
through the :py:attr:`vis` field of the bonds data object, which is part in the data collection managed 
by the pipeline's :py:attr:`source` object:

```python
  pipeline = import_file('input/bonds.data.gz', atom_style='bond')
  pipeline.add_to_scene()
  bonds_vis = pipeline.source.data.particles.bonds.vis
  bonds_vis.width = 0.4
```

In cases where the :py:class:`Bonds` data is dynamically generated by a modifier, e.g. the :py:class:`CreateBondsModifier`, 
the :py:class:`BondsVis` element is managed by the modifier:

```python
  modifier = CreateBondsModifier(cutoff = 2.8)
  modifier.vis.flat_shading = True
  pipeline.modifiers.append(modifier)
```"""

    class ColoringMode(enum.Enum):
        """"""
        Uniform = enum.auto()
        ByBondType = enum.auto()
        ByParticle = enum.auto()
    color: Color = (0.6, 0.6, 0.6)
    'color() -> tuple[float, float, float]\n\nThe uniform color of bonds. This parameter is only used if :py:attr:`coloring_mode` is set to ``Uniform`` and if the bonds do not possess a bond property named ``Color``, i.e., explicit per-bond colors were not provided. \n\nDefault: ``(0.6, 0.6, 0.6)``'
    coloring_mode: BondsVis.ColoringMode = ColoringMode.ByParticle
    "coloring_mode() -> BondsVis.ColoringMode\n\nSelects how the color of each bond is determined. Available modes:\n\n  * ``BondsVis.ColoringMode.Uniform``: Use the specified :py:attr:`color` value to render all bonds.\n  * ``BondsVis.ColoringMode.ByBondType``: Use each bond type's :py:attr:`color` to render the bonds.\n  * ``BondsVis.ColoringMode.ByParticle``: Adopt the colors of the particles connect by the bonds.\n\n\n  If the :py:class:`Bonds` object being rendered contains the ``Color`` property, then the visual element will directly use these explicit per-bond RGB values   for rendering the bonds. The :py:attr:`coloring_mode` parameter is ignored in this case. \n\nDefault: ``BondsVis.ColoringMode.ByParticle``"
    flat_shading: bool = False
    'flat_shading() -> bool\n\nBoolean flag that activates a flat-shaded representation of the bonds instead of the normal cylinder representation. \n\nDefault: ``False``'
    width: float = 0.4
    'width() -> float\n\nThe display width of bonds (in natural length units).\n\nDefault: ``0.4``'

@dataclass(kw_only=True)
class DislocationVis(DataVis):
    """Base: :py:class:`ovito.vis.DataVis`

Controls the visual appearance of dislocation lines extracted by a :py:class:`DislocationAnalysisModifier`. An instance of this class is attached to every :py:class:`DislocationNetwork` data object. 

See also the corresponding user manual page for more information on this visual element."""

    class ColoringMode(enum.Enum):
        """"""
        ByDislocationType = enum.auto()
        ByBurgersVector = enum.auto()
        ByCharacter = enum.auto()

    class Shading(enum.Enum):
        """A simple attribute-based namespace.

SimpleNamespace(**kwargs)"""
        Normal = enum.auto()
        Flat = enum.auto()
    burgers_vector_color: Color = (0.7, 0.7, 0.7)
    'burgers_vector_color() -> tuple[float, float, float]\n\nThe color of Burgers vector arrows.\n\nDefault: ``(0.7, 0.7, 0.7)``'
    burgers_vector_scaling: float = 1.0
    'burgers_vector_scaling() -> float\n\nThe scaling factor applied to displayed Burgers vectors. This can be used to exaggerate the arrow size.\n\nDefault: ``1.0``'
    burgers_vector_width: float = 0.6
    'burgers_vector_width() -> float\n\nSpecifies the width of Burgers vector arrows (in length units).\n\nDefault: ``0.6``'
    coloring_mode: DislocationVis.ColoringMode = ColoringMode.ByDislocationType
    'coloring_mode() -> DislocationVis.ColoringMode\n\nSelects the coloring mode for dislocation lines. Supported modes are:\n\n   * ``DislocationVis.ColoringMode.ByDislocationType`` (default) \n   * ``DislocationVis.ColoringMode.ByBurgersVector``\n   * ``DislocationVis.ColoringMode.ByCharacter``'
    line_width: float = 1.0
    'line_width() -> float\n\nControls the display width (in units of length of the simulation) of dislocation lines.\n\nDefault: ``1.0``'
    shading: DislocationVis.Shading = Shading.Normal
    'shading() -> DislocationVis.Shading\n\nThe shading style used for the lines.\nPossible values:\n\n   * ``DislocationVis.Shading.Normal`` (default) \n   * ``DislocationVis.Shading.Flat``'
    show_burgers_vectors: bool = False
    'show_burgers_vectors() -> bool\n\nBoolean flag that enables the display of Burgers vector arrows.\n\nDefault: ``False``'
    show_line_directions: bool = False
    'show_line_directions() -> bool\n\nBoolean flag that enables the visualization of line directions.\n\nDefault: ``False``'

@dataclass(kw_only=True)
class SurfaceMeshVis(DataVis):
    """Base: :py:class:`ovito.vis.DataVis`

Controls the visual appearance of a :py:class:`SurfaceMesh` object, which is typically generated by modifiers such as 
:py:class:`ConstructSurfaceModifier` or :py:class:`CreateIsosurfaceModifier`. 
See also the corresponding user manual page for more information on this visual element."""

    class ColorMappingMode(enum.Enum):
        """"""
        Uniform = enum.auto()
        Vertex = enum.auto()
        Face = enum.auto()
        Region = enum.auto()
    cap_color: Color = (0.8, 0.8, 1.0)
    'cap_color() -> tuple[float, float, float]\n\nThe RGB display color of the cap polygons at periodic boundaries.\n\nDefault: ``(0.8, 0.8, 1.0)``'
    cap_transparency: float = 0.0
    'cap_transparency() -> float\n\nThe degree of transparency of the cap polygons shown at periodic cell boundaries. The valid range is 0.0 -- 1.0  (fully opaque to fully transparent).\n\nDefault: ``0.0``'
    clip_at_domain_boundaries: bool = False
    'clip_at_domain_boundaries() -> bool\n\nControls whether the mesh gets clipped at *non-periodic* cell boundaries during visualization. This option plays a role only if the mesh extends beyond the boundaries of the finite :py:attr:`domain` of the :py:class:`SurfaceMesh`; it does *not* apply to intersections of the surface with *periodic* boundaries of the simulation domain (see :py:attr:`pbc`), at which the surface mesh always gets wrapped back into primary cell image for visualization. \n\nIf the mesh extends beyond the (non-periodic) domain boundaries, you can use this option to restrict the display of the mesh to those parts that are located inside the domain. \n\n.. figure:: ../introduction/graphics/surface_mesh_vis_clipping_off.png\n  :figwidth: 20%\n  :align: left\n\n  Clipping off\n\n.. figure:: ../introduction/graphics/surface_mesh_vis_clipping_on.png\n  :figwidth: 20%\n  :align: left\n\n  Clipping on\n\nDefault: ``False``'
    color_mapping_gradient: ovito.modifiers.ColorCodingModifier.Gradient = ovito.modifiers.ColorCodingModifier.Rainbow()
    'color_mapping_gradient() -> ovito.modifiers.ColorCodingModifier.Gradient\n\nThe color gradient for mapping scalar property values taken from the selected :py:attr:`color_mapping_property` to corresponding RGB color values (*color transfer function*). See the `ColorCodingModifier.gradient` parameter for a list of available color gradient types. \n\nDefault: ``ColorCodingModifier.Rainbow()``'
    color_mapping_interval: Tuple[float, float] = (0.0, 0.0)
    'color_mapping_interval() -> tuple[float, float]\n\nSpecifies the range of input values from the selected :py:attr:`color_mapping_property` getting mapped to corresponding RGB values by the selected :py:attr:`color_mapping_gradient`. The tuple defines the start and end of the linear interval that is translated to pseudo-colors by the color map. Input property values not within of the interval get mapped to the marginal colors of the selected color map. \n\nDefault: ``(0.0, 0.0)``'
    color_mapping_mode: SurfaceMeshVis.ColorMappingMode = ColorMappingMode.Uniform
    "color_mapping_mode() -> SurfaceMeshVis.ColorMappingMode\n\nControls how the color of the surface is computed. Using pseudo-coloring you can visualize a local property of the surface. \n\nAvailable modes:\n\n``SurfaceMeshVis.ColorMappingMode.Uniform``: \n   Uses :py:attr:`surface_color` for rendering the entire surface with a constant color (disables local pseudo-coloring).\n``SurfaceMeshVis.ColorMappingMode.Vertex``: \n   Colors the surface based on a local property associated with the surface's :py:attr:`vertices`.\n``SurfaceMeshVis.ColorMappingMode.Face``: \n   Colors the surface based on a local property associated with the surface's :py:attr:`faces`.\n``SurfaceMeshVis.ColorMappingMode.Region``: \n   Colors the surface based on a local property associated with the surface's :py:attr:`regions`.\n\n\nDefault: ``SurfaceMeshVis.ColorMappingMode.Uniform``\n\n\n  This setting has no effect if the :py:attr:`vertices`, :py:attr:`faces` or :py:attr:`regions` of the :py:class:`SurfaceMesh` have   explicit colors associated with them, i.e., if the ``Color`` property exists in one of these property containers."
    color_mapping_property: str = ''
    "color_mapping_property() -> str\n\nThe name of the property to be used for coloring the mesh to visualize the local values of this property on the surface. If the :py:class:`Property` has several components, then the name must be followed by a component name, e.g. ``'Orientation.X'``. Whether the property is taken from the :py:attr:`vertices`, :py:attr:`faces`, or :py:attr:`regions` of the :py:class:`SurfaceMesh` being rendered is determined by the selected :py:attr:`color_mapping_mode`. \n\nNumeric values from the source property are mapped to corresponding RGB-based pseudo-colors by first normalizing them according to the specified :py:attr:`color_mapping_interval` and then applying the selected :py:attr:`color_mapping_gradient`. \n\nNote that, if the ``Color`` property is defined on the surface's :py:attr:`vertices`, :py:attr:`faces`, or :py:attr:`regions`, then the visual element directly uses these explicit RGB values to render the surface. No color mapping takes place in this case and the :py:attr:`color_mapping_property`, :py:attr:`color_mapping_mode` and :py:attr:`surface_color` parameters are all ignored. \n\nDefault: ``''``"
    highlight_edges: bool = False
    'highlight_edges() -> bool\n\nActivates the highlighted rendering of the polygonal edges of the mesh.\n\nDefault: ``False``'
    reverse_orientation: bool = False
    'reverse_orientation() -> bool\n\nFlips the orientation of the surface. This affects the generation of cap polygons as well.\n\nDefault: ``False``'
    show_cap: bool = True
    'show_cap() -> bool\n\nControls the visibility of cap polygons, which are created at the intersection of the surface mesh with the `domain` boundaries. This option has an effect only if the surface mesh being rendered is *closed*, which means there are well-defined "interior" and "exterior" regions of space separated by the surface manifold. \n\nDefault: ``True``\n\n\n.. seealso:: `SurfaceMeshTopology.is_closed`'
    smooth_shading: bool = True
    'smooth_shading() -> bool\n\nEnables smooth shading of the triangulated surface mesh.\n\nDefault: ``True``'
    surface_color: Color = (1.0, 1.0, 1.0)
    'surface_color() -> tuple[float, float, float]\n\nThe RGB display color of the surface mesh. Used only if :py:attr:`color_mapping_mode` is set to uniform coloring. \n\nDefault: ``(1.0, 1.0, 1.0)``'
    surface_transparency: float = 0.0
    'surface_transparency() -> float\n\nThe degree of transparency of the displayed surface. The valid range is 0.0 -- 1.0 (fully opaque to fully transparent).\n\nDefault: ``0.0``'

@dataclass(kw_only=True)
class LinesVis(DataVis):
    """Base: :py:class:`ovito.vis.DataVis`

Controls the visual appearance of a :py:class:`Lines` data object. Every :py:class:`Lines`
instance is associated with a :py:class:`LinesVis` instance, which can be accessed through the data object's
:py:attr:`ovito.data.DataObject.vis` field.

For a :py:class:`Lines` data object that is created by the :py:class:`GenerateTrajectoryLinesModifier`,
the visual element is managed by the modifier and can be accessed as `GenerateTrajectoryLinesModifier.vis`."""

    class Shading(enum.Enum):
        """"""
        Normal = enum.auto()
        Flat = enum.auto()
    color: Color = (0.6, 0.6, 0.6)
    'color() -> tuple[float, float, float]\n\nThe uniform color to be used for rendering the lines. This parameter is ignored if pseudo-coloring of the lines has been activated by setting a :py:attr:`color_mapping_property`. \n\nDefault: ``(0.6, 0.6, 0.6)``'
    color_mapping_gradient: ovito.modifiers.ColorCodingModifier.Gradient = ovito.modifiers.ColorCodingModifier.Rainbow()
    'color_mapping_gradient() -> ovito.modifiers.ColorCodingModifier.Gradient\n\nThe color gradient used to map scalar property values from the selected :py:attr:`color_mapping_property` to corresponding RGB output values (also called *color transfer function*). See the `ColorCodingModifier.gradient` parameter for a list of available color gradient types. \n\nDefault: ``ColorCodingModifier.Rainbow()``'
    color_mapping_interval: Tuple[float, float] = (0.0, 0.0)
    'color_mapping_interval() -> tuple[float, float]\n\nSpecifies the range of input values from the selected :py:attr:`color_mapping_property` getting mapped to corresponding RGB values by the selected :py:attr:`color_mapping_gradient`. The tuple defines the start and end of the linear interval that is translated to pseudo-colors by the color map. Input property values not within of the interval get mapped to the marginal colors of the selected color map. \n\nDefault: ``(0.0, 0.0)``'
    color_mapping_property: str = ''
    "color_mapping_property() -> str\n\nThe name of the :py:class:`Lines` property to be used for pseudo-coloring the lines according to the scalar values of this property. If the :py:class:`Property` consists of several vector components, then the name must be followed by a specific component name, e.g. ``'Velocity.Z'``. \n\nTypically, this parameter should be set to the name of the particle property which was sampled during line tracing by the :py:class:`GenerateTrajectoryLinesModifier`. See its :py:attr:`sample_particle_property` parameter for an example. \n\nNumeric values from the selected source property are mapped to corresponding RGB values by first normalizing them according to the specified :py:attr:`color_mapping_interval` and then applying the selected :py:attr:`color_mapping_gradient`. \n\n  If the :py:class:`Lines` object being rendered has the standard property ``Color``, then this explicit per-vertex color information   is used. No pseudo-color mapping takes place in this case, and the :py:attr:`color_mapping_property` and :py:attr:`color` parameters of the visual element are ignored. \n\nDefault: ``''``"
    shading: LinesVis.Shading = Shading.Flat
    'shading() -> LinesVis.Shading\n\nThe shading style used for lines. Possible values:\n\n   * ``LinesVis.Shading.Normal`` \n   * ``LinesVis.Shading.Flat`` (default)'
    rounded_caps: bool = False
    'rounded_caps() -> bool\n\nIf ``True``, lines are rendered with a rounded cap at each end. Otherwise, lines are terminated by a flat face.\n\nDefault: ``False``'
    upto_current_time: bool = False
    'upto_current_time() -> bool\n\nIf ``True``, trajectory lines are only rendered up to the particle positions at the current animation time. Otherwise, the complete trajectory lines are displayed.This has no effect for non-trajectory lines.\n\nDefault: ``False``'
    width: float = 0.2
    'width() -> float\n\nThe display width of lines.\n\nDefault: ``0.2``'
    wrapped_lines: bool = False
    'wrapped_lines() -> bool\n\nIf ``True``, the continuous lines will automatically be wrapped back into the simulation box during rendering. Thus, they will be shown as several discontinuous segments if they cross periodic boundaries of the simulation box. \n\nDefault: ``False``'

@dataclass(kw_only=True)
class TriangleMeshVis(DataVis):
    """Base: :py:class:`ovito.vis.DataVis`

Controls the visual appearance of a :py:class:`TriangleMesh`. 
See also the corresponding user manual page for more information on this visual element."""
    backface_culling: bool = False
    'backface_culling() -> bool\n\nControls whether triangle faces facing away from the viewer are not rendered. \n\nDefault: ``False``'
    color: Color = (0.85, 0.85, 1.0)
    "color() -> tuple[float, float, float]\n\nThe uniform RGB color of the triangle mesh, which is used for rendering if the mesh's faces or vertices have no local colors associated with them. RGB components must be in the range 0--1.\n\nDefault: ``(0.85, 0.85, 1.0)``"
    highlight_edges: bool = False
    'highlight_edges() -> bool\n\nHighlights the polygonal edges of the mesh by rendering a wireframe lines along those edges that have been marked as visible.\n\nDefault: ``False``'
    transparency: float = 0.0
    'transparency() -> float\n\nThe degree of semi-transparency of the rendered mesh. Valid parameter range is 0.0 -- 1.0.\n\nDefault: ``0.0``'

@dataclass(kw_only=True)
class VectorVis(DataVis):
    """Base: :py:class:`ovito.vis.DataVis`

This kind of visual element renders arrow glyphs for visualizing vectorial data stored in a :py:class:`Property` object. 
See also the corresponding user manual page for more information.

A vector property is any :py:class:`Property` array with data type ``float`` and three components per element. The :py:class:`VectorVis` element supports visualization of 
vector properties that are stored of the following :py:class:`PropertyContainer` types: :py:class:`Particles`, :py:class:`Bonds`,
`SurfaceMesh.vertices`, `SurfaceMesh.faces`, and :py:class:`VoxelGrid`.

The standard particle properties ``Force``, ``Displacement``, ``Dipole``, and ``Velocity`` already have an existing :py:class:`VectorVis` element
attached to them, which is disabled by default. You must `enable`  it for the arrow glyphs to be displayed, e.g.:

```python
  pipeline = import_file('input/simulation.dump')
  pipeline.add_to_scene()
  vector_vis = pipeline.compute().particles.forces.vis
  vector_vis.enabled = True  # This activates the display of arrow glyphs
  vector_vis.color = (1,0,0)
```

In this example, the atomistic :py:attr:`forces` were loaded as particle property named ``Force`` from the imported simulation file, 
Parameters such as :py:attr:`color`, :py:attr:`width`, and :py:attr:`flat_shading` of the :py:class:`VectorVis` element control the visual appearance of the arrow glyphs in rendered images. 

Some modifiers in OVITO dynamically add new vector properties to particles. For instance, the :py:class:`CalculateDisplacementsModifier` 
creates the ``Displacement`` property and automatically attaches a :py:class:`VectorVis` element to it in case you want to visualize the displacements. 
The visual element is part of the modifier in this case: 

```python
  modifier = CalculateDisplacementsModifier()
  pipeline.modifiers.append(modifier)
  modifier.vis.enabled = True  # This activates the display of displacement vectors
  modifier.vis.flat_shading = False
```

If you are writing your own modifier function to compute a vector property, and you want to visualize that property 
using arrow glyphs, you need to construct a :py:class:`VectorVis` element and attach it to the newly created :py:class:`Property` object. For example: 

```python
  def modify(frame, data, vector_vis=VectorVis(alignment=VectorVis.Alignment.Center, color=(1.0, 0.0, 0.4))):
  
      # Add a new vector property to the particles:
      vector_data = numpy.random.random_sample(size=(data.particles.count, 3))
      property = data.particles_.create_property('My Vector Property', data=vector_data)
  
      # Attach the visual element to the output property:
      property.vis = vector_vis  
```

Setting up the visual element as an additional parameter of the ``modify()`` function provides two advantages: 
Only a single instance is created, which survives multiple invocations of the modifier function, and OVITO Pro displays the element's 
parameter panel in the UI."""

    class Alignment(enum.Enum):
        """"""
        Base = enum.auto()
        Center = enum.auto()
        Head = enum.auto()
    alignment: VectorVis.Alignment = Alignment.Base
    'alignment() -> VectorVis.Alignment\n\nControls the positioning of the arrows glyphs with respect to the base points, e.g., the particle positions.\nPossible values:\n\n   * ``VectorVis.Alignment.Base`` (default) \n   * ``VectorVis.Alignment.Center``\n   * ``VectorVis.Alignment.Head``'
    color: Color = (1.0, 1.0, 0.0)
    'color() -> tuple[float, float, float]\n\nThe uniform display color of arrow glyphs. This parameter is *not* used if pseudo-color mapping is enabled through the :py:attr:`color_mapping_property` option or when the ``Vector Color`` property was set for the particles. \n\nDefault: ``(1.0, 1.0, 0.0)``'
    color_mapping_gradient: ovito.modifiers.ColorCodingModifier.Gradient = ovito.modifiers.ColorCodingModifier.Rainbow()
    'color_mapping_gradient() -> ovito.modifiers.ColorCodingModifier.Gradient\n\nThe color gradient used to map scalar property values from the selected :py:attr:`color_mapping_property` to corresponding RGB output values (*color transfer function*). See the `ColorCodingModifier.gradient` parameter for a list of available color gradient types. \n\nDefault: ``ColorCodingModifier.Rainbow()``'
    color_mapping_interval: Tuple[float, float] = (0.0, 0.0)
    'color_mapping_interval() -> tuple[float, float]\n\nSpecifies the range of input values from the selected :py:attr:`color_mapping_property` getting mapped to corresponding RGB values by the selected :py:attr:`color_mapping_gradient`. The tuple defines the start and end of the linear interval that is translated to pseudo-colors by the color map. Input property values not within of the interval get mapped to the marginal colors of the selected color map. \n\nDefault: ``(0.0, 0.0)``'
    color_mapping_property: str = ''
    "color_mapping_property() -> str\n\nThe name of a scalar property to be used for coloring the vector glyphs. If the :py:class:`Property` has several components, then the name must be followed by a component name, e.g. ``'Displacement.Z'``. \n\nNumeric values from the selected source property are mapped to corresponding RGB values by first normalizing them according to the specified :py:attr:`color_mapping_interval` and then applying the selected :py:attr:`color_mapping_gradient`. \n\nNote that, if a :py:class:`Particles` object is being rendered that has a property named ``Vector Color``, then these explicit per-particle colors will be used for rendering the vector glyphs. No color mapping takes place in this case and the :py:attr:`color_mapping_property` and :py:attr:`color` parameters of the visual element are ignored. \n\nDefault: ``''``"
    flat_shading: bool = True
    'flat_shading() -> bool\n\nSwitches between a flat rendering style for the arrows and a three-dimensional representation. \n\nDefault: ``True``'
    offset: Vector3 = (0.0, 0.0, 0.0)
    'offset() -> tuple[float, float, float]\n\nAdditional three-dimensional offset vector by which all arrows are displaced with respect to they base points. This can be used to move the arrows in front of or behind the particles and avoid undesirable occlusions. \n\nDefault: ``(0.0, 0.0, 0.0)``'
    reverse: bool = False
    'reverse() -> bool\n\nBoolean flag which reverses the direction the arrow glyphs.\n\nDefault: ``False``'
    scaling: float = 1.0
    'scaling() -> float\n\nThe uniform scaling factor applied to arrow glyphs. \n\nDefault: ``1.0``'
    transparency: float = 0.0
    'transparency() -> float\n\nThe degree of semi-transparency for rendering the arrows. The valid parameter range is 0.0 -- 1.0 (fully opaque to fully transparent).This parameter is ignored when the ``Vector Transparency`` property is set for the particles to specify explicit per-particle vectortransparency values. \n\nDefault: ``0.0``'
    width: float = 0.5
    'width() -> float\n\nControls the width of arrows (in simulation units of length).\n\nDefault: ``0.5``'

@dataclass(kw_only=True)
class VoxelGridVis(DataVis):
    """Base: :py:class:`ovito.vis.DataVis`

This visual element controls the appearance of a :py:class:`VoxelGrid` data object, which is typically generated by the 
:py:class:`SpatialBinningModifier` or imported directly from files containing volumetric data. The visual element is responsible for rendering 
the outer boundaries of the grid, i.e., showing only the voxel cells at the surface but not in the interior of the grid volume.

See also the corresponding user manual page for further information on this visual element."""
    color_mapping_gradient: ovito.modifiers.ColorCodingModifier.Gradient = ovito.modifiers.ColorCodingModifier.Rainbow()
    'color_mapping_gradient() -> ovito.modifiers.ColorCodingModifier.Gradient\n\nThe color gradient used to map scalar property values from the selected :py:attr:`color_mapping_property` to corresponding RGB output values (also called *color transfer function*). See the `ColorCodingModifier.gradient` parameter for a list of available color gradient types. \n\nDefault: ``ColorCodingModifier.Rainbow()``'
    color_mapping_interval: Tuple[float, float] = (0.0, 0.0)
    'color_mapping_interval() -> tuple[float, float]\n\nSpecifies the range of input values from the selected :py:attr:`color_mapping_property` getting mapped to corresponding RGB values by the selected :py:attr:`color_mapping_gradient`. The tuple defines the start and end of the linear interval that is translated to pseudo-colors by the color map. Input property values not within of the interval get mapped to the marginal colors of the selected color map. \n\nDefault: ``(0.0, 0.0)``'
    color_mapping_property: str = ''
    "color_mapping_property() -> str\n\nThe name of the :py:class:`VoxelGrid` scalar property to be used for coloring the grid cells. If the :py:class:`Property` has several components, then the name must be followed by a component name, e.g. ``'Velocity.Z'``. \n\nNumeric values from the selected source property are mapped to corresponding RGB cell colors by first normalizing them according to the specified :py:attr:`color_mapping_interval` and then applying the selected :py:attr:`color_mapping_gradient`. \n\nNote that, if the :py:class:`VoxelGrid` being rendered contains the ``Color`` property, then the visual element directly uses these RGB values to render the grid cells. No color mapping takes place in this case and the :py:attr:`color_mapping_property` parameter is ignored. \n\nDefault: ``''``"
    highlight_grid_lines: bool = True
    'highlight_grid_lines() -> bool\n\nControls the rendering of grid lines separating the voxel cells.\n\nDefault: ``True``'
    interpolate_colors: bool = False
    'interpolate_colors() -> bool\n\nControls whether the (pseudo)colors of the voxel cells visible on the boundary of the grid are smoothly interpolated between neighboring cells. \n\nDefault: ``False``'
    transparency: float = 0.0
    'transparency() -> float\n\nThe degree of transparency of the displayed grid surface. The valid parameter range is 0.0 -- 1.0 (fully opaque to fully transparent).\n\nDefault: ``0.0``'

@dataclass(kw_only=True)
class JupyterViewportWidget(ipywidgets.DOMWidget):
    antialiasing: bool = True
    picking: bool = False
    vr_scale: float = 0.0

    def refresh(self) -> None:
        ...

@dataclass(kw_only=True)
class Viewport:
    """A viewport is a "window" to the three-dimensional scene, showing the scene from the point of view of a virtual camera. 

The virtual camera's position and orientation are given by the :py:attr:`camera_pos` and :py:attr:`camera_dir` properties. Additionally, the :py:attr:`type` field allows you to switch between perspective and parallel projection modes or reset the camera to one of the standard axis-aligned orientations (top, left, front, etc.). The :py:meth:`.zoom_all` method repositions the camera automatically such that the entire scene becomes fully visible within the viewport. See also the documentation of the Adjust View dialog of OVITO to learn more about these camera-related settings. 

After the viewport's virtual camera has been set up, you can render an image or movie using the :py:meth:`.render_image` and :py:meth:`.render_anim` methods. For example: 

```python
  from ovito.io import import_file
  from ovito.vis import Viewport, TachyonRenderer
  
  pipeline = import_file('input/simulation.dump')
  pipeline.add_to_scene()
  
  vp = Viewport(type = Viewport.Type.Ortho, camera_dir = (2, 1, -1))
  vp.zoom_all()
  vp.render_image(filename='output/simulation.png', 
                  size=(320, 240), 
                  renderer=TachyonRenderer())
```

Furthermore, so-called *overlays* may be added to a viewport. Overlays are function objects that draw additional two-dimensional graphics or text on top of or behind the rendered scene, e.g. coordinate axes or a color legend. See the documentation of the :py:attr:`overlays` and :py:attr:`underlays` lists for more information."""

    class Type(enum.Enum):
        """"""
        NONE = enum.auto()
        Perspective = enum.auto()
        Ortho = enum.auto()
        Top = enum.auto()
        Bottom = enum.auto()
        Front = enum.auto()
        Back = enum.auto()
        Left = enum.auto()
        Right = enum.auto()
    camera_dir: Vector3 = (0.0, 0.0, 1.0)
    "camera_dir() -> numpy.typing.ArrayLike\n\nThe viewing direction of the viewport's camera in 3d world space coordinates."
    camera_pos: Vector3 = (0.0, 0.0, 0.0)
    "camera_pos() -> numpy.typing.ArrayLike\n\nThe position of the viewport's camera in 3d world space coordinates."
    camera_up: Vector3 = (0.0, 0.0, 0.0)
    "camera_up() -> numpy.typing.ArrayLike\n\nDirection vector specifying which coordinate axis will point upward in rendered images. Set this parameter to a non-zero vector in order to rotate the camera around the viewing direction and align the vertical direction in rendered images with a different simulation coordinate axis. If set to ``(0,0,0)``, then the upward axis is determined by the current user settings set in OVITO's application settings dialog (z-axis by default). \n\nDefault: ``(0.0, 0.0, 0.0)``"
    fov: float = 100.0
    "fov() -> float\n\nThe field of view of the viewport's camera. For perspective projections this is the camera's angle in the vertical direction (in radians). For orthogonal projections this is the visible range in the vertical direction (in world units)."
    type: Viewport.Type = Type.NONE
    'type() -> Viewport.Type\n\nSpecifies the projection type of the viewport. The following standard projections are available:\n\n  * ``Viewport.Type.Perspective``\n  * ``Viewport.Type.Ortho``\n  * ``Viewport.Type.Top``\n  * ``Viewport.Type.Bottom``\n  * ``Viewport.Type.Front``\n  * ``Viewport.Type.Back``\n  * ``Viewport.Type.Left``\n  * ``Viewport.Type.Right``\n\nThe first two types (``Perspective`` and ``Ortho``) allow you to set up custom views with arbitrary camera orientations.'

    @property
    def overlays(self) -> MutableSequence[ViewportOverlay]:
        """The list of :py:class:`ViewportOverlay` objects currently attached to this viewport. Overlays render two-dimensional graphics on top of the three-dimensional scene. See the following overlay types for more information:

   * :py:class:`TextLabelOverlay`
   * :py:class:`ColorLegendOverlay`
   * :py:class:`CoordinateTripodOverlay`
   * :py:class:`PythonViewportOverlay`


To attach a new overlay to the viewport, use the list's ``append()`` method:

```python
  from ovito.vis import Viewport, CoordinateTripodOverlay
  
  vp = Viewport(type = Viewport.Type.Ortho)
  tripod = CoordinateTripodOverlay(size = 0.07)
  vp.overlays.append(tripod)
```

The viewport also has an :py:attr:`underlays` list. :py:class:`ViewportOverlay` objects inserted into that list will be rendered *behind* the 3d objects of the scene."""
        ...

    @property
    def underlays(self) -> MutableSequence[ViewportOverlay]:
        """The list of :py:class:`ViewportOverlay` objects currently attached to this viewport. They render two-dimensional graphics *behind* the three-dimensional scene. See the :py:attr:`overlays` list for further information."""
        ...

    def create_qt_widget(self, parent: Optional[PySide6.QtWidgets.QWidget]=None) -> PySide6.QtWidgets.QWidget:
        """Creates an interactive visual widget displaying the three-dimensional scene as seen through this virtual viewport.
The method creates an interactive window accepting mouse inputs from the user similar to the viewport windows
of the OVITO desktop application. You can use this method to develop custom user interfaces based on the Qt cross-platform framework
that integrate OVITO's functionality and display the output of a data pipeline.

:param parent: An optional Qt widget that should serve as parent of the newly created viewport widget.
:returns: A new `QWidget <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QWidget.html>`__ displaying the three-dimensional scene as seen through the virtual viewport.

The Qt widget returned by this method is linked to this :py:class:`Viewport` instance.
Any changes your Python script subsequently makes to the non-visual :py:class:`Viewport` instance,
for example setting :py:attr:`camera_pos` or :py:attr:`camera_dir`, will automatically be reflected by the
visual viewport widget. Vice versa will interactions of the user with the viewport widget
automatically lead to changes of the corresponding fields of the :py:class:`Viewport` instance.

The following short example program demonstrates the use of the :py:meth:`create_qt_widget` method. Please see the
`Qt for Python <https://doc.qt.io/qtforpython-6/>`__ documentation for more information on how to create graphical
user interfaces using the Qt framework.

.. seealso:: :ref:`example_trajectory_viewer`

```python
  from PySide6.QtWidgets import QApplication
  from ovito.io import import_file
  from ovito.vis import Viewport
  import ovito
  
  # Let OVITO create a global PySide6 QApplication object, which is needed for displaying
  # a graphical user interface with the Qt/PySide6 framework.
  ovito.init_qt_app(support_gui=True)
  
  # Import model and add it to visualization scene.
  pipeline = import_file('input/simulation.dump')
  pipeline.add_to_scene()
  
  # Create a virtual Viewport.
  vp = Viewport(type=Viewport.Type.Perspective, camera_dir=(2, 1, -1))
  
  # Create a GUI widget associated with the viewport.
  widget = vp.create_qt_widget()
  widget.resize(500, 400)
  widget.setWindowTitle('OVITO Viewport Demo')
  widget.show()
  vp.zoom_all((widget.width(), widget.height()))
  
  # Start the Qt event loop by invoking the QApplication.exec() method.
  app = QApplication.instance()
  widget.destroyed.connect(app.quit) # Signal/slot connection to shutdown when user closes the viewport window.
  sys.exit(app.exec())
```"""
        ...

    def create_jupyter_widget(self, antialiasing: bool=True, picking: bool=False, vr_scale: float=0.0, layout: ipywidgets.Layout=ipywidgets.Layout(width='400px', height='200px')) -> JupyterViewportWidget:
        """Creates an interactive widget for embedding in a Jupyter notebook, which displays the 3d scene as seen through this virtual viewport.
The method returns an interactive notebook element, which accepts mouse inputs similar to the viewport windows
of the OVITO desktop application. It may be necessary to call :func:`display <ipython:IPython.display.display>` in order to show the widget:

.. code-block::

    vp = Viewport(type=Viewport.Type.Perspective, camera_dir=(0.5, 1.0, -0.4))
    vp.zoom_all()
    widget = vp.create_jupyter_widget(picking=True)
    display(widget)

The `Jupyter widget <https://ipywidgets.readthedocs.io/en/stable/>`__ returned by this method is permanently linked to this :py:class:`Viewport` instance.
Any changes you subsequently make to the non-visual :py:class:`Viewport`, for example, setting its :py:attr:`camera_pos` or :py:attr:`camera_dir`, will be
reflected by the visual viewport widget. Vice versa do all user interactions with the viewport widget
update the corresponding fields of the :py:class:`Viewport` object.

.. important::

    This method requires the `ipywidgets <https://ipywidgets.readthedocs.io/en/stable/user_install.html>`__ Python package.
    Please install this package in the Python interpreter used by your Jupyter environment.

:param antialiasing: Enables multisample anti-aliasing to reduce jagged edges, which appear during WebGL rasterization.
:param picking: Enables object picking. When hovering the mouse cursor over an object, the widget will display the object's properties as text.
:param vr_scale: Enables VR support (WebXR browser interface) if set to a positive value. The parameter value specifies the ratio of 1 length unit
                 of the simulation model and 1 meter in VR space. It thus controls the apparent size (scaling) of the model in virtual reality mode.
                 For example, if object dimensions are specified in terms of nanometers in the simulation model, then a *vr_scale* value of 0.2 would let
                 a 1 nanometer sphere appear 20 centimeters large in virtual reality space.
:param layout: The `layout attribute <https://ipywidgets.readthedocs.io/en/latest/examples/Widget%20Layout.html>`__ for the new Jupyter widget.
:return: `ipywidgets.DOMWidget <https://ipywidgets.readthedocs.io/en/stable/>`__

The ``layout`` attribute lets you control the `size of the widget <https://ipywidgets.readthedocs.io/en/stable/examples/Widget%20Layout.html>`__, e.g.:

.. code-block::

    from ipywidgets import Layout
    widget = vp.create_jupyter_widget(layout=Layout(width='100%', height='400px'))

.. caution::

    This method is still under active development and not fully functional yet. Expect these (known) limitations:

        * Changes you make to the scene or the viewport camera do not automatically trigger a refresh of the viewport widget.
          You need to explicitly call ``widget.refresh()`` to update the widget display whenever you change the scene.
        * Semi-transparent objects will likely be rendered incorrectly.
        * Viewport layers are not supported yet.

    These limitations will be resolved in a future update of the OVITO Python module.
    Please support the development of this new feature and report any issues you may encounter in our `issue tracker <https://gitlab.com/stuko/ovito/-/issues>`__
    or in the `OVITO support forum <https://matsci.org/c/ovito/>`__."""
        ...

    def render_anim(self, filename: str, size: Tuple[int, int]=(640, 480), fps: int=10, background: Color=(1.0, 1.0, 1.0), renderer: Optional[Renderer]=None, range: Optional[Tuple[int, int]]=None, every_nth: int=1, layout: Optional[Sequence[Tuple[Viewport, Tuple[float, float, float, float]]]]=None, stop_on_error: bool=True) -> None:
        """Renders an animation sequence.

:param filename: The filename under which the rendered animation should be saved.
                 Supported video formats are: :file:`.avi`, :file:`.mp4`, :file:`.mov` and :file:`.gif`.
                 Alternatively, an image format may be specified (:file:`.png`, :file:`.jpeg`).
                 In this case, a series of image files will be produced, one for each frame, which
                 may be combined into an animation using an external video encoding tool of your choice.
:param size: The resolution of the movie in pixels.
:param fps: The number of frames per second of the encoded movie. This determines the playback speed of the animation.
:param background: An RGB triplet in the range [0,1] specifying the background color of the rendered movie.
:param renderer: The rendering engine to use. If none is specified, either OpenGL or Tachyon are used,
                 depending on the availability of OpenGL in the script execution context.
:param range: The interval of frames to render, specified in the form ``(from,to)``.
              Frame numbering starts at 0. If no interval is specified, the entire animation is rendered, i.e.
              frame 0 through (`Pipeline.num_frames`-1).
:param every_nth: Frame skipping interval in case you don't want to render every frame of a very long animation.
:param layout: Optional definition of a multi-viewport layout to be rendered into the output image.
:param stop_on_error: Controls whether the rendering process should be aborted by raising an exception in case an error occurs in any of the scene's data pipelines.

See also the :py:meth:`.render_image` method for a more detailed discussion of some of these parameters."""
        ...

    def render_image(self, size: Tuple[int, int]=(640, 480), frame: int=0, filename: Optional[str]=None, background: Color=(1.0, 1.0, 1.0), alpha: bool=False, renderer: Optional[Renderer]=None, crop: bool=False, layout: Optional[Sequence[Tuple[Viewport, Tuple[float, float, float, float]]]]=None, stop_on_error: bool=True) -> PySide6.QtGui.QImage:
        """Renders an image of the viewport's view.

:param size: A pair of integers specifying the horizontal and vertical dimensions of the output image in pixels.
:param int frame: The animation frame to render. Numbering starts at 0. See the `Pipeline.num_frames` property for the number of loaded animation frames.
:param str filename: The file path under which the rendered image should be saved (optional).
                     Supported output formats are: :file:`.png`, :file:`.jpeg`, and :file:`.tiff`.
:param background: A triplet of RGB components in the range [0,1] specifying the background color of the rendered image (unless *alpha* is set).
:param alpha: This option makes the background transparent so that the rendered image may later be superimposed on a different backdrop.
              When using this option, make sure to save the image in the PNG format in order to preserve the generated transparency information.
:param renderer: The rendering engine to use. If set to ``None``, either OpenGL or Tachyon are used,
                 depending on the availability of OpenGL in the current execution context.
:param crop: This option cuts away border areas of the rendered image filled with the background color; the resulting image may thus turn out smaller than the requested *size*.
:param layout: Optional definition of a multi-viewport layout to be rendered into the output image. The layout must be provided as a list of :py:class:`Viewport` objects
               and corresponding rectangular areas, which determine where each viewport's picture appears within the composed output image.
               Please make use of OVITO Pro's code generation function to learn how to construct the *layout* argument.
:param stop_on_error: Controls whether the rendering process should be aborted by raising an exception in case an error occurs in any of the scene's data pipelines.
:returns: A `QImage <https://doc.qt.io/qtforpython-6/PySide6/QtGui/QImage.html>`__ object containing the rendered picture.

Populating the scene

Before rendering an image using this method, you should make sure the three-dimensional contains some
visible objects. Typically this involves calling the `Pipeline.add_to_scene()`
method on a pipeline to insert its output data into the scene::

   pipeline = import_file('simulation.dump')
   pipeline.add_to_scene()

Selecting the rendering backend

OVITO supports several different rendering backends for producing pictures of the three-dimensional scene:

    * :py:class:`OpenGLRenderer` (default)
    * :py:class:`TachyonRenderer`
    * :py:class:`OSPRayRenderer`

Each of these backends exhibits specific parameters that control the image quality and other aspect of the image
generation process. Typically, you would create an instance of one of these renderer classes, configure it and pass
it to the :py:meth:`!render_image()` method:

```python
  vp.render_image(filename='output/simulation.png', 
                  size=(320,240),
                  background=(0,0,0), 
                  renderer=TachyonRenderer(ambient_occlusion=False, shadows=False))
```

Post-processing images

If the ``filename`` parameter is omitted, the method does not save the rendered image to disk.
This gives you the opportunity to paint additional graphics on top before saving the
`QImage <https://doc.qt.io/qtforpython/PySide6/QtGui/QImage.html>`__ later using its ``save()`` method:

```python
  from ovito.vis import Viewport, TachyonRenderer
  from ovito.qt_compat import QtGui
  import ovito
  import sys
  
  # Render an image of the three-dimensional scene:
  vp = Viewport(type=Viewport.Type.Ortho, camera_dir=(2, 1, -1))
  vp.zoom_all()
  image = vp.render_image(size=(320,240), renderer=TachyonRenderer())
  
  # Note: Qt's font rendering function QPainter.drawText() requires a Qt application object.
  # Let OVITO create one if necessary:
  ovito.init_qt_app(support_gui=False) # We don't need full GUI support, just font rendering.
  
  # Paint on top of the rendered image using Qt's drawing functions:
  painter = QtGui.QPainter(image)
  painter.drawText(10, 20, "Hello world!")
  del painter
  
  # Save image to disk:
  image.save("output/image.png")
```

As an alternative to the direct method demonstrated above, you can also make use of a :py:class:`PythonViewportOverlay`
to paint custom graphics on top of rendered images."""
        ...

    def zoom_all(self, size: Tuple[int, int]=(640, 480)) -> None:
        """Repositions the viewport camera such that all objects in the scene become completely visible.
The current orientation (:py:attr:`camera_dir`) of the viewport's camera is maintained but
the :py:attr:`camera_pos` and :py:attr:`fov` parameters are adjusted by this method.

:param size: Size in pixels of the image that is going to be renderer from this viewport.
             This information is used to compute the aspect ratio of the viewport rectangle into which
             the visible objects should be fitted. The tuple should match the *size* argument you pass
             to :py:meth:`render_image` later.

Note that this method uses an axis-aligned bounding box computed at frame 0 of the
loaded trajectory enclosing all visible objects to adjust the viewport camera.
Make sure to call `Pipeline.add_to_scene()` first
to insert some visible object(s) into the scene."""
        ...