from __future__ import annotations
import ovito
from ..vis import PythonViewportOverlay
from ..data import DataCollection
from ..pipeline import Pipeline
import abc
import os
import sys
from contextlib import contextmanager
import traits.api
import numpy
import numpy.typing
from typing import Optional

class ViewportOverlayInterface(traits.api.HasTraits):
    """
    Base: :py:class:`traits.has_traits.HasTraits`

    Abstract base class for :ref:`custom viewport overlays <writing_custom_viewport_overlays>` written in Python.

    When you write a new viewport overlay, you must implement the :py:meth:`render` method, which gets called by the system each time a
    :py:class:`Viewport` window is being rendered:

    .. literalinclude:: ../example_snippets/viewport_overlay_interface.py
        :lines: 5-9

    If you are working with OVITO Pro, you can :ref:`add your overlay to one of the interactive viewport windows <manual:viewport_layers.python_script>`.
    If you are writing a standalone Python program to render images or movies using the :py:meth:`Viewport.render_image` and :py:meth:`Viewport.render_anim`
    methods, you need to add your overlay to the viewport's :py:attr:`~Viewport.overlays` or :py:attr:`~Viewport.underlays` lists.

    When adding your overlay to one of these lists, the instance must be wrapped in a :py:class:`~ovito.vis.PythonViewportOverlay` object as follows:

    .. literalinclude:: ../example_snippets/viewport_overlay_interface.py
        :lines: 22-25

    .. versionadded:: 3.9.2
    """

    # Import the Canvas helper class defined by the C++ code into the namespace of this class.
    class Canvas(PythonViewportOverlay.ViewportOverlayCanvas):
        """
        The system passes an instance if this class to the :py:meth:`ViewportOverlayInterface.render` method. It provides various painting functions
        for drawing 2d graphics on top of (or under) the 3d scene.
        """

        # Define these members only when generating the Sphinx documentation for the OVITO module.
        # Otherwise they are directly taken from the C++ base class implementation.
        if os.environ.get('OVITO_SPHINX_BUILD', False):
            @property
            def is_perspective(self) -> bool:
                """
                Indicates whether the 3d view being rendered uses a perspective projection or parallel projection. This depends on the selected :py:attr:`Viewport.type`.
                """
                return super().is_perspective

            @property
            def field_of_view(self) -> float:
                """
                The field of view of the viewport's camera (:py:attr:`Viewport.fov`). For perspective projections, this value specifies the frustum angle in the vertical direction
                (in radians). For orthogonal projections, this is the visible range in the vertical direction (in simulation units of length).
                """
                return super().field_of_view

            @property
            def physical_size(self) -> tuple[int,int]:
                """
                The width and height in physical pixels of the canvas onto which the overlay is currently being rendered. This resolution may be higher or lower than
                the output image size set by the user (:py:attr:`logical_size`) if rendering currently takes place in an interactive viewport window in the OVITO desktop application.

                On the other hand, when rendering an offscreen image, the :py:attr:`physical_size` typically equals the :py:attr:`logical_size` -- unless some form of supersampling is
                being performed (i.e., the image is rendered at an increased resolution before it is scaled down to the final output resolution).
                """
                return super().physical_size

            @property
            def logical_size(self) -> tuple[int,int]:
                """
                The width and height in logical pixels of the canvas. This value reflects
                the output image size set by the user (parameter ``size`` of the :py:meth:`Viewport.render_image` method).

                Note, however, that the logical canvas size may comprise only a sub-region of the full output image when rendering a :ref:`multi-viewport layout <manual:viewport_layouts.rendering>`.
                """
                return super().logical_size

            @property
            def device_pixel_ratio(self) -> float:
                # """
                # Ratio between (physical) *device pixels* and (logical) *device-independent pixels* of the rendering frame buffer. This ratio is usually 1.0 when rendering an offscreen image,
                # but it may be larger when rendering an interactive viewport on a high-resolution display. The device pixel ratio is configured at the operating system level
                # and allows `scaling up UI elements on high-dpi displays <https://en.wikipedia.org/wiki/Resolution_independence>`__.
                # """
                return super().device_pixel_ratio

            @property
            def preferred_qimage_format(self) -> 'PySide6.QtGui.QImage.Format':
                """
                Optimal `QImage.Format <https://doc.qt.io/qtforpython-6/PySide6/QtGui/QImage.html#PySide6.QtGui.QImage.Format>`__ to be used with
                the :py:meth:`draw_image` method for best performance. Typically, this will be either ``Format_ARGB32_Premultiplied`` or ``QImage.Format_RGBA8888``
                depending on the scene renderer currently in use.
                """
                return super().preferred_qimage_format

            @property
            def view_tm(self) -> numpy.typing.NDArray[numpy.float64]:
                """
                Affine transformation matrix encoding the location and orientation of the virtual camera in the three-dimensional scene.
                This 3-by-4 matrix transforms points/vectors from world space to camera space. For direct access to the camera information,
                use the :py:attr:`camera_pos`, :py:attr:`camera_dir`, and :py:attr:`camera_up` properties.
                """
                return super().view_tm

            @property
            def projection_tm(self) -> numpy.typing.NDArray[numpy.float64]:
                """
                The 3d projection matrix (4-by-4) that transforms coordinates from camera space to screen space.
                """
                return super().projection_tm

            @property
            def camera_pos(self) -> numpy.typing.NDArray[numpy.float64]:
                """
                The position of the virtual camera in world space coordinates.

                .. versionadded:: 3.11.0
                """
                return super().camera_pos

            @property
            def camera_dir(self) -> numpy.typing.NDArray[numpy.float64]:
                """
                The viewing direction of the virtual camera in 3d world space coordinates.

                .. versionadded:: 3.11.0
                """
                return super().camera_dir

            @property
            def camera_up(self) -> numpy.typing.NDArray[numpy.float64]:
                """
                The (in-plane) vertical axis of the camera's image projection plane in world space coordinates.

                .. versionadded:: 3.11.0
                """
                return super().camera_up

            def project_location(self, world_xyz: numpy.typing.ArrayLike) -> Optional[tuple[float,float]]:
                """
                Projects a point, given in 3d world-space coordinates, to screen space. This method can be used to determine
                where a 3d point would appear on the canvas in the rendered image.

                Note that the projected point may lay outside of the visible viewport region. Furthermore, for viewports with a
                perspective projection, the input point may lie behind the virtual camera. In this case no corresponding
                projected point in 2d screen space exists and the method returns ``None``.

                :param world_xyz: The (x,y,z) coordinates of the input point.
                :return: A (x,y) pair of reduced canvas coordinates; or ``None`` if *world_xyz* is behind the viewer.
                """
                return super().project_location(world_xyz)

            def project_length(self, world_xyz: numpy.typing.ArrayLike, length: float) -> float:
                """
                Projects a length or distance from 3d world space to 2d screen space. This method can be used to determine
                how large a 3d object, for example a sphere with a given radius, would appear in the rendered image.

                Additionally to the input *length*, the method takes a coordinate triplet (x,y,z).
                This is the location of the base point from where the distance is measured.

                :param world_xyz: The (x,y,z) world-space coordinates of the base point.
                :param length: The world-space size or distance to be converted to screen space.
                :return: The computed screen-space size expressed as a fraction of the canvas height.
                """
                return super().project_length(world_xyz, length)

        @staticmethod
        def _anchor_to_qt_alignment(anchor: str):
            from ovito.qt_compat import QtCore
            if anchor == 'south west': return QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignBottom
            if anchor == 'west': return QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignVCenter
            if anchor == 'north west': return QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignTop
            if anchor == 'north': return QtCore.Qt.AlignmentFlag.AlignHCenter | QtCore.Qt.AlignmentFlag.AlignTop
            if anchor == 'north east': return QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignTop
            if anchor == 'east': return QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter
            if anchor == 'south east': return QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignBottom
            if anchor == 'south': return QtCore.Qt.AlignmentFlag.AlignHCenter | QtCore.Qt.AlignmentFlag.AlignBottom
            if anchor == 'center': return QtCore.Qt.AlignmentFlag.AlignHCenter | QtCore.Qt.AlignmentFlag.AlignVCenter
            raise ValueError(f"Invalid anchor value '{anchor}'. Must be one of: 'center', 'south west', 'west', 'north west', 'north', 'north east', 'east', 'south east', 'south'.")

        def draw_image(self,
                       image,
                       pos: tuple[float,float] = (0.0, 0.0),
                       size: tuple[float,float] | None = (1.0, 1.0),
                       anchor: str = "south west"):
            """
            Draws a pixel-based image onto the canvas. The image must be provided as PySide6 `QImage <https://doc.qt.io/qtforpython/PySide6/QtGui/QImage.html>`__.
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

            **Example**

            .. literalinclude:: ../example_snippets/viewport_overlay_interface.py
                :lines: 31-38
            """
            from ovito.qt_compat import shiboken
            from ovito.qt_compat import QtGui
            if not isinstance(image, QtGui.QImage):
                raise TypeError("Invalid image parameter value: expected a QImage.")
            if size is None:
                size = (image.width() * self.device_pixel_ratio / image.devicePixelRatio(), image.height() * self.device_pixel_ratio / image.devicePixelRatio())
            self._draw_image(shiboken.getCppPointer(image)[0], pos, size, ViewportOverlayInterface.Canvas._anchor_to_qt_alignment(anchor))

        def draw_text(self,
                      text: str,
                      pos: tuple[float,float],
                      font_size: float = 0.05,
                      anchor: str = "south west",
                      color: tuple[float,float,float] = (0.0, 0.0, 0.0),
                      alpha: float = 1.0,
                      outline_width: float = 0.0,
                      outline_color: tuple[float,float,float] = (1.0, 1.0, 1.0),
                      tight_layout: bool = False,
                      rotation: float = 0.0):
            """
            Draws a text string onto the canvas.

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

            .. seealso:: :py:meth:`text_bounds`
            """
            self._draw_text(text, pos, font_size, ViewportOverlayInterface.Canvas._anchor_to_qt_alignment(anchor), color, alpha, outline_color, outline_width, tight_layout, rotation)

        def text_bounds(self,
                        text: str,
                        pos: tuple[float,float] = (0.0, 0.0),
                        font_size: float = 0.05,
                        anchor: str = "south west",
                        outline_width: float = 0.0,
                        tight_layout: bool = False,
                        rotation: float = 0.0) -> tuple[tuple[float,float], tuple[float,float]]:
            """
            Calculates the axis-aligned bounding box of a text as if it were drawn by :py:meth:`draw_text`.
            The parameters have the same meaning and default values as in the :py:meth:`draw_text` method.

            :param text: The text for which to compute the bounding box.
            :param pos: Position of the anchor point on the canvas in reduced (fractional) coordinates. The origin (0,0) is in the lower left corner of the canvas, (1,1) in the upper right.
            :param font_size: The size of the text font specified as a fraction of the height of the viewport canvas.
            :param anchor: Position of the anchor point relative to the text bounds. This controls the alignment of the text. Must be one of ``"center"``, ``"north west"``, ``"west"``, ``"south west"``, ``"south"``, ``"south east"``, ``"east"``, ``"north east"``, ``"north"``.
            :param outline_width: Width of the outline to draw around the glyphs in units of logical pixels.
            :param tight_layout: Controls whether the true (pixel-precise) bounds of the text are used when laying it out with respect to the anchor position.
                                 The default mode is to use a more extended bounding box, which is based on the general ascent and descent (line height) of the font.
            :param rotation: Rotation of the text in radians around the anchor point.
            :return: A tuple containing the coordinates of the lower left corner of the bounding box and its size (all in reduced canvas coordinates).
            """
            return self._text_bounds(text, pos, font_size, ViewportOverlayInterface.Canvas._anchor_to_qt_alignment(anchor), outline_width, tight_layout, rotation)

        @contextmanager
        def qt_painter(self):
            """
            Creates a `QPainter <https://doc.qt.io/qtforpython/PySide6/QtGui/QPainter.html>`__ object providing advanced
            drawing methods. The painter lets you `paint complex graphics <https://doc.qt.io/qtforpython-6/PySide6/QtGui/QPainter.html#more>`__ onto the viewport canvas.

            The method returns a Python context manager, which must be used in a ``with`` statement to obtain the actual `QPainter <https://doc.qt.io/qtforpython/PySide6/QtGui/QPainter.html>`__:

            .. literalinclude:: ../example_snippets/viewport_overlay_interface.py
                :lines: 46-57

            The QPainter's `window rect <https://doc.qt.io/qtforpython-6/PySide6/QtGui/QPainter.html#PySide6.QtGui.QPainter.window>`__ is configured
            to match the canvas' :py:attr:`logical_size`. The QPainter's `viewport rect <https://doc.qt.io/qtforpython-6/PySide6/QtGui/QPainter.html#PySide6.QtGui.QPainter.viewport>`__ is configured
            to match the canvas' :py:attr:`physical_size`. See `Window-Viewport Conversion <https://doc.qt.io/qtforpython-6/overviews/coordsys.html#window-viewport-conversion>`__.

            Internally, the method creates a temporary `QImage <https://doc.qt.io/qtforpython/PySide6/QtGui/QImage.html>`__ for the
            `QPainter <https://doc.qt.io/qtforpython/PySide6/QtGui/QPainter.html>`__ to draw into. When leaving the ``with`` block,
            that image gets copied to the canvas using the :py:meth:`draw_image` method.
            """
            from ovito.qt_compat import QtGui
            image = QtGui.QImage(*self.physical_size, self.preferred_qimage_format)
            image.fill(0)
            painter = QtGui.QPainter(image)
            painter.setWindow(0, 0, *self.logical_size)
            painter.setRenderHint(QtGui.QPainter.Antialiasing)
            painter.setRenderHint(QtGui.QPainter.TextAntialiasing)
            try:
                yield painter
            finally:
                painter.end()
            self.draw_image(image, pos=(0.0, 0.0), size=(1.0, 1.0))

        @contextmanager
        def mpl_figure(self,
                       pos: tuple[float,float] = (0.5, 0.5),
                       size: tuple[float,float] = (0.5, 0.5),
                       anchor: str = "center",
                       font_scale: float = 1.0,
                       alpha: float = 0.0,
                       tight_layout: bool = False):
            """
            A context manager for creating and rendering a `Matplotlib <https://matplotlib.org>`__ figure onto the canvas.

            This method creates a Matplotlib figure and renders it onto the viewport canvas. Inside a `with` statement, you can add various types of plots
            to the Matplotlib figure. The figure is then drawn onto the canvas.

            :param pos: Position of the anchor point for placing the figure on the canvas. The origin (0,0) is in the lower left corner of the canvas, (1,1) in the upper right.
            :param size: Size of the figure in relative viewport canvas coordinates, specified as a tuple *(width, height)*.
            :param anchor: Position of the anchor point relative to the figure bounds. Must be one of ``"center"``, ``"north west"``, ``"west"``, ``"south west"``, ``"south"``, ``"south east"``, ``"east"``, ``"north east"``, ``"north"``.
            :param font_scale: Scaling factor applied to the fonts in the figure. Useful for adjusting the text size of axis labels.
            :param alpha: Transparency level of the figure background. A value of 0.0 makes the background fully transparent, while 1.0 makes it opaque.
            :param tight_layout: Controls whether to automatically adjust subplot parameters for a "tight" layout.
            :return: A generator yielding a `Matplotlib figure <https://matplotlib.org/stable/api/figure_api.html#matplotlib.figure.Figure>`__. The figure is automatically closed and copied to the canvas after the generator exits.

            **Example**

            Create a Matplotlib figure, plot some data dynamically calculated by a :py:class:`~ovito.modifiers.HistogramModifier` as part of a data pipeline,
            and render it onto the viewport canvas:

            .. literalinclude:: ../example_snippets/viewport_overlay_interface.py
                :lines: 65-74

            .. note::

                To use the :py:meth:`mpl_figure` method, you first need to install the `matplotlib` Python module.
                See :ref:`ovitos_install_modules`.

            .. seealso:: :ref:`example_data_plot_overlay`

            """
            from ovito.qt_compat import QtGui
            import matplotlib
            import matplotlib.pyplot as plt
            matplotlib.use('Agg') # Activate 'Agg' non-interactive backend for off-screen plotting.
            dpi = 80.0 * font_scale * self.physical_size[0] / self.logical_size[0]
            w = size[0] * self.physical_size[0] / dpi
            h = size[1] * self.physical_size[1] / dpi
            fig = plt.figure(figsize=(w,h), dpi=dpi, tight_layout=tight_layout)
            try:
                fig.patch.set_alpha(alpha) # Make background semi-transparent
                yield fig
                buffer = fig.canvas.print_to_buffer()
                image = QtGui.QImage(buffer[0], buffer[1][0], buffer[1][1], QtGui.QImage.Format_RGBA8888)
                self.draw_image(image, pos=pos, size=size, anchor=anchor)
            finally:
                plt.close(fig)

    # Abstract method that must be implemented by all sub-classes:
    @abc.abstractmethod
    def render(self, canvas: Canvas, *, data: DataCollection, pipeline: Optional[Pipeline], interactive: bool, frame: int, **kwargs):
        """
        Abstract method to implement custom rendering of viewport overlays.

        This method must be overridden in subclasses of :py:class:`ViewportOverlayInterface` to define the custom rendering behavior for the overlay.
        When the viewport window is being rendered, this method is called by the system to generate the overlay's visual content.

        :param canvas: An object provided by the system, which offers various painting functions for drawing 2D graphics on top of the 3D scene.
        :param data: The data collection produced by the overlay's associated :py:attr:`~PythonViewportOverlay.pipeline`. It contains the dynamically computed data that can be used for rendering the overlay.
        :param pipeline: The overlay's associated :py:attr:`~PythonViewportOverlay.pipeline`.
        :param interactive: A boolean flag indicating whether the rendering happens in an interactive context (in a GUI environment) or off-screen (e.g., for generating images and animations). Your overlay can use this to perform a long-running computation only in a non-interactive context and render a placeholder instead in the interactive viewports of the OVITO desktop app.
        :param frame: The animation frame number currently being rendered.
        :param kwargs: Captures any additional arguments that may be passed in by the system.
        """
        raise NotImplementedError("Abstract method render() must be implemented by the ViewportOverlayInterface derived class.")

ovito.vis.ViewportOverlayInterface = ViewportOverlayInterface
ovito.vis.PythonViewportOverlay.ViewportOverlayCanvas.draw_image = ViewportOverlayInterface.Canvas.draw_image
ovito.vis.PythonViewportOverlay.ViewportOverlayCanvas.draw_text = ViewportOverlayInterface.Canvas.draw_text
ovito.vis.PythonViewportOverlay.ViewportOverlayCanvas.text_bounds = ViewportOverlayInterface.Canvas.text_bounds
ovito.vis.PythonViewportOverlay.ViewportOverlayCanvas.qt_painter = ViewportOverlayInterface.Canvas.qt_painter
ovito.vis.PythonViewportOverlay.ViewportOverlayCanvas.mpl_figure = ViewportOverlayInterface.Canvas.mpl_figure
