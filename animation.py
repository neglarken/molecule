import os.path
import numpy as np
import constants
from atom import Atom

# функция для вращения координат относительно оси z
def rotate_z(x: float, y: float, z: float, angle_deg: float):
    angle_rad = np.radians(angle_deg) # преобразует угол в градусах в радианы
    cos_a, sin_a = np.cos(angle_rad), np.sin(angle_rad) # вычисление углов
    x_new = cos_a * x - sin_a * y # матрица поворота
    y_new = sin_a * x + cos_a * y # матрица поворота
    return x_new, y_new, z

# вращаем молекулу и записываем каждый кадр в отдельный файл
def make_animation(atoms: list[Atom]):
    # если папки нет - создаем
    if not os.path.exists(constants.output_directory):
        os.makedirs(constants.output_directory)

    for frame in range(constants.frames_count):
        path = os.path.join("animation", f"{constants.output_filename}_{frame}.xyz")

        # вращаем и поднимаем атом относительно оси z и записываем в файл
        with open(path, 'w') as out_file:
            frame_data = [f"{constants.frames_count}\n{frame}\n"]
            angle = frame * constants.angle_increment

            for atom in atoms:
                atom.z += 0.5
                x_rot, y_rot, z_rot = rotate_z(atom.x, atom.y, atom.z, angle)
                frame_data.append(f"{atom.type} {x_rot:.2f} {y_rot:.2f} {z_rot:.2f}\n")

            out_file.writelines(frame_data)