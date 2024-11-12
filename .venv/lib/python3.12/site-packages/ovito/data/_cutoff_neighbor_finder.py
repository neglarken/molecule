from __future__ import annotations
from collections.abc import Iterator
import ovito.nonpublic
from . import DataCollection
import numpy
import numpy.typing
import typing
from typing import Optional

class CutoffNeighborFinder(ovito.nonpublic.CutoffNeighborFinder):
    """
    A utility class that computes particle neighbor lists.

    This class lets you iterate over all neighbors of a particle that are located within a specified spherical cutoff.
    You can use it to build neighbor lists or perform computations that require neighbor vector information.

    The constructor takes a positive cutoff radius and a :py:class:`DataCollection <ovito.data.DataCollection>`
    providing the input particles and the :py:class:`~ovito.data.SimulationCell` (needed for periodic systems).

    Once the :py:class:`!CutoffNeighborFinder` has been constructed, you can call its :py:meth:`.find` method to
    iterate over the neighbors of a particle, for example:

    .. literalinclude:: ../example_snippets/cutoff_neighbor_finder.py

    Note: In case you rather want to determine the *N* nearest neighbors of a particle,
    use the :py:class:`NearestNeighborFinder` class instead.
    """

    def __init__(self, cutoff: float, data_collection: DataCollection) -> None:
        """This is the constructor."""
        super(self.__class__, self).__init__()
        assert isinstance(data_collection, DataCollection)
        if (
            data_collection.particles is None
            or data_collection.particles.positions is None
        ):
            raise KeyError("DataCollection does not contain any particles.")
        pos_property = data_collection.particles.positions
        self.particle_count = len(pos_property)
        self.prepare(cutoff, pos_property, data_collection.cell)

    def find(self, index: int) -> Iterator:
        """
        Returns an iterator over all neighbors of the given particle.

        :param index: The zero-based index of the central particle whose neighbors should be enumerated.
        :returns: A Python iterator that visits all neighbors of the central particle within the cutoff distance.
                  For each neighbor the iterator returns an object with the following property fields:

                      * **index**: The zero-based global index of the current neighbor particle.
                      * **distance**: The distance of the current neighbor from the central particle.
                      * **distance_squared**: The squared neighbor distance.
                      * **delta**: The three-dimensional vector connecting the central particle with the current neighbor (taking into account periodicity).
                      * **pbc_shift**: The periodic shift vector, which specifies how often each periodic boundary of the simulation cell is crossed when going from the central particle to the current neighbor.

        The `index` value returned by the iterator can be used to look up properties of the neighbor particle, as demonstrated in the example above.

        Note that all periodic images of particles within the cutoff radius are visited. Thus, the same particle index may appear multiple times in the neighbor
        list of the central particle. In fact, the central particle may be among its own neighbors in a small periodic simulation cell.
        However, the computed vector (``delta``) and PBC shift (``pbc_shift``) will be unique for each visited image of the neighbor particle.
        """
        if index < 0 or index >= self.particle_count:
            raise IndexError("Particle index is out of range.")
        # Construct the C++ neighbor query.
        query = ovito.nonpublic.CutoffNeighborFinder.Query(self, int(index))
        # Iterate over neighbors.
        while not query.at_end:
            yield query
            query.next()

    def find_at(self, coords: numpy.typing.ArrayLike) -> Iterator:
        """
        Returns an iterator over all particles located within the spherical range of the given center position. In contrast to :py:meth:`find` this method can search for neighbors around arbitrary
        spatial locations, which don't have to coincide with any physical particle position.

        :param coords: A (x,y,z) coordinate triplet specifying the center location around which to search for particles.
        :returns: A Python iterator enumerating all particles within the cutoff distance.
                  For each neighbor the iterator returns an object with the following properties:

                      * **index**: The zero-based global index of the current neighbor particle.
                      * **distance**: The distance of the current particle from the center position.
                      * **distance_squared**: The squared distance.
                      * **delta**: The three-dimensional vector from the center to the current neighbor (taking into account periodicity).
                      * **pbc_shift**: The periodic shift vector, which specifies how often each periodic boundary of the simulation cell is crossed when going from the center point to the current neighbor.

        The index value returned by the iterator can be used to look up properties of the neighbor particle, as demonstrated in the example above.

        Note that all periodic images of particles within the cutoff radius are visited. Thus, the same particle index may appear multiple times in the neighbor list.
        However, the computed vector (``delta``) and image offset (``pbc_shift``) will be unique for each visited image of a neighbor particle.
        """
        # Construct the C++ neighbor query.
        query = ovito.nonpublic.CutoffNeighborFinder.Query(self, coords)
        # Iterate over neighbors.
        while not query.at_end:
            yield query
            query.next()

    def find_all(self, indices: Optional[numpy.typing.ArrayLike]=None, sort_by: Optional[typing.Literal['index', 'distance']]=None) -> tuple[numpy.typing.NDArray[numpy.int64], numpy.typing.NDArray[numpy.float32]]:
        """
        This is a vectorized version of the :py:meth:`find` method, computing the neighbor lists and neighbor vectors of several particles in a single operation.
        Thus, this method can help you avoid a slow, nested Python loop in your code and it will make use of all available processor cores.
        You can request the neighbor lists for the whole system in one go, or just for a specific subset of particles given by *indices*.

        The method produces a uniform array of neighbor list entries. Each entry comprises a pair of indices, i.e. the central particle and one of its neighboring particles within the cutoff distance,
        and the corresponding spatial neighbor vector in 3d Cartesian coordinates. For best performance, the method returns all neighbors of all particles as one large
        array, which is unsorted by default (*sort_by* = ``None``). That means the neighbors of central particles will *not* form contiguous blocks in the output array;
        entries belonging to different central particles may rather appear in intermingled order!

        Set *sort_by* to ``'index'`` to request grouping the entries in the output array based on the central particle index.
        That means each particle's neighbor list will be output as a contiguous block. All blocks are stored back-to-back in the output array
        in ascending order of the central particle index or, if parameter *indices* was specified, in that order.
        The ordering of neighbor entries within each block will still be arbitrary though. To change this, set *sort_by* to ``'distance'``, which additionally
        sorts the neighbors of each particle by increasing distance.

        The method returns two NumPy arrays:

        ``neigh_idx`` : Array of shape (*M*, *2*) containing pairs of indices of neighboring particles, with *M* equal to the
        total number of neighbors in the system. Note that the array will contain symmetric entries (*a*, *b*) and (*b*, *a*) if
        neighbor list computation was requested for both particles *a* and *b* and they are within reach of each other.

        ``neigh_vec`` : Array of shape (*M*, 3) containing the xyz components of the Cartesian neighbor vectors ("delta"),
        which connect the *M* particle pairs stored in ``neigh_idx``.

        :param indices: List of zero-based indices of central particles for which the neighbor lists should be computed.
                        If left unspecified, neighbor lists will be computed for every particle in the system.
        :param sort_by: One of *"index"* or *"distance"*. Requests ordering of the output arrays based on central particle index and, optionally, neighbor distance.
                        If left unspecified, neighbor list entries will be returned in arbitrary order.

        :returns: ``(neigh_idx, neigh_vec)``

        .. tip:: Sorting of neighbor lists will incur an additional runtime cost and should only be requested if necessary.
                 In any case, however, this vectorized method will be much faster than an equivalent Python for-loop invoking the
                 :py:meth:`find` method for each individual particle.


        .. attention::

            The same index pair (*a*, *b*) may appear multiple times in the list ``neigh_idx`` if the :py:class:`~ovito.data.SimulationCell` uses periodic boundary
            conditions and its size is smaller than twice the neighbor cutoff radius. Note that, in such a case, the corresponding neighbor vectors in ``neigh_vec``
            will still be unique, because they are computed for each periodic image of the neighbor *b*.

        .. versionadded:: 3.8.1

        """
        if sort_by:
            if sort_by.lower() == "index":
                return super().find_all_sorted(indices, False)
            elif sort_by.lower() == "distance":
                return super().find_all_sorted(indices, True)
            else:
                raise ValueError(
                    f'sort_by must be either "index" or "distance", not "{sort_by}".'
                )
        else:
            return super().find_all(indices)

    # Inherit method neighbor_distances() from C++ base class.
    neighbor_distances = ovito.nonpublic.CutoffNeighborFinder.neighbor_distances

    # Inherit method neighbor_vectors() from C++ base class.
    neighbor_vectors = ovito.nonpublic.CutoffNeighborFinder.neighbor_vectors


ovito.data.CutoffNeighborFinder = CutoffNeighborFinder
