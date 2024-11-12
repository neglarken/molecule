"""This module deals with direct data exchange between the LAMMPS simulation code and OVITO.
The following function allows employing OVITO's data analysis and rendering functions
within a running molecular dynamics simulation.

  The function from this module is typically called from a Python script being executed
  in the context of a running LAMMPS simulation. Please install the ``ovito`` package
  in the Python interpreter used by your LAMMPS installation
  to make it available for import."""
__all__ = ['lammps_to_ovito']
from typing import Tuple, Optional, Any, Union, Iterator, Mapping, MutableMapping, Sequence, MutableSequence
import ovito.data
import lammps

def lammps_to_ovito(lmp: lammps.Lammps, data_collection: Optional[ovito.data.DataCollection]) -> ovito.data.DataCollection:
    """Constructs an OVITO :py:class:`DataCollection` from a LAMMPS simulation state.
This function should be called from within a running LAMMPS molecular dynamics simulation to
hand over the current particle model to OVITO and perform data analysis or visualization
tasks in regular time intervals, see the usage example below.

:param lmp: The LAMMPS Python object, which is used to by the function to access the particle data of the simulation.
:param data_collection: An existing :py:class:`DataCollection` to fill in with the particle model. A new data collection will be created if not provided.
:return: :py:class:`DataCollection` containing the converted particle data - only on rank 0 of a parallel LAMMPS simulation. On other ranks, the function returns ``None``.

.. caution::

   This function is still under active development and should be considered as experimental.
   Only the simulation cell geometry, boundary conditions, and particle coordinates are
   converted from LAMMPS to the OVITO representation. Please `contact the OVITO developers <https://www.ovito.org/forum/>`__
   if you require more particle properties to be transferred from LAMMPS for your specific
   application.

Usage example:

In the LAMMPS simulation script, include the following `python` and `fix python/invoke` commands to
load the following Python script into the context of the LAMMPS simulation and invoke
the ``perform_dxa()`` function in regular timestep intervals during the MD run:

.. code-block:: none

  python perform_dxa source perform_dxa.py
  fix 1 all python/invoke 1000 end_of_step perform_dxa

The following script file, :file:`perform_dxa.py`, defines the Python function to be executed every
1000 timesteps. It runs OVITO's :py:class:`DislocationAnalysisModifier`
on the current simulation snapshot to identify all dislocation defects in the crystal::

    from lammps import lammps
    from ovito.io.lammps import lammps_to_ovito
    from ovito.io import export_file
    from ovito.modifiers import DislocationAnalysisModifier

    def perform_dxa(lammps_ptr):

        # Access the LAMMPS simulation state.
        lmp = lammps(ptr=lammps_ptr)

        # Convert simulation state to OVITO data representation.
        data = lammps_to_ovito(lmp)

        # Let OVITO perform data analysis only on MPI rank 0. Do nothing on other processors.
        if data is None:
            return

        # Run DXA.
        data.apply(DislocationAnalysisModifier(input_crystal_structure=DislocationAnalysisModifier.Lattice.FCC))

        # Output total length of all dislocation lines.
        total_line_length = data.attributes['DislocationAnalysis.total_line_length']
        print('Total dislocation line length:', total_line_length)

        # Dump dislocation lines to a CA file for later visualization in the OVITO desktop application.
        timestep = int(lmp.get_thermo('step'))
        export_file(data, f'dislocations.{timestep}.ca', format='ca')"""
    ...