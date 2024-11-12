from __future__ import annotations
from . import Lines, PropertyContainer
import numpy.typing as npt

Lines.positions = PropertyContainer._create_property_accessor(
    "Position",
    "The :py:class:`~ovito.data.Property` array containing the XYZ coordinates of the line vertices (:ref:`standard property <lines-property-list>` :guilabel:`Position`). "
    "May be ``None`` if the property is not defined yet. Use :py:meth:`~PropertyContainer.create_property` to add the property to the container if necessary. "
    "Use :py:attr:`!positions_` (with an underscore) to access an independent copy of the array, whose contents can be safely modified in place. ",
)
Lines.positions_ = PropertyContainer._create_property_accessor("Position_")

Lines.time_stamps = PropertyContainer._create_property_accessor(
    "Time",
    "The :py:class:`~ovito.data.Property` array with the time stamps of the line vertices (:ref:`standard property <lines-property-list>` :guilabel:`Time`). "
    "May be ``None`` if the property is not defined yet. Use :py:meth:`~PropertyContainer.create_property` to add the property to the container if necessary. "
    "Use :py:attr:`!time_stamps_` (with an underscore) to access an independent copy of the array, whose contents can be safely modified in place. ",
)
Lines.time_stamps_ = PropertyContainer._create_property_accessor("Time_")

Lines.sections = PropertyContainer._create_property_accessor(
    "Section",
    "The :py:class:`~ovito.data.Property` array with the section each line vertex belongs to (:ref:`standard property <lines-property-list>` :guilabel:`Section`). "
    "May be ``None`` if the property is not defined yet. Use :py:meth:`~PropertyContainer.create_property` to add the property to the container if necessary. "
    "Use :py:attr:`!sections_` (with an underscore) to access an independent copy of the array, whose contents can be safely modified in place. ",
)
Lines.sections_ = PropertyContainer._create_property_accessor("Section_")

Lines.colors = PropertyContainer._create_property_accessor(
    "Color",
    "The :py:class:`~ovito.data.Property` data array for the :guilabel:`Color` standard "
    "(:ref:`line property <lines-property-list>`); or ``None`` if that property is undefined.",
)
Lines.colors_ = PropertyContainer._create_property_accessor("Color_")


def _Lines_create_line(self, positions: npt.ArrayLike) -> int:
    """
    Adds a new section (a *polyline*) to an existing :py:class:`Lines` container. The container's vertex :py:attr:`~ovito.data.PropertyContainer.count`
    will be incremented by the number of newly inserted points. The method copies *positions* into the ``Position`` property array after extending the array
    and gives the new polyline a unique ``Section`` property value.

    :param positions: The xyz coordinates for the new lines section (*N* x 3 array). *N* must be at least 2.
    :return: The unique section identifier that was assigned to the newly added polyline.
    """
    npoints = len(positions)
    if npoints == 0:
        return -1

    self.count += npoints
    self.create_property("Position")[-npoints:] = positions

    if "Section" not in self:
        sections = self.create_property("Section")
    if npoints != self.count:
        sections = self.sections_
        sections[-npoints:] = sections[-npoints - 1] + 1
    return self.sections[-1]


Lines.create_line = _Lines_create_line
