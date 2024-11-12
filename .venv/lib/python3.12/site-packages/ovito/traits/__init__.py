"""
.. versionadded:: 3.8.0

This module contains various `trait types <https://docs.enthought.com/traits/traits_user_manual/intro.html>`__, which
can be used in the context of :ref:`custom modifiers <writing_custom_modifiers>`, :ref:`custom viewport overlays <writing_custom_viewport_overlays>`, and
other Python-based extensions for OVITO. Traits encapsulate :ref:`object parameters <writing_custom_modifiers.advanced_interface.user_params>`,
which are displayed in the OVITO graphical user interface and can be adjusted by the user.

The specific trait types defined in this module supplement the `generic trait types <https://docs.enthought.com/traits/traits_user_manual/defining.html#predefined-traits>`__
provided by the `Traits <https://docs.enthought.com/traits/index.html>`__ Python package, which can be used to define parameters with simple data types such as numeric values and
strings. The OVITO-specific trait types in this module are tailored to the needs of OVITO's Python scripting interface and provide additional functionality
for interacting with the OVITO data pipeline, the undo system, and the graphical user interface.

The following OVITO-specific trait types are available:

- :py:class:`OvitoObject`: A trait type that stores an instance of a class from the :py:mod:`ovito` package, e.g. a visual element, modifier, or data object.
- :py:class:`Color`: A trait type that stores a tuple of three floats representing the RGB components of a color parameter.
- :py:class:`Vector2`: A trait type that stores a tuple of two floats representing a vector or point in 2d space.
- :py:class:`Vector3`: A trait type that stores a tuple of three floats representing a vector or point in 3d space.
- :py:class:`FilePath`: A trait type that stores a filesystem path. In the GUI, a file selection dialog is displayed for the user to pick the trait value.
- :py:class:`DataObjectReference`: A trait type that holds a reference to a certain :py:class:`~ovito.data.DataObject` in a :py:class:`~ovito.data.DataCollection` object hierarchy.
- :py:class:`PropertyReference`: A trait type that holds a reference to a :py:class:`~ovito.data.Property`.
"""

import traits.api
from collections.abc import Iterable
import ovito.nonpublic
import ovito.data
from typing import Optional, Union
import collections.abc
from enum import Enum
import warnings

__all__ = ['OvitoObject', 'Color', 'Vector2', 'Vector3', 'FilePath', 'DataObjectReference', 'PropertyReference', 'OvitoObjectTrait', 'ColorTrait']

class OvitoObject(traits.api.Instance):
    """
    A `trait type <https://docs.enthought.com/traits/traits_user_manual/intro.html>`__ that stores an instance of a class from the :py:mod:`ovito` package,
    e.g. a visual element, modifier, or data object. The object instance is treated as an sub-object of the class defining the trait,
    and the sub-object's parameters are displayed in the OVITO graphical user interface such that the user can adjust its settings.
    See :ref:`writing_custom_modifiers.advanced_interface.user_params` for more information.

    :param klass: The object class type to instantiate.
    :param params: All other keyword parameters are forwarded to the constructor of the object class.
    """
    def __init__(self, klass, factory=None, **params):
        params['_load_user_defaults_in_gui'] = True # Initialize object parameters to user default values when running in the GUI environment.
        for key in params.keys():
            if key.startswith('ovito_'):
                warnings.warn(f"OvitoObject trait does not accept 'ovito_*' metadata keys.", stacklevel=2)
        super().__init__(klass, factory=factory, kw=params)

