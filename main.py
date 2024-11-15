import ovito.io
from ovito.modifiers import CreateBondsModifier, ClusterAnalysisModifier, CalculateDisplacementsModifier, AffineTransformationModifier
from ovito.vis import Viewport
import math
import numpy as np

if __name__ == '__main__':
    num_frames = 100  # Количество кадров в анимации
    rotation_angle_per_frame_z = 360 / num_frames  # Угол вращения по оси Z на кадр (в градусах)

    # читаем файл .xyz с исходной молекулой
    pipeline = ovito.io.import_file("20.xyz")

    # создаем модификатор поиска связей
    bond_modifier = CreateBondsModifier()
    # устанавливаем режим поиска на пары атомов
    bond_modifier.mode = CreateBondsModifier.Mode.Pairwise
    bond_modifier.set_pairwise_cutoff("C", "C", 1.6) # расстояние между атомами С и С - 1.6
    bond_modifier.set_pairwise_cutoff("C", "H", 1.1) # расстояние между атомами С и Н - 1.1
    bond_modifier.set_pairwise_cutoff("C", "O", 1.5) # расстояние между атомами С и О - 1.5
    bond_modifier.set_pairwise_cutoff("O", "H", 1.0) # расстояние между атомами О и Н - 1.0

    # создаем модификатор анализа кластеров
    # модификатор анализа кластеров позволяет найти центр масс молекулы, который нам необходим
    cluster_analysis_modifier = ClusterAnalysisModifier(compute_com=True)

    # создаем модификатор расчета смещений атомов
    calculate_displacements_modifier = CalculateDisplacementsModifier()
    calculate_displacements_modifier.vis.enabled = False # удаляем стрелки координат x, y, z из кадра

    # функция движения молекулы в пространстве
    # frame - текущий кадр
    def rotate(frame, data):
        # frame * 5.0 - угол в градусах, где угол увеличивается на 5 градусов с каждым новым кадром
        theta = np.deg2rad(frame * 5.0) # угол поворота, который вычисляется для текущего кадра в радианах

        # tm - матрица трансформации
        tm = [
            [np.cos(theta), 0, np.sin(theta), 0], # создание вращения вокруг оси y
            [0, 1, 0, 0], # остается неизменным, так как ось y не поворачивается вокруг самой себя
            [-np.sin(theta), 0, np.cos(theta), 0] # создание вращения вокруг оси y
        ]

        # применяем модификатор трансформации к молекуле на текущем кадре
        data.apply(AffineTransformationModifier(transformation=tm))

    pipeline.modifiers.append(bond_modifier) # применяем модификатор поиска связей
    pipeline.modifiers.append(cluster_analysis_modifier) # применяем модификатор анализа кластеров
    pipeline.modifiers.append(calculate_displacements_modifier) # применяем модификатор расчета смещений атомов
    pipeline.modifiers.append(rotate) # применяем модификатор смещения молекулы в пространстве
    pipeline.add_to_scene() # добавляем молекулу и все модификаторы (пайплайн) на сцену

    data = pipeline.compute() # вызываем вычисление пайплайна

    particles_property = data.particles # переменная для хранения атомов

    type_property = particles_property.particle_types # переменная для хранения типов атомов

    cluster_table = data.tables['clusters'] # переменная для хранения таблицы анализа кластеров

    # итерируемся по атомам
    for i in range(particles_property.count):
        particle_type = type_property.type_by_id(type_property[i]).name # получаем тип атома
        particle_position = particles_property.positions[i] # получаем координаты атома

        print(f"Атом {particle_type} на координатах: {particle_position}") # выводим в консоль тип и координаты атома

    print(f"Количество атомов: {particles_property.count}") # выводим в консоль количество атомов
    print(f"Количество связей в молекуле: {data.particles.bonds.count}") # выводим в консоль количество связей в молекуле
    print(f"Центр масс: {cluster_table['Center of Mass'][...]}") # выводим в консоль центр масс молекулы из таблицы анализа кластеров

    vp = Viewport() # создаем камеру
    vp.type = Viewport.Type.Ortho # настраиваем точку обзора на произвольный
    vp.camera_pos = (0, -30, 30) # настраиваем позицию камеры (координаты)
    vp.camera_dir = (0, 1, -1) # настраиваем направление камеры, чтобы она смотрела на молекулу
    vp.fov = math.radians(1000) # отдаляем камеру, чтобы было видно всю молекулу

    vp.render_anim(size=(800, 600), filename="animation.mp4", range=(0,num_frames), fps=8) # рендерим видео с анимацией