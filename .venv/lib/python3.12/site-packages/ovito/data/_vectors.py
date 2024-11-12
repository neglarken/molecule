from . import Vectors, PropertyContainer

Vectors.positions = PropertyContainer._create_property_accessor(
    "Position",
    "The :py:class:`~ovito.data.Property` array containing the XYZ coordinates of vectors' "
    "base points (:ref:`standard property <vectors-property-list>` :guilabel:`Position`). "
    "May be ``None`` if the property is not defined yet. Use :py:meth:`~PropertyContainer.create_property` "
    "to add the property to the container if necessary. "
    "Use :py:attr:`!positions_` (with an underscore) to access an independent copy of the array, "
    "whose contents can be safely modified in place. ",
)
Vectors.positions_ = PropertyContainer._create_property_accessor("Position_")

Vectors.directions = PropertyContainer._create_property_accessor(
    "Direction",
    "The :py:class:`~ovito.data.Property` array containing the XYZ components of the vectors "
    "(:ref:`standard property <vectors-property-list>` :guilabel:`Direction`). "
    "May be ``None`` if the property is not defined yet. Use :py:meth:`~PropertyContainer.create_property` "
    "to add the property to the container if necessary. "
    "Use :py:attr:`!directions_` (with an underscore) to access an independent copy of the array, "
    "whose contents can be safely modified in place. ",
)
Vectors.directions_ = PropertyContainer._create_property_accessor("Direction_")

Vectors.colors = PropertyContainer._create_property_accessor(
    "Color",
    "The :py:class:`~ovito.data.Property` data array for the ``Color`` "
    ":ref:`standard vector property <vectors-property-list>`; or ``None`` if that property is undefined. "
    "Use :py:meth:`~PropertyContainer.create_property` "
    "to add the property to the container if necessary. "
    "Use :py:attr:`!colors_` (with an underscore) to access an independent copy "
    "of the array, whose contents can be safely modified in place.",
)
Vectors.colors_ = PropertyContainer._create_property_accessor("Color_")

Vectors.transparencies = PropertyContainer._create_property_accessor(
    "Transparency",
    "The :py:class:`~ovito.data.Property` array containing the transparency values "
    "(:ref:`standard property <vectors-property-list>` :guilabel:`Transparency`) "
    "of the vectors. "
    "May be ``None`` if the property is not defined yet. Use :py:meth:`~PropertyContainer.create_property` "
    "to add the property to the container if necessary. "
    "Use :py:attr:`!transparencies_` (with an underscore) to access an independent copy "
    "of the array, whose contents can be safely modified in place. ",
)
Vectors.transparencies_ = PropertyContainer._create_property_accessor("Transparency_")