class Color(traits.api.BaseTuple):
    """
    A `trait type <https://docs.enthought.com/traits/traits_user_manual/intro.html>`__ that stores a tuple of three floats representing the RGB components of a color parameter.
    The three components must be in the range 0.0 - 1.0.

    See :ref:`writing_custom_modifiers.advanced_interface.user_params` for more information.

    :param default: The initial RGB values to be assigned to the parameter trait.
    :param metadata: Additional keyword arguments are forwarded to the base trait constructor.
    """
    def __init__(self, default=(1.0, 1.0, 1.0), **metadata):
        if not isinstance(default, tuple) and isinstance(default, Iterable):
            default = tuple(default)
        if len(default) != 3:
            raise ValueError("Expected tuple of length 3.")
        super().__init__(default, **metadata)

    # Override the validate() method to also accept NumPy arrays.
    # Some OVITO functions return RGB colors as NumPy arrays, not tuples.
    def validate(self, object, name, value):
        if not isinstance(value, tuple) and isinstance(value, Iterable):
            value = tuple(value)
        return super().validate(object, name, value)

class FilePath(traits.api.BaseFile):
    """
    A `trait type <https://docs.enthought.com/traits/traits_user_manual/intro.html>`__ that stores a filesystem path.
    In the GUI, a file selection dialog is displayed for the user to pick the trait value.

    See :ref:`writing_custom_modifiers.advanced_interface.user_params` for more information.

    :param default: Initial parameter trait value.
    :param metadata: Additional keyword arguments are forwarded to the base trait constructor.

    .. versionadded:: 3.10.0
    """
    def __init__(self, default: str = "", **metadata) -> None:
        super().__init__(default, **metadata)

class Vector2(traits.api.BaseTuple):
    """
    A `trait type <https://docs.enthought.com/traits/traits_user_manual/intro.html>`__ that stores a tuple of two floats, which represent a vector or point in 2d space.

    See :ref:`writing_custom_modifiers.advanced_interface.user_params` for more information.

    :param default: The initial vector value to be assigned to the parameter trait.
    :param metadata: Additional keyword arguments are forwarded to the base trait constructor.

    .. versionadded:: 3.10.0
    """
    def __init__(self, default=(0.0, 0.0), **metadata):
        if len(default) != 2:
            raise ValueError("Expected tuple of length 2.")
        super().__init__(default, **metadata)

    # Override the validate() method to also accept NumPy arrays.
    # Some OVITO functions return Vector2 values as NumPy arrays, not tuples.
    def validate(self, object, name, value):
        if not isinstance(value, tuple) and isinstance(value, Iterable):
            value = tuple(value)
        return super().validate(object, name, value)

class Vector3(traits.api.BaseTuple):
    """
    A `trait type <https://docs.enthought.com/traits/traits_user_manual/intro.html>`__ that stores a tuple of three floats, which represent a vector or point in 3d space.

    See :ref:`writing_custom_modifiers.advanced_interface.user_params` for more information.

    :param default: The initial vector value to be assigned to the parameter trait.
    :param metadata: Additional keyword arguments are forwarded to the base trait constructor.

    .. versionadded:: 3.10.0
    """
    def __init__(self, default=(0.0, 0.0, 0.0), **metadata):
        if len(default) != 3:
            raise ValueError("Expected tuple of length 3.")
        super().__init__(default, **metadata)

    # Override the validate() method to also accept NumPy arrays.
    # Some OVITO functions return Vector3 values as NumPy arrays, not tuples.
    def validate(self, object, name, value):
        if not isinstance(value, tuple) and isinstance(value, Iterable):
            value = tuple(value)
        return super().validate(object, name, value)

class DataObjectReference(traits.api.Instance):
    """
    This `trait type <https://docs.enthought.com/traits/traits_user_manual/intro.html>`__ holds a :py:class:`DataObject.Ref <ovito.data.DataObject.Ref>` reference
    to a data object in a :py:class:`~ovito.data.DataCollection`.
    The stored reference tells where to find the selected object in the pipeline output but it does not hold the actual object.
    The user can select the data object from a list of available objects in the OVITO graphical user interface.
    To retrieve the actual object from a data collection, use the :py:meth:`DataCollection.get <ovito.data.DataCollection.get>` method.

    :param object_type: A :py:class:`~ovito.data.DataObject`-derived class type.
    :param filter: Optional callback function that can be used to additionally filter the list of data objects shown to the user in the GUI.
    :param default_value: Optional :py:class:`DataObject.Ref <ovito.data.DataObject.Ref>` instance to be used as the initial value of the trait.
    :param metadata: Additional keyword arguments are forwarded to the base trait constructor.

    Usage example: a :ref:`custom modifier <writing_custom_modifiers>` that lets the user select a :py:class:`~ovito.data.DataTable` object from the pipeline:

    .. literalinclude:: ../example_snippets/data_object_reference_trait.py
      :lines: 6-18

    This is how you would insert the custom modifier into the pipeline and configure it to print a specific data table:

    .. literalinclude:: ../example_snippets/data_object_reference_trait.py
      :lines: 26-26

    .. versionadded:: 3.11.0
    """
    def __init__(self,
                 object_type: type[ovito.data.DataObject],
                 filter: Optional[collections.abc.Callable[[ovito.data.DataObject], bool]] = None,
                 default_value: Optional[ovito.data.DataObject.Ref] = None,
                 **metadata):
        if not issubclass(object_type, ovito.data.DataObject):
            raise ValueError("Expected a subclass of ovito.data.DataObject")
        if default_value:
            if not isinstance(default_value, ovito.data.DataObject.Ref):
                raise ValueError("Expected a DataObject.Ref instance as default value")
            metadata['factory'] = lambda: default_value
        super().__init__(
            klass=ovito.data.DataObject.Ref,
            args=(),
            allow_none=False,
            ovito_data_class=object_type,
            ovito_data_filter=filter,
            **metadata)

class PropertyReference(traits.api.Str):
    """
    A `trait type <https://docs.enthought.com/traits/traits_user_manual/intro.html>`__ that manages a reference
    to a :py:class:`~ovito.data.Property`. The reference is encoded as a string containing the name of the property -
    optionally followed by a dot and the name of a vector component of the property.

    See :ref:`writing_custom_modifiers.advanced_interface.user_params` for more information.

    :param container:   1. :py:class:`~ovito.data.DataObject.Ref` specifying a :py:class:`~ovito.data.PropertyContainer` object
                           from which the user can select a property or
                        2. name of a :py:class:`DataObjectReference` trait defined in the same class,
                           which allows the user to select a property container.
    :param default_value: Initial property name to be assigned to the parameter trait.
    :param mode: Controls whether the trait should list entire properties, individual components of properties, or both.
    :param filter: Optional callback function that can be used to filter the list of properties shown to the user.
    :param metadata: Additional keyword arguments are forwarded to the base trait constructor.

    **Usage example**:

    .. literalinclude:: ../example_snippets/property_reference_trait.py
      :lines: 6-37

    .. versionadded:: 3.11.0
    """
    class Mode(Enum):
        """
        Enumeration of possible component listing modes for vector properties.
        """
        #: List entire properties (not their vector components).
        Properties = "properties"
        #: List individual components of vector properties.
        Components = "components"
        #: List entire properties AND their vector components.
        PropertiesAndComponents = "properties_and_components"
    def __init__(self,
                 *,
                 container: Union[str, ovito.data.DataObject.Ref] = ovito.data.DataObject.Ref(ovito.data.Particles),
                 default_value: str = '',
                 mode: Mode = Mode.Components,
                 filter: Optional[collections.abc.Callable[[ovito.data.PropertyContainer, ovito.data.Property], bool]] = None,
                 **metadata):
        if isinstance(container, ovito.data.DataObject.Ref):
            metadata['ovito_property_container_ref'] = container
        elif isinstance(container, str):
            metadata['ovito_property_container_trait'] = container
        else:
            raise ValueError("Expected a trait name (string) or a DataObject.Ref")
        if not isinstance(mode, PropertyReference.Mode):
            raise ValueError("Expected a PropertyReference.Mode enum value")
        super().__init__(
            default_value=default_value,
            ovito_list_mode=mode,
            ovito_property_filter=filter,
            **metadata)

# For backward compatibility with OVITO 3.9.2:
OvitoObjectTrait = OvitoObject
ColorTrait = Color