"""
This Python module defines various data object types, which are produced and processed within OVITO's data pipeline system.
It also provides the :py:class:`DataCollection` class as a container for such data objects as well as several utility classes for
computing neighbor lists and iterating over the bonds of connected to a particle.

**Data containers:**

  * :py:class:`DataObject` - base of all data object types in OVITO
  * :py:class:`DataCollection` - a general container for data objects representing an entire dataset
  * :py:class:`PropertyContainer` - manages a set of uniform :py:class:`Property` arrays
  * :py:class:`Particles` - a specialized :py:class:`PropertyContainer` for particles
  * :py:class:`Bonds` - specialized :py:class:`PropertyContainer` for bonds
  * :py:class:`VoxelGrid` - specialized :py:class:`PropertyContainer` for 2d and 3d volumetric grids
  * :py:class:`DataTable` - specialized :py:class:`PropertyContainer` for tabulated data
  * :py:class:`Lines` - set of 3d line segments

**Data objects:**

  * :py:class:`Property` - uniform array of property values
  * :py:class:`SimulationCell` - simulation box geometry and boundary conditions
  * :py:class:`SurfaceMesh` - polyhedral mesh representing the boundaries of spatial regions
  * :py:class:`TriangleMesh` - general mesh structure made of vertices and triangular faces
  * :py:class:`DislocationNetwork` - set of discrete dislocation lines with Burgers vector information

**Auxiliary data objects:**

  * :py:class:`ElementType` - base class for type descriptors used in *typed properties*
  * :py:class:`ParticleType` - describes a single particle or atom type
  * :py:class:`BondType` - describes a single bond type

**Utility classes:**

  * :py:class:`CutoffNeighborFinder` - finds neighboring particles within a cutoff distance
  * :py:class:`NearestNeighborFinder` - finds *N* nearest neighbor particles
  * :py:class:`BondsEnumerator` - lets you efficiently iterate over the bonds connected to a particle

"""

__all__ = ['DataCollection', 'DataObject', 'TriangleMesh', 'AttributeDataObject']
