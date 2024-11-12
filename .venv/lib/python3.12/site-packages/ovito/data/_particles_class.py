from __future__ import annotations
from . import Particles, PropertyContainer, SimulationCell, DataCollection, Bonds, Angles, Dihedrals, Impropers
import numpy.typing
import collections.abc
from typing import Any, Optional, Union

Particles.positions  = PropertyContainer._create_property_accessor("Position",
"""
    Returns the :py:class:`~ovito.data.Property` data array storing the particle coordinates, i.e. the values of the ``Position`` standard :ref:`particle property <particle-properties-list>`.
    Accessing this field is equivalent to a name-based lookup in the :py:class:`PropertyContainer`::

        assert data.particles.positions is (data.particles['Position'] if 'Position' in data.particles else None)

    Under special circumstances the ``Position`` particle property might not be defined (yet). Then the value is ``None``.

    .. note::

        The returned :py:class:`~ovito.data.Property` will likely be write-protected. If you intend to modify (some of) the particle coordinates in the property array,
        request a modifiable version of the array by using the :py:ref:`underscore notation <underscore_notation>`::

            data.particles_.positions_[:] = new_coordinates

        Alternatively, you can use the :py:meth:`~PropertyContainer.create_property` method to newly create or overwrite the entire property::

            data.particles_.create_property('Position', data=new_coordinates)
""")
Particles.positions_ = PropertyContainer._create_property_accessor("Position_")

Particles.colors  = PropertyContainer._create_property_accessor("Color", "The :py:class:`~ovito.data.Property` data array for the ``Color`` standard :ref:`particle property <particle-properties-list>`; or ``None`` if that property is undefined.")
Particles.colors_ = PropertyContainer._create_property_accessor("Color_")

Particles.identifiers  = PropertyContainer._create_property_accessor("Particle Identifier",
"""
    Returns a :py:class:`~ovito.data.Property` data array containing the values of the ``Particle Identifier`` standard :ref:`particle property <particle-properties-list>`; or ``None`` if that particle property does not exist.

    The property array stores the numerical IDs that are typically used by simulation codes to uniquely identify individual particles.

    .. note::

        A particle *identifier* is an arbitrary and unique 64-bit integer value permanently associated with a particle. In contrast, the particle's *index* is implicitly
        given by the particle's current position within the particles list.

        If you delete some of the particles from the system, using the :py:class:`~ovito.modifiers.DeleteSelectedModifier` or the :py:meth:`~PropertyContainer.delete_elements` method for example,
        the indices of the remaining particles get typically shifted but their unique IDs stay the same.

    Some of OVITO's :ref:`simulation file readers <manual:file_formats.input>` provide the option to sort the list of particles by ID during
    import to obtain a stable ordering. Generally, however, the storage order of particles is arbitrary and can vary between frames
    of a trajectory. The :py:meth:`.remap_indices` method can be useful in this situation.

    .. note::

        The value of :py:attr:`.identifiers` may be ``None``, which means particles don't have any identifiers. Many operations in OVITO then assume that the ordering
        and total count of particles are constant throughout the entire simulation trajectory and the identities are implicitly given by the particles' *indices*.

    Given some list of zero-based particle *indices*, determining the corresponding unique identifiers requires just a simple :ref:`NumPy indexing <numpy:basics.indexing>` expression:

    .. literalinclude:: ../example_snippets/particle_identifiers.py
       :lines: 10-12

    The reverse lookup, i.e., finding the indices at which particles with certain IDs are stored in the list, requires some more work.
    That's because particles may be stored in arbitrary order, i.e., the sequence of unique IDs is generally not sorted nor contigous.
    A rather **slow** approach is to :obj:`search <numpy:numpy.argwhere>` through the entire array of IDs to locate the one we are looking for:

    .. literalinclude:: ../example_snippets/particle_identifiers.py
       :lines: 16-18

    We can speed things up with some extra effort, which pays off when there is a need to look up several particle IDs.
    To this end, we first :obj:`sort <numpy:numpy.argsort>` the list of IDs, then perform a more efficient :obj:`sorted search <numpy:numpy.searchsorted>`,
    and finally map the found indices back to the original particle ordering:

    .. literalinclude:: ../example_snippets/particle_identifiers.py
       :lines: 23-26

    The above ``assert`` statements are for illustration purposes only.
""")
Particles.identifiers_ = PropertyContainer._create_property_accessor("Particle Identifier_")

