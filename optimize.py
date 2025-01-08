import ovito.io
from ovito.modifiers import CreateBondsModifier
from optimize_modifier import OptimizeModifier # Кастомный модификатор для создания анимации оптимизации

# Viewport используется для настройки визуализации сцены, например, камеры и её параметров.
from ovito.vis import Viewport

if __name__ == '__main__':
    # Количество кадров в анимации.
    num_frames = 200

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

    pipeline.modifiers.append(bond_modifier)

    pipeline.modifiers.append(OptimizeModifier())

    # Добавляем весь конвейер (пайплайн) на сцену для визуализации.
    pipeline.add_to_scene()

    data = pipeline.compute()

    best_positions = data.particles.positions[:]

    # Создаём объект камеры для визуализации сцены.
    vp = Viewport()

    # Устанавливаем тип камеры (ортографическая проекция).
    vp.type = Viewport.Type.Ortho

    # Устанавливаем позицию камеры.
    vp.camera_pos = (0, -30, 30)

    # Задаём направление камеры (вектор взгляда).
    vp.camera_dir = (0, 1, -1)

    # Наводим камеру на молекулу
    vp.zoom_all()

    vp.render_anim(size=(800, 600), filename="optimization.mp4", range=(0, num_frames), fps=20)