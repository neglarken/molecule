from __future__ import annotations
import collections.abc
import numbers
import warnings
from typing import Optional, Union
import numpy
import numpy.typing

from . import Property, PropertyContainer

# Give the PropertyContainer class a dict-like interface for accessing properties by name:
collections.abc.Mapping.register(PropertyContainer)

# Implementation of the printing method for the PropertyContainer class.
def _PropertyContainer__str__(self):
    return str(dict(self))
PropertyContainer.__str__ = _PropertyContainer__str__

# Assigns the property to the container.
# This is needed to make statements of the following kind work:
#
#    data.particles_['Position_'] += (0, 0, 1)
#
# That statement implicitly translates to
#
#    data.particles_['Position_'] = (data.particles_['Position_'] += (0, 0, 1))
#
# invoking this __setitem__() special method.
def _PropertyContainer__setitem__(self, key, value):
    if not isinstance(value, Property):
        raise ValueError("Expected a Property object. PropertyContainer only accepts Property objects as dictionary values.")
    if key.endswith('_'):
        key = key[:-1]
    if value.name != key:
        raise ValueError("Can only assign a Property whose name matches the key string. Consider using PropertyContainer.create_property() method instead.")
    # Accept only the existing property as new dictionary value:
    if self.get(key) is not value:
        raise ValueError("Can only re-assign an existing Property instance to the PropertyContainer but not a new instance. Consider using PropertyContainer.create_property() method instead if you want to assign a new property or replace the values of an existing property in the container.")
    # The following check is not needed as long as we only accept the existing property:
    #if not self.is_safe_to_modify:
    #    raise ValueError("Property assignment is only possible for a container that itself is mutable. "
    #                    "Make sure you are working with a mutable version of the {} object.".format(self.__class__.__name__))
PropertyContainer.__setitem__ = _PropertyContainer__setitem__

# Removes the property with the given name from the container.
def _PropertyContainer__delitem__(self, key):
    for p in self.properties:
        if p.name == key:
            self._remove_property(p)
            return
    raise KeyError(f"{self.__class__.__name__} data object does not contain the property '{key}'.")
PropertyContainer.__delitem__ = _PropertyContainer__delitem__

# Returns the list of names of all properties in the PropertyContainer.
def _PropertyContainer_keys(self):
    return collections.abc.KeysView(self)
PropertyContainer.keys = _PropertyContainer_keys

# Returns the list of name-property pairs in the PropertyContainer.
def _PropertyContainer_items(self):
    return collections.abc.ItemsView(self)
PropertyContainer.items = _PropertyContainer_items

# Returns the list Property objects in the PropertyContainer.
def _PropertyContainer_values(self):
    return self.properties
PropertyContainer.values = _PropertyContainer_values

# Internal helper function for registering standard property accessor fields for a PropertyContainer subclass.
def create_property_accessor(property_name, doc = None):
    base_property_name = property_name
    # Remove the leading underscore to get the actual property name.
    if base_property_name.endswith('_'):
        base_property_name = base_property_name[:-1]
        def getter(self):
            return self.get_(base_property_name)
    else:
        def getter(self) -> Optional[Property]:
            return self.get(property_name)
    def setter(self, val):
        # Detect trivial case where the property object is assigned to itself:
        if isinstance(val, Property) and val in self.properties and val.name == base_property_name:
            return
        self.create_property(base_property_name, data=val)
    return property(getter, setter, doc=doc)
PropertyContainer._create_property_accessor = staticmethod(create_property_accessor)

