"""This module provides functions for direct data exchange with the ASE (`Atomistic Simulation Environment <https://wiki.fysik.dtu.dk/ase/>`__).
It contains two high-level functions for converting atomistic data back and forth between
the representations of OVITO and ASE:

    * :py:func:`ovito_to_ase`
    * :py:func:`ase_to_ovito`

    The functions of this module will raise an ``ImportError`` if the ASE package
    is not installed in the current Python interpreter. The embedded
    Python interpreter of OVITO Pro does *not* include the ASE package by default.
    You can install the ASE module by running ``ovitos -m pip install ase`` if you are using the embedded Python interpreter of OVITO Pro.
    Alternatively, if you installed the ``ovito`` module in your own Python interpreter,
    simply run ``pip3 install ase`` to make the ASE package available."""
__all__ = ['ovito_to_ase', 'ase_to_ovito']
from typing import Tuple, Optional, Any, Union, Iterator, Mapping, MutableMapping, Sequence, MutableSequence
import ovito.data
import ase

def ase_to_ovito(atoms: ase.Atoms, data_collection: Optional[ovito.data.DataCollection]) -> ovito.data.DataCollection:
    """Converts an `ASE Atoms object <https://wiki.fysik.dtu.dk/ase/ase/atoms.html>`__ to an OVITO :py:class:`DataCollection`.

:param atoms: The `ASE Atoms object <https://wiki.fysik.dtu.dk/ase/ase/atoms.html>`__ to be converted.
:param data_collection: An existing :py:class:`DataCollection` to fill in with the atoms model. A new data collection will be created if not provided.
:return: The data collection containing the converted atoms data.

Usage example:

```python
  from ovito.pipeline import StaticSource, Pipeline
  from ovito.io.ase import ase_to_ovito
  from ase.atoms import Atoms
  
  # The ASE Atoms object to convert:
  ase_atoms = Atoms('CO', positions=[(0, 0, 0), (0, 0, 1.1)])
  
  # Convert the ASE object to an OVITO DataCollection:
  data = ase_to_ovito(ase_atoms)
  
  # We may now create a Pipeline object with a StaticSource and use the 
  # converted dataset as input for a data pipeline:
  pipeline = Pipeline(source = StaticSource(data = data))
```"""
    ...

def ovito_to_ase(data_collection: ovito.data.DataCollection) -> ase.Atoms:
    """Constructs an `ASE Atoms object <https://wiki.fysik.dtu.dk/ase/ase/atoms.html>`__ from the
particle data in an OVITO :py:class:`DataCollection`.

:param data_collection: The OVITO :py:class:`DataCollection` to convert.
:return: An `ASE Atoms object <https://wiki.fysik.dtu.dk/ase/ase/atoms.html>`__ containing the
         converted particle data from the source :py:class:`DataCollection`.

Usage example:

```python
  from ovito.io import import_file
  from ovito.io.ase import ovito_to_ase
  
  # Create an OVITO data pipeline from an external file:
  pipeline = import_file('input/simulation.dump')
  
  # Evaluate pipeline to obtain a DataCollection:
  data = pipeline.compute()
  
  # Convert it to an ASE Atoms object:
  ase_atoms = ovito_to_ase(data)
```"""
    ...