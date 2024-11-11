import math

bond_distance_dict = {
    ("C", "C"): 1.6,
    ("C", "H"): 1.1,
    ("H", "C"): 1.1,
    ("C", "O"): 1.5,
    ("O", "C"): 1.5,
    ("O", "H"): 1.0,
    ("H", "O"): 1.0
}

mass_dict = {
    "C": 12.0, # масса углерода
    "H": 1.0, # масса водорода
    "O": 16.0 # масса кислорода
}

# класс атома
class Atom:
    # Инициализация атома с типом и координатами x, y, z.
    def __init__(self, atom_type: str, x: str, y: str, z: str):
        self.type = atom_type  # Тип атома, например "C" или "H"
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)
        self.mass = mass_dict[atom_type]

    # Вычисление расстояния до другого атома.
    def distance_to(self, other):
        return math.sqrt((self.x - other.x) ** 2 +
                         (self.y - other.y) ** 2 +
                         (self.z - other.z) ** 2)

    def is_bonded_to(self, other) -> bool:
        if (self.type, other.type) not in bond_distance_dict:
            return False

        bond_distance = bond_distance_dict[(self.type, other.type)]
        if self.distance_to(other) < bond_distance:
            return True

        bond_distance = bond_distance_dict[(other.type, self.type)]
        if self.distance_to(other) < bond_distance:
            return True

        return False

    # Представление атома в виде строки.
    def __repr__(self):
        return f"{self.type} {self.x} {self.y} {self.z}"

def read_from_lines(lines: list[str]) -> list[Atom]:
    # записываем атомы и их координаты в список atoms
    atoms = []
    for line in lines:
        splited_line = line.split()

        # создаем объект класса Atom и добавляем его в список
        atoms.append(Atom(
            atom_type=splited_line[0],
            x=splited_line[1],
            y=splited_line[2],
            z=splited_line[3],
        ))

    return atoms

def find_mass_center(atoms: list[Atom]):
    x = 0
    y = 0
    mass = 0

    for atom in atoms:
        x += atom.x * atom.mass
        y += atom.y * atom.mass
        mass += atom.mass

    return x/mass, y/mass

def find_bonds_count(atoms: list[Atom]) -> int:
    # счетчик количества связей в молекуле
    bonds_number = 0
    atom_number = len(atoms)

    for i in range(atom_number):
        atom_1 = atoms[i]
        for j in range(i + 1, atom_number):
            atom_2 = atoms[j]

            if atom_1.is_bonded_to(atom_2):
                bonds_number += 1

    return bonds_number