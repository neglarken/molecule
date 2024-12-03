# Пакет ovito.io используется для работы с файлами, включая импорт данных из симуляций молекулярной динамики.
import ovito.io

# Импортируем необходимые модификаторы из пакета ovito.modifiers:
# - CreateBondsModifier: для создания связей между частицами на основе расстояния.
# - ClusterAnalysisModifier: для выполнения кластерного анализа, в данном случае для расчёта центра масс молекулы.
# - CalculateDisplacementsModifier: для расчёта смещений частиц.
# - AffineTransformationModifier: для применения аффинных преобразований (например, вращения).
from ovito.modifiers import CreateBondsModifier, ClusterAnalysisModifier, CalculateDisplacementsModifier, \
    AffineTransformationModifier

# Viewport используется для настройки визуализации сцены, например, камеры и её параметров.
from ovito.vis import Viewport

# Импортируем дополнительные библиотеки для математических вычислений и работы с массивами.
import math
import numpy as np

if __name__ == '__main__':
    # Количество кадров в анимации.
    num_frames = 100

    # Угол вращения молекулы по оси Z в каждом кадре (в градусах).
    rotation_angle_per_frame_z = 360 / num_frames

    # Загружаем входной файл в формате .xyz с молекулярной структурой.
    # Pipeline в OVITO — это последовательность шагов (модификаторов), которые
    # применяются к данным, загруженным из симуляции.
    pipeline = ovito.io.import_file("20.xyz")

    # Создаём модификатор для генерации связей между атомами.
    bond_modifier = CreateBondsModifier()

    # Устанавливаем режим модификатора для создания связей между парами частиц.
    bond_modifier.mode = CreateBondsModifier.Mode.Pairwise

    # Задаём предельные расстояния для создания связей между различными типами атомов.
    bond_modifier.set_pairwise_cutoff("C", "C", 1.6)  # Связь между атомами углерода.
    bond_modifier.set_pairwise_cutoff("C", "H", 1.1)  # Связь между углеродом и водородом.
    bond_modifier.set_pairwise_cutoff("C", "O", 1.5)  # Связь между углеродом и кислородом.
    bond_modifier.set_pairwise_cutoff("O", "H", 1.0)  # Связь между кислородом и водородом.

    # Создаём модификатор для кластерного анализа.
    # В данном случае он используется для вычисления центра масс молекулы.
    cluster_analysis_modifier = ClusterAnalysisModifier(compute_com=True)

    # Создаём модификатор для расчёта смещений частиц между кадрами.
    calculate_displacements_modifier = CalculateDisplacementsModifier()

    # Отключаем визуализацию смещений (например, стрелки).
    calculate_displacements_modifier.vis.enabled = False


    # Функция для вращения молекулы в пространстве.
    def rotate(frame, data):
        # Вычисляем угол вращения для текущего кадра в радианах.
        theta = np.deg2rad(frame * 5.0)

        # Определяем матрицу трансформации для вращения вокруг оси Y.
        tm = [
            [np.cos(theta), 0, np.sin(theta), 0],  # X-координата после вращения.
            [0, 1, 0, 0],  # Y-координата остаётся неизменной.
            [-np.sin(theta), 0, np.cos(theta), 0]  # Z-координата после вращения.
        ]

        # Применяем модификатор трансформации с заданной матрицей.
        data.apply(AffineTransformationModifier(transformation=tm))


    # Добавляем модификаторы в конвейер обработки данных.
    pipeline.modifiers.append(bond_modifier)  # Модификатор для создания связей.
    pipeline.modifiers.append(cluster_analysis_modifier)  # Модификатор для анализа кластеров.
    pipeline.modifiers.append(calculate_displacements_modifier)  # Модификатор для расчёта смещений.
    pipeline.modifiers.append(rotate)  # Функция вращения молекулы.

    # Добавляем весь конвейер (пайплайн) на сцену для визуализации.
    pipeline.add_to_scene()

    # Выполняем вычисление всех шагов конвейера.
    data = pipeline.compute()

    # Получаем данные о частицах (атомах).
    particles_property = data.particles

    # Получаем информацию о типах частиц.
    type_property = particles_property.particle_types

    # Получаем таблицу результатов кластерного анализа.
    cluster_table = data.tables['clusters']

    # Проходим по всем атомам и выводим их тип и координаты.
    for i in range(particles_property.count):
        particle_type = type_property.type_by_id(type_property[i]).name  # Тип атома.
        particle_position = particles_property.positions[i]  # Координаты атома.

        # Выводим информацию о каждом атоме.
        print(f"Атом {particle_type} на координатах: {particle_position}")

    # Выводим количество атомов.
    print(f"Количество атомов: {particles_property.count}")

    # Выводим количество связей в молекуле.
    print(f"Количество связей в молекуле: {particles_property.bonds.count}")

    # Выводим центр масс молекулы (из таблицы кластерного анализа).
    print(f"Центр масс: {cluster_table['Center of Mass'][...]}")

    # Создаём объект камеры для визуализации сцены.
    vp = Viewport()

    # Устанавливаем тип камеры (ортографическая проекция).
    vp.type = Viewport.Type.Ortho

    # Устанавливаем позицию камеры.
    vp.camera_pos = (0, -30, 30)

    # Задаём направление камеры (вектор взгляда).
    vp.camera_dir = (0, 1, -1)

    # Задаём поле зрения камеры (отдаляем её).
    vp.fov = math.radians(1000)

    # Рендерим анимацию молекулы с вращением.
    vp.render_anim(size=(800, 600), filename="animation.mp4", range=(0, num_frames), fps=8)