Particles.particle_types  = PropertyContainer._create_property_accessor("Particle Type", "The :py:class:`~ovito.data.Property` data array for the ``Particle Type`` standard :ref:`particle property <particle-properties-list>`; or ``None`` if that property is undefined.")
Particles.particle_types_ = PropertyContainer._create_property_accessor("Particle Type_")

Particles.structure_types  = PropertyContainer._create_property_accessor("Structure Type", "The :py:class:`~ovito.data.Property` data array for the ``Structure Type`` standard :ref:`particle property <particle-properties-list>`; or ``None`` if that property is undefined.")
Particles.structure_types_ = PropertyContainer._create_property_accessor("Structure Type_")

Particles.forces  = PropertyContainer._create_property_accessor("Force", "The :py:class:`~ovito.data.Property` data array for the ``Force`` standard :ref:`particle property <particle-properties-list>`; or ``None`` if that property is undefined.")
Particles.forces_ = PropertyContainer._create_property_accessor("Force_")

Particles.selection  = PropertyContainer._create_property_accessor("Selection", "The :py:class:`~ovito.data.Property` data array for the ``Selection`` standard :ref:`particle property <particle-properties-list>`; or ``None`` if that property is undefined.")
Particles.selection_ = PropertyContainer._create_property_accessor("Selection_")

Particles.masses  = PropertyContainer._create_property_accessor("Mass", "The :py:class:`~ovito.data.Property` data array for the ``Mass`` standard :ref:`particle property <particle-properties-list>`; or ``None`` if that property is undefined.")
Particles.masses_ = PropertyContainer._create_property_accessor("Mass_")

Particles.velocities  = PropertyContainer._create_property_accessor("Velocity", "The :py:class:`~ovito.data.Property` data array for the ``Velocity`` standard :ref:`particle property <particle-properties-list>`; or ``None`` if that property is undefined.")
Particles.velocities_ = PropertyContainer._create_property_accessor("Velocity_")

Particles.orientations  = PropertyContainer._create_property_accessor("Orientation", "The :py:class:`~ovito.data.Property` data array for the ``Orientation`` standard :ref:`particle property <particle-properties-list>`; or ``None`` if that property is undefined.")
Particles.orientations_ = PropertyContainer._create_property_accessor("Orientation_")

# Particle creation function.
def _Particles_add_particle(self, position: numpy.typing.ArrayLike) -> int:
    """
    Adds a new particle to the model. The particle :py:attr:`~ovito.data.PropertyContainer.count` will be incremented by one.
    The method assigns *position* to the ``Position`` property of the new particle. The values of all other properties
    are initialized to zero.

    :param position: The xyz coordinates for the new particle.
    :returns: The 0-based index of the newly created particle, which is :py:attr:`(Particles.count-1) <ovito.data.PropertyContainer.count>`.
    """
    assert len(position) == 3
    particle_index = self.count # Index of the newly created particle.

    # Extend the particles array by 1:
    self.count = particle_index + 1
    # Store the coordinates in the 'Position' particle property:
    self.create_property("Position")[particle_index] = position

    return particle_index
Particles.add_particle = _Particles_add_particle

# For backward compatibility with OVITO 3.7.3:
Particles.create_particle = lambda self, position: self.add_particle(position)

# Implementation of the Particles.delta_vector() method.
def _Particles_delta_vector(self,
                            a: Union[int, collections.abc.Sequence[int]],
                            b: Union[int, collections.abc.Sequence[int]],
                            cell: SimulationCell,
                            return_pbcvec: bool = False) -> Union[numpy.ndarray, tuple[numpy.ndarray, numpy.ndarray]]:
    """
    Computes the vector connecting two particles *a* and *b* in a periodic simulation cell by applying the minimum image convention.

    This is a convenience wrapper for the :py:meth:`SimulationCell.delta_vector() <ovito.data.SimulationCell.delta_vector>` method,
    which computes the vector between two arbitrary spatial locations :math:`r_a` and :math:`r_b` taking into account periodic
    boundary conditions. The version of the method described here takes two particle indices *a* and *b* as input, computing the shortest vector
    :math:`{\\Delta} = (r_b - r_a)` between them using the `minimum image convention <https://en.wikipedia.org/wiki/Periodic_boundary_conditions>`__.
    Please see the :py:meth:`SimulationCell.delta_vector() <ovito.data.SimulationCell.delta_vector>` method for further information.

    :param a: Zero-based index of the first input particle. This may also be an array of particle indices.
    :param b: Zero-based index of the second input particle. This may also be an array of particle indices with the same length as *a*.
    :param cell: The periodic domain. Typically, :py:attr:`DataCollection.cell <ovito.data.DataCollection.cell>` is used as argument here.
    :param return_pbcvec: If true, lets the method also return the vector :math:`n`, which specifies how often the computed particle-to-particle vector crosses the cell's face.
    :returns: The delta vector and, optionally, the vector :math:`n`.
    """
    return cell.delta_vector(self.positions[a], self.positions[b], return_pbcvec)
