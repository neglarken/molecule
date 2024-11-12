import numpy as np
from traitlets import TraitError, TraitType, Undefined
import warnings

def array_from_json(value, obj=None):
    if value is not None:
        # This will accept regular json data, like an array of values
        if isinstance(value, list):
            if len(value) > 0 and (isinstance(value[0], dict) and 'value' in value[0]):
                subarrays = [array_from_json(k) for k in value]
                if len(subarrays) > 0:
                    expected_length = len(subarrays[0])
                    # if a 'ragged' array, we should explicitly pass dtype=object
                    if any(len(k) != expected_length for k in subarrays[1:]):
                        return np.array(subarrays, dtype=object)
                return np.array(subarrays)
            elif len(value) > 0 and isinstance(value[0], list):
                return np.array(value, dtype=object)
            else:
                return np.array(value)
        elif 'value' in value:
            ar = np.frombuffer(value['value'], dtype=value['dtype']).reshape(value['shape'])
            if value.get('type') == 'date':
                assert value['dtype'] == 'float64'
                ar = ar.astype('datetime64[ms]')
            return ar

def array_to_json(ar, obj=None, force_contiguous=True):
    if ar is None:
        return None

    array_type = None

    if ar.dtype.kind == 'O':
        # Try to serialize the array of objects
        is_string = np.vectorize(lambda x: isinstance(x, str))
        is_array_like = np.vectorize(lambda x: isinstance(x, (list, np.ndarray)))

        if np.all(is_string(ar)):
            ar = ar.astype('U')
        elif np.all(is_array_like(ar)):
            return [array_to_json(np.array(row), obj, force_contiguous) for row in ar]
        else:
            raise ValueError("Unsupported dtype object")

    if ar.dtype.kind in ['S', 'U']:  # strings to as plain json
        return ar.tolist()

    if ar.dtype.kind == 'M':
        # since there is no support for int64, we'll use float64 but as ms
        # resolution, since that is the resolution the js Date object understands
        ar = ar.astype('datetime64[ms]').astype(np.float64)
        array_type = 'date'

    if ar.dtype.kind not in ['u', 'i', 'f']:  # ints and floats, and datetime
        raise ValueError("Unsupported dtype: %s" % (ar.dtype))

    if ar.dtype == np.int64:  # JS does not support int64
        ar = ar.astype(np.int32)

    if force_contiguous and not ar.flags["C_CONTIGUOUS"]:  # make sure it's contiguous
        ar = np.ascontiguousarray(ar)

    if not ar.dtype.isnative:
        dtype = ar.dtype.newbyteorder()
        ar = ar.astype(dtype)

    return {'value': memoryview(ar), 'dtype': str(ar.dtype), 'shape': ar.shape, 'type': array_type}

array_serialization = dict(to_json=array_to_json, from_json=array_from_json)

def array_dimension_bounds(mindim=0, maxdim=np.inf):
    def validator(trait, value):
        dim = len(value.shape)
        if dim < mindim or dim > maxdim:
            raise TraitError('Dimension mismatch for trait %s of class %s: expected an \
                array of dimension comprised in interval [%s, %s] and got an array of shape %s' % (
                trait.name, trait.this_class, mindim, maxdim, value.shape))
        return value
    return validator

def array_shape(*shape):
    def validator(trait, value):
        if value is None or value is Undefined:
            return value
        if value.shape != shape:
            raise TraitError('Array shape mismatch for trait %s of class %s: expected an \
                array of shape %s and got an array of shape %s' % (
                trait.name, trait.this_class, shape, value.shape))
        return value
    return validator

def shape_constraints(*args):
    # Example: shape_constraints(None,3) insists that the shape looks like (*,3)
    def validator(trait, value):
        if value is None or value is Undefined:
            return value
        if len(value.shape) != len(args):
            raise TraitError('%s shape expected to have %s components, but got %s components' % (
                trait.name, len(args), value.shape))
        for i, constraint in enumerate(args):
            if constraint is not None:
                if value.shape[i] != constraint:
                    raise TraitError(
                        'Dimension %i is supposed to be size %d, but got dimension %d' % (
                            i, constraint, value.shape[i]))
        return value
    return validator

def array_supported_kinds(kinds='biufMSUO'):
    def validator(trait, value):
        if value.dtype.kind not in kinds:
            raise TraitError('Array type not supported for trait %s of class %s: expected a \
                array of kind in list %r and got an array of type %s (kind %s)' % (
                trait.name, trait.this_class, list(kinds), value.dtype, value.dtype.kind))
        return value
    return validator

class Array(TraitType):
    """A numpy array trait type."""

    info_text = 'a numpy array'
    dtype = None

    def __init__(self, default_value=Undefined, allow_none=False, dtype=None, **kwargs):
        self.validators = []
        self.dtype = dtype
        if default_value is not None and default_value is not Undefined:
            default_value = np.asarray(default_value, dtype=self.dtype)
        super(Array, self).__init__(default_value=default_value, allow_none=allow_none, **kwargs)
#        self.metadata.setdefault("to_json", array_to_json)
#        self.metadata.setdefault("from_json", array_from_json)
        self.tag(**array_serialization)

    def valid(self, *validators):
        """
        Register new trait validators
        Validators are functions that take two arguments.
         - The trait instance
         - The proposed value
        Validators return the (potentially modified) value, which is either
        assigned to the HasTraits attribute or input into the next validator.
        They are evaluated in the order in which they are provided to the `valid`
        function.
        Example
        -------
        .. code:: python
            # Test with a shape constraint
            def shape(*dimensions):
                def validator(trait, value):
                    if value.shape != dimensions:
                        raise TraitError('Expected an array of shape %s and got an array with shape %s' % (dimensions, value.shape))
                    else:
                        return value
                return validator
            class Foo(HasTraits):
                bar = Array(np.identity(2)).valid(shape(2, 2))
            foo = Foo()
            foo.bar = [1, 2]  # Should raise a TraitError
        """
        self.validators.extend(validators)
        return self

    def validate(self, obj, value):
        """Validate the value against registered validators."""
        if value is None and not self.allow_none:
            self.error(obj, value)
        try:
            if not value is None and not value is Undefined:
                r = np.asarray(value, dtype=self.dtype)
                if isinstance(value, np.ndarray) and r is not value:
                    warnings.warn(
                        'Given trait value dtype "%s" does not match required type "%s". '
                        'A coerced copy has been created.' % (
                            np.dtype(value.dtype).name,
                            np.dtype(self.dtype).name))
                value = r
            for validator in self.validators:
                value = validator(self, value)
            return value
        except (ValueError, TypeError) as e:
            raise TraitError(e)

    def set(self, obj, value):
        new_value = self._validate(obj, value)
        old_value = obj._trait_values.get(self.name, self.default_value)
        obj._trait_values[self.name] = new_value
        if not np.array_equal(old_value, new_value):
            obj._notify_trait(self.name, old_value, new_value)

    def make_dynamic_default(self):
        if self.default_value is None or self.default_value is Undefined:
            return self.default_value
        else:
            return np.copy(self.default_value)