# Implementation of the PropertyContainer.create_property() method.
def _PropertyContainer_create_property(self,
                                       name: str,
                                       dtype: Optional[numpy.typing.DTypeLike] = None,
                                       components: Optional[Union[int, collections.abc.Sequence[str]]] = None,
                                       data: Optional[numpy.typing.ArrayLike] = None) -> Property:
    """
    Adds a new property with the given *name* to the container and optionally initializes its element-wise values with *data*.
    If a property with the given *name* already exists in the container, that existing property is returned
    (after replacing its contents with *data* if provided).

    :param name: Name of the property to create.
    :param data: Optional array with initial values for the new property.
                    The size of the array must match the element :py:attr:`count` of the container
                    and the shape must be consistent with the number of components of the property to be created.
    :param dtype: Data type of the user-defined property. Must be either :py:class:`python:int`, :py:class:`python:float`, :py:attr:`numpy:numpy.int8`, :py:attr:`numpy:numpy.int32`, :py:attr:`numpy:numpy.int64`, :py:attr:`numpy:numpy.float32`, or :py:attr:`numpy:numpy.float64`.
    :param components: Number of vector components of the user-defined property (1 if not specified) or a list of strings specifying the property's :py:attr:`~ovito.data.Property.component_names`.
    :returns: The new :py:class:`Property` object.

    You can create *standard* and *user-defined* properties in a container.
    A *standard* property with a prescribed data layout is automatically created if *name* matches one of the
    predefined names for the container type:

      * :py:class:`~ovito.data.Particles`: :ref:`List of standard particle properties <particle-properties-list>`
      * :py:class:`~ovito.data.Bonds`: :ref:`List of standard bond properties <bond-types-list>`
      * :py:attr:`SurfaceMesh.vertices <ovito.data.SurfaceMesh.vertices>`: :ref:`List of standard mesh vertex properties <surface-mesh-vertex-properties-list>`
      * :py:attr:`SurfaceMesh.faces <ovito.data.SurfaceMesh.faces>`: :ref:`List of standard mesh face properties <surface-mesh-face-properties-list>`
      * :py:attr:`SurfaceMesh.regions <ovito.data.SurfaceMesh.regions>`: :ref:`List of standard mesh region properties <surface-mesh-region-properties-list>`

    The length of the provided *data* array must match the number of elements in the container, which is given by :py:attr:`PropertyContainer.count`.
    If the property to be created is a vectorial property (having :math:`M>1` components), the initial data
    array should be of shape :math:`(N,M)` if provided:

    .. literalinclude:: ../example_snippets/property_container.py
        :lines: 16-17

    In general, however, *data* may be any value that is broadcastable to the array dimensions of the standard property (e.g. a uniform value).

    If you don't specify the function argument *data*, OVITO will automatically initialize the property elements with sensible default
    values (0 in most cases). Subsequently, you can set the property values for all or some of the elements:

    .. literalinclude:: ../example_snippets/property_container.py
        :lines: 23-24

    To create a *user-defined* property, specify a non-standard property name:

    .. literalinclude:: ../example_snippets/property_container.py
        :lines: 29-30

    In this case, the data type and the number of vector components of the new property are inferred from
    the provided *data* array. Specifying a one-dimensional array creates a scalar property whereas
    a two-dimensional array creates a vectorial property.

    If a property of the same name already exists in the container, it gets replaced with a :ref:`modifiable copy <data_ownership>` if necessary.
    Its contents get overwritten with the *data* array while maintaining all other attributes of the existing property, e.g. its :py:attr:`~ovito.data.Property.types` list.

    When creating a user-defined property, the *dtype* and *components* parameters may also be specified explicitly
    if you are going to fill in the property values in a second step:

    .. literalinclude:: ../example_snippets/property_container.py
        :lines: 34-35

    If desired, the components of the user-defined vector property can be given names, e.g. ``components=('X', 'Y', 'Z')``.

    Note: If you're creating new empty :py:class:`PropertyContainer`, its initial element :py:attr:`count` is 0.
    In this state, and only then, the :py:meth:`!create_property` method allows you to initialize the count while adding the very first property
    by providing a data array of the desired length:

    .. literalinclude:: ../example_snippets/property_container.py
        :lines: 40-47

    All subsequently added properties must have a matching length.
    """

    # Process 'name' function parameter.
    if isinstance(name, numbers.Integral):
        if name <= 0:
            raise TypeError("Invalid standard property type.")
        property_type = name
        property_name = self.standard_property_name(name)
    else:
        property_name = name
        property_type = self.standard_property_type_id(property_name)

    # Process 'components' function parameter.
    if isinstance(components, numbers.Integral):
        component_count = components
        component_names = []
    elif isinstance(components, collections.abc.Iterable):
        component_names = list(components)
        component_count = len(component_names)
    else:
        component_count = None
        component_names = []

    if property_type != 0:
        if component_count is not None:
            raise ValueError(f"'{property_name}' is the name of a standard property. When creating such a predefined property with a fixed data layout, you may not exlicitly specify the component count or list of vector components.")
        if dtype is not None:
            raise ValueError(f"'{property_name}' is the name of a standard property. When creating such a predefined property with a fixed data layout, you may not explicitly specify a data type.")
    else:
        if dtype is None:
            if data is None:
                raise ValueError("Must provide either a 'data' array or a data type (dtype).")
        if data is not None:
            data = numpy.asanyarray(data)
        elif component_count is None:
            component_count = 1
        if component_count is None:
            if data.ndim < 1 or data.ndim > 2:
                raise ValueError("Provided data array must be either 1 or 2-dimensional (or specify no. of components explicitly)")
            component_count = data.shape[1] if data.ndim==2 else 1
        if dtype is None:
            dtype = data.dtype
        if component_count < 1:
            raise ValueError(f"Invalid number of vector components specified for a user-defined property: {component_count}")
        if not property_name:
            raise ValueError(f"Invalid name for a property: '{property_name}'. Property name must not be empty.")
        if '.' in property_name:
            raise ValueError(f"Invalid name for a property: '{property_name}'. Name contains illegal character '.'")

        # Translate data type from Python to Qt metatype id.
        if dtype in (int, numpy.int32):
            dtype = Property.DataType.Int32
        elif dtype in (numpy.longlong, numpy.int64):
            dtype = Property.DataType.Int64
        elif dtype == numpy.int8:
            dtype = Property.DataType.Int8
        elif dtype == numpy.float32:
            dtype = Property.DataType.Float32
        elif dtype in (float, numpy.float64):
            dtype = Property.DataType.Float64
        else:
            raise TypeError("Invalid property dtype. Supported dtypes are: 'int', 'int8', 'int32', 'int64', 'float', 'float32', and 'float64'.")

        # Validate user-defined property name and component names.
        try:
            Property.throw_if_invalid_property_name(property_name)
            for cmpnt in component_names:
                Property.throw_if_invalid_property_name(cmpnt)
        except RuntimeError as exc:
            # Turn exception from C++ into a Python warning
            warnings.warn(str(exc), DeprecationWarning, stacklevel=2)

    # Check whether property already exists in the container.
    existing_prop = self.get_standard_property(property_type) if property_type != 0 else self.get_user_property(property_name)

    if existing_prop is None:

        if data is not None and isinstance(data, collections.abc.Sized) and (not isinstance(data, numpy.ndarray) or data.ndim != 0):
            element_count_hint = len(data)
        else:
            element_count_hint = self.count

        # If property does not exist yet in the container, create and add a new Property instance.
        if property_type != 0:
            prop = self.create_standard_property(property_type, data, element_count_hint)
        else:
            prop = self.create_user_property(property_name, dtype, component_count, data, element_count_hint, component_names)
    else:
        # Make sure the data layout of the existing property is compatible with the requested layout.
        if component_count is not None and existing_prop.component_count != component_count:
            raise ValueError(f"Existing property '{existing_prop.name}' has {existing_prop.component_count} vector component(s), but {component_count} component(s) have been requested for the new property.")
        if dtype is not None and existing_prop.data_type != dtype:
            from ovito.qt_compat import QtCore
            raise ValueError(f"Existing property '{existing_prop.name}' has data type '{QtCore.QMetaType.typeName(existing_prop.data_type)}', but data type '{QtCore.QMetaType.typeName(dtype)}' has been requested for the new property.")

        # Adjust container's element count to the provided data array length in case the count is still zero (the default).
        if data is not None and hasattr(data, '__iter__') and self.count == 0:
            self.count = len(data)
            # Note: Have to look up the property in the container again now, because changing the element count likely replaces all property objects with copies.
            existing_prop = self.get_standard_property(property_type) if property_type != 0 else self.get(property_name)

        # Make a copy of the existing property if necessary so that we can safely modify it. Then overwrite its contents if the user has provided new values.
        prop = self._assign_property_contents(existing_prop, data)

    return prop
PropertyContainer.create_property = _PropertyContainer_create_property

# Implementation of the PropertyContainer.delete_elements() method.
def _PropertyContainer_delete_elements(self, mask: numpy.typing.ArrayLike):
    """
    Deletes a subset of the elements from this container. The elements to be deleted must be specified in terms
    of a 1-dimensional mask array having the same length as the container (see :py:attr:`count`).
    The method will delete those elements whose corresponding mask value is non-zero, i.e., the ``i``-th element
    will be deleted if ``mask[i]!=0``.

    For example, to delete all currently selected particles, i.e., the subset of particles whose ``Selection`` property
    is non-zero, one would simply write:

    .. literalinclude:: ../example_snippets/property_container_delete_elements.py
        :lines: 10-10

    The effect of this statement is the same as for applying the :py:class:`~ovito.modifiers.DeleteSelectedModifier` to the particles list.
    """
    mask_arr = numpy.asanyarray(mask)
    if mask_arr.shape != (self.count, ):
        raise ValueError(f"Mask array must be a 1-d array of length {self.count}, matching the element count in the PropertyContainer.")
    return self._delete_elements(mask_arr)
PropertyContainer.delete_elements = _PropertyContainer_delete_elements

# Implementation of the PropertyContainer.delete_indices() method.
def _PropertyContainer_delete_indices(self, indices: collections.abc.Iterable[int]):
    """
    Deletes a subset of the elements from this container. The elements to be deleted must be specified in terms
    of a sequence of indices, all in the range 0 to :py:attr:`count`-1. The method accepts any type of iterable object,
    including sequence types, arrays, and generators.

    For example, to delete every other particle, one could use Python's :py:class:`python:range` function to generate
    all even indices up to the length of the particle container:

    .. literalinclude:: ../example_snippets/property_container_delete_elements.py
        :lines: 25-25
    """
    return self._delete_indices(indices)
PropertyContainer.delete_indices = _PropertyContainer_delete_indices