Particles.delta_vector = _Particles_delta_vector

# Implementation of the Particles.create_bonds() method.
def _Particles_create_bonds(self, *, vis_params: Optional[collections.abc.Mapping[str, Any]] = None, **params: Any) -> Bonds:
    """
    This convenience method conditionally creates and associates a :py:class:`Bonds` object with this :py:class:`Particles` parent object.
    If there is already an existing bonds object (:py:attr:`.bonds` is not ``None``), then that bonds object is
    replaced with a :ref:`modifiable copy <data_ownership>` if necessary. The attached :py:class:`~ovito.vis.BondsVis` element is preserved.

    :param params: Key-value pairs passed to the method as keyword arguments are used to set attributes of the :py:class:`Bonds` object (even if the bonds object already existed).
    :param vis_params: Optional dictionary to initialize attributes of the attached :py:class:`~ovito.vis.BondsVis` element (only used if the bonds object is newly created by the method).

    The logic of this method is roughly equivalent to the following code::

        def create_bonds(particles: Particles, vis_params=None, **params) -> Bonds:
            if particles.bonds is None:
                particles.bonds = Bonds()
                if vis_params:
                    for name, value in vis_params.items(): setattr(particles.bonds.vis, name, value)
            for name, value in params.items(): setattr(particles.bonds_, name, value)
            return particles.bonds_

    Usage example:

    .. literalinclude:: ../example_snippets/particles_create_bonds.py
       :lines: 8-10

    .. versionadded:: 3.7.4
    """
    return Bonds._create(self, params, vis_params)
Particles.create_bonds = _Particles_create_bonds

# Implementation of the Particles.create_angles() method.
def _Particles_create_angles(self, **kwargs):
    return Angles._create(self, **kwargs)
Particles.create_angles = _Particles_create_angles

# Implementation of the Particles.create_dihedrals() method.
def _Particles_create_dihedrals(self, **kwargs):
    return Dihedrals._create(self, **kwargs)
Particles.create_dihedrals = _Particles_create_dihedrals

# Implementation of the Particles.create_impropers() method.
def _Particles_create_impropers(self, **kwargs):
    return Impropers._create(self, **kwargs)
Particles.create_impropers = _Particles_create_impropers

# Implementation of the DataCollection.create_particles() method.
def _DataCollection_create_particles(self, *, vis_params: Optional[collections.abc.Mapping[str, Any]] = None, **params: Any) -> Particles:
    """
    This convenience method conditionally creates a new :py:class:`Particles` container object and stores it in this data collection.
    If the data collection already contains an existing particles object (:py:attr:`.particles` is not ``None``), then that particles object is
    replaced with a :ref:`modifiable copy <data_ownership>` if necessary. The associated :py:class:`~ovito.vis.ParticlesVis` element is preserved.

    :param params: Key-value pairs passed to the method as keyword arguments are used to set attributes of the :py:class:`Particles` object (even if the particles object already existed).
    :param vis_params: Optional dictionary to initialize attributes of the attached :py:class:`~ovito.vis.ParticlesVis` element (only used if the particles object is newly created by the method).

    The logic of this method is roughly equivalent to the following code::

        def create_particles(data: DataCollection, vis_params=None, **params) -> Particles:
            if data.particles is None:
                data.particles = Particles()
                if vis_params:
                    for name, value in vis_params.items(): setattr(data.particles.vis, name, value)
            for name, value in params.items(): setattr(data.particles_, name, value)
            return data.particles_

    Usage example:

    .. literalinclude:: ../example_snippets/data_collection_create_particles.py
       :lines: 8-12

    .. versionadded:: 3.7.4
    """
    return Particles._create(self, params, vis_params)
DataCollection.create_particles = _DataCollection_create_particles