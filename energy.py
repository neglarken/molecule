import numpy as np
from ovito import data

# Константы Леннард-Джонса для различных типов атомов
vdw_params = {
    ("C", "H"): {"epsilon": 0.035, "sigma": 1.32},  # Углерод-водород
    ("H", "C"): {"epsilon": 0.035, "sigma": 1.32},  # Водород-углерод
    ("C", "C"): {"epsilon": 0.05, "sigma": 1.92},   # Углерод-углерод
    ("C", "O"): {"epsilon": 0.06, "sigma": 1.8},    # Углерод-кислород
    ("O", "C"): {"epsilon": 0.06, "sigma": 1.8},    # Кислород-углерод
    ("O", "H"): {"epsilon": 0.045, "sigma": 1.2},   # Кислород-водород
    ("H", "O"): {"epsilon": 0.045, "sigma": 1.2},   # Водород-кислород
}

def get_bonds(particles: data.Particles) -> list[tuple[int, int]]:
    """
    Получить список всех связей между атомами.

    :param particles: Объект Particles из OVITO.
    :return: Список кортежей, каждый из которых представляет связь (индексы атомов).
    """
    res = list()

    for a_tpl, b_tpl in particles.bonds.topology:
        # Извлекаем индексы атомов, связанных данной связью
        a_id = particles.particle_types[a_tpl]
        b_id = particles.particle_types[b_tpl]

        # Добавляем связь в список
        res.append((a_id, b_id))

    return res


def build_atom_tree(data_collection: data.DataCollection, root_atom_index: int):
    """
    Построить дерево атомов, начиная с заданного атома, используя BondsEnumerator.

    :param data_collection: DataCollection из OVITO.
    :param root_atom_index: Индекс корневого атома.
    :return: Дерево в виде вложенного словаря.
    """
    # Получаем объект BondsEnumerator для итерации по связям
    bonds = data_collection.particles.bonds
    if bonds is None:
        raise ValueError("Молекула не содержит информации о связях (Bonds).")

    bond_topology = data_collection.particles.bonds.topology
    enumerator = data.BondsEnumerator(bonds)

    def traverse(atom_index, visited):
        """
        Рекурсивно строит дерево атомов.

        :param atom_index: Индекс текущего атома.
        :param visited: Множество посещённых атомов.
        :return: Поддерево с текущим атомом как корнем.
        """
        visited.add(atom_index)  # Отмечаем текущий атом как посещённый

        tree = {"atom": atom_index, "neighbors": []}  # Узел дерева

        for bond_index in enumerator.bonds_of_particle(atom_index):  # Перебор связей текущего атома
            a_id = bond_topology[bond_index, 0]
            b_id = bond_topology[bond_index, 1]

            # Определяем индекс соседнего атома
            neighbor_index = b_id if a_id == atom_index else a_id

            if neighbor_index not in visited:  # Избегаем зацикливания
                subtree = traverse(neighbor_index, visited)  # Рекурсивно строим поддерево
                tree["neighbors"].append(subtree)

        return tree

    visited_atoms = set()
    atom_tree = traverse(root_atom_index, visited_atoms)  # Построение дерева с корня
    return atom_tree


def find_neighbors_of_order(tree: dict[str, list], order=3):
    """
    Находит соседей заданного порядка и выше для указанного атома в дереве.

    :param tree: Дерево атомов в виде словаря (результат build_atom_tree).
    :param order: Минимальный порядок соседства (например, 3 для соседей 3-го порядка).
    :return: Список индексов соседей заданного порядка и выше.
    """
    neighbors = []

    def traverse(subtree, depth):
        """
        Рекурсивный обход дерева для поиска соседей.

        :param subtree: Текущее поддерево.
        :param depth: Текущая глубина относительно корневого атома.
        """
        if depth >= order + 1:  # Добавляем атомы с глубиной >= заданного порядка
            neighbors.append(subtree["atom"])

        for neighbor in subtree["neighbors"]:  # Обходим соседей
            traverse(neighbor, depth + 1)

    traverse(tree, depth=1)  # Начинаем с корня
    return neighbors


def calculate_bond_energy_by_length(data_collection: data.DataCollection) -> float:
    """
    Вычисляет энергию молекулы на основе взаимодействия связей.

    :param data_collection: Объект данных OVITO, содержащий позиции атомов и их типы.
    :return: Суммарная энергия взаимодействия связей.
    """
    bond_k = 500.0  # Гармоническая константа для связи (кДж/моль/Å^2)

    bond_lengths = {
        ("C", "H"): 1.1, ("H", "C"): 1.1,  # Длина связи углерод-водород
        ("C", "C"): 1.6,                  # Длина связи углерод-углерод
        ("C", "O"): 1.5, ("O", "C"): 1.5,  # Длина связи углерод-кислород
        ("O", "H"): 1.0, ("H", "O"): 1.0,  # Длина связи кислород-водород
    }

    positions = data_collection.particles.positions
    type_property = data_collection.particles.particle_types

    energy = 0.0
    bonds = get_bonds(data_collection.particles)

    for bond in bonds:
        atom1_id, atom2_id = bond
        r = np.linalg.norm(positions[atom1_id] - positions[atom2_id])  # Расстояние между атомами

        # Определяем типы атомов
        particle_type_i = type_property.type_by_id(type_property[atom1_id]).name
        particle_type_j = type_property.type_by_id(type_property[atom2_id]).name

        atom_types = sorted([particle_type_i, particle_type_j])
        pair = tuple(atom_types)

        if pair in bond_lengths:  # Вычисление энергии по гармоническому потенциалу
            r0 = bond_lengths[pair]
            energy += 0.5 * bond_k * (r - r0) ** 2

    return energy


def calculate_vdw_energy(data_collection: data.DataCollection) -> float:
    """
    Вычисляет энергию молекулы на основе взаимодействия ван-дер-Ваальса.

    :param data_collection: Объект данных OVITO, содержащий позиции атомов и их типы.
    :return: Суммарная энергия взаимодействия ван-дер-Ваальса.
    """
    positions = data_collection.particles.positions
    type_property = data_collection.particles.particle_types

    energy = 0.0

    for i_id in range(data_collection.particles.count):  # Для каждого атома
        tree = build_atom_tree(data_collection, i_id)  # Построение дерева соседей
        neighbors = find_neighbors_of_order(tree, 3)  # Соседи 3-го порядка

        for j_id in neighbors:
            r = np.linalg.norm(positions[i_id] - positions[j_id])  # Расстояние между атомами

            # Определяем типы атомов
            particle_type_i = type_property.type_by_id(type_property[i_id]).name
            particle_type_j = type_property.type_by_id(type_property[j_id]).name

            atom_types = sorted([particle_type_i, particle_type_j])
            pair = tuple(atom_types)

            if pair in vdw_params:  # Если параметры Леннард-Джонса заданы
                epsilon = vdw_params[pair]['epsilon']
                sigma = vdw_params[pair]['sigma']

                if r > 0:
                    r6 = (sigma / r) ** 6
                    r12 = r6 ** 2
                    energy += 4 * epsilon * (r12 - r6)  # Потенциал Леннард-Джонса

    return energy


def total_energy(data_collection: data.DataCollection) -> float:
    """
    Вычисляет общую энергию молекулы как сумму энергии связей и ван-дер-Ваальса.

    :param data_collection: Объект данных OVITO.
    :return: Общая энергия молекулы.
    """
    return calculate_bond_energy_by_length(data_collection) + calculate_vdw_energy(data_collection)
