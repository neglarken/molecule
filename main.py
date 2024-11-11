import animation
import atom
import constants

# открываем xyz файл для чтения и автоматически закрываем после
with open(constants.input_filename, "r") as input_file:
    atom_number = int(input_file.readline())
    molecule_name = input_file.readline()

    print(f"Атомов в молекуле: {atom_number}\nИмя молекулы: {molecule_name}")

    atoms = atom.read_from_lines(input_file.readlines())

# ищем количество связей в молекуле
bonds_number = atom.find_bonds_count(atoms)
print(f"В молекуле {bonds_number} связей.")

# ищем центр масс плоской молекулы (z = 0)
x_center, y_center = atom.find_mass_center(atoms)
print(f"Центр масс: x = {x_center} y = {y_center}")

# создаем и записываем анимацию вращения в файл
animation.make_animation(atoms)