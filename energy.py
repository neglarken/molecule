import numpy as np
from ovito import data

def get_bonds(particles: data.Particles) -> list[tuple[int, int]]:
    res = list()

    for a_tpl, b_tpl in particles.bonds.topology:
        a_id = particles.particle_types[a_tpl]
        b_id = particles.particle_types[b_tpl]

        res.append((a_id, b_id))

    return res


def calculate_bond_energy_by_length(data_collection: data.DataCollection) -> float:
    """
        Вычисляет энергию молекулы на основе взаимодействия ван-дер-Ваальса.

        :param data_collection: Объект данных OVITO, содержащий позиции атомов и их типы.
        :return: Суммарная энергия взаимодействия связей.
        """

    bond_k = 500.0  # Гармоническая константа для связи (кДж/моль/Å^2)

    bond_lengths = {
        ("C", "H"): 1.1,
        ("H", "C"): 1.1,
        ("C", "C"): 1.6,
        ("C", "O"): 1.5,
        ("O", "C"): 1.5,
        ("O", "H"): 1.0,
        ("H", "O"): 1.0,
    }

    bonds = get_bonds(data_collection.particles)

    positions = data_collection.particles.positions

    energy = 0.0

    for bond in bonds:
        atom1_id, atom2_id = bond
        r = np.linalg.norm(positions[atom1_id] - positions[atom2_id])

        atom_types = sorted([data_collection.particles.particle_types.type_by_id(atom1_id).name,
                             data_collection.particles.particle_types.type_by_id(atom2_id).name])

        pair = tuple(atom_types)

        if pair in bond_lengths:
            r0 = bond_lengths[pair]
            energy += 0.5 * bond_k * (r - r0)**2

    return energy


def calculate_vdw_energy(data_collection: data.DataCollection) -> float:
    """
    Вычисляет энергию молекулы на основе взаимодействия ван-дер-Ваальса.

    :param data_collection: Объект данных OVITO, содержащий позиции атомов и их типы.
    :return: Суммарная энергия взаимодействия ван-дер-Ваальса.
    """
    # Константы Леннард-Джонса для различных типов атомов
    vdw_params = {
        ("C", "H"): {"epsilon": 0.035, "sigma": 1.32},
        ("H", "C"): {"epsilon": 0.035, "sigma": 1.32},
        ("C", "C"): {"epsilon": 0.05, "sigma": 1.92},
        ("C", "O"): {"epsilon": 0.06, "sigma": 1.8},
        ("O", "C"): {"epsilon": 0.06, "sigma": 1.8},
        ("O", "H"): {"epsilon": 0.045, "sigma": 1.2},
        ("H", "O"): {"epsilon": 0.045, "sigma": 1.2},
    }

    # Получение позиций атомов
    positions = data_collection.particles.positions

    # Инициализация энергии
    energy = 0.0

    bonds = get_bonds(data_collection.particles)

    for bond in bonds:
        atom1_id, atom2_id = bond
        r = np.linalg.norm(positions[atom1_id] - positions[atom2_id])

        # Получаем типы атомов
        atom_types = sorted([
            data_collection.particles.particle_types.type_by_id(atom1_id).name,
            data_collection.particles.particle_types.type_by_id(atom2_id).name
        ])
        pair = tuple(atom_types)

        # Проверяем, есть ли параметры ван-дер-Ваальса для данной пары
        if pair in vdw_params:
            epsilon = vdw_params[pair]['epsilon']
            sigma = vdw_params[pair]['sigma']

            # Вычисляем потенциал Леннард-Джонса
            if r > 0:
                r6 = (sigma / r) ** 6
                r12 = r6 ** 2
                energy += 4 * epsilon * (r12 - r6)

    return energy
