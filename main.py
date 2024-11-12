import ovito.io
from ovito.modifiers import CreateBondsModifier, ClusterAnalysisModifier, CalculateDisplacementsModifier, AffineTransformationModifier
from ovito.vis import Viewport
import math
import numpy as np

if __name__ == '__main__':
    num_frames = 100  # Количество кадров в анимации
    rotation_angle_per_frame_z = 360 / num_frames  # Угол вращения по оси Z на кадр (в градусах)
    rotation_angle_per_frame_y = 180 / num_frames

    pipeline = ovito.io.import_file("20.xyz")

    bond_modifier = CreateBondsModifier()
    bond_modifier.mode = CreateBondsModifier.Mode.Pairwise
    bond_modifier.set_pairwise_cutoff("C", "C", 1.6)
    bond_modifier.set_pairwise_cutoff("C", "H", 1.1)
    bond_modifier.set_pairwise_cutoff("C", "O", 1.5)
    bond_modifier.set_pairwise_cutoff("O", "H", 1.0)

    cluster_analysis_modifier = ClusterAnalysisModifier(compute_com=True)

    calculate_displacements_modifier = CalculateDisplacementsModifier()
    calculate_displacements_modifier.vis.enabled = False

    def rotate(frame, data):
        theta = np.deg2rad(frame * 5.0)

        tm = [
            [np.cos(theta), 0, np.sin(theta), 0],
            [0, 1, 0, 0],
            [-np.sin(theta), 0, np.cos(theta), 0]
        ]

        data.apply(AffineTransformationModifier(transformation=tm))

    pipeline.modifiers.append(bond_modifier)
    pipeline.modifiers.append(cluster_analysis_modifier)
    pipeline.modifiers.append(calculate_displacements_modifier)
    pipeline.modifiers.append(rotate)
    pipeline.add_to_scene()

    data = pipeline.compute()

    particles_property = data.particles

    type_property = particles_property.particle_types

    cluster_table = data.tables['clusters']

    for i in range(particles_property.count):
        particle_type = type_property.type_by_id(type_property[i]).name
        particle_position = particles_property.positions[i]

        print(f"Атом {particle_type} на координатах: {particle_position}")

    print(f"Количество атомов: {particles_property.count}")
    print(f"Количество связей в молекуле: {data.particles.bonds.count}")
    print(f"Центр масс: {cluster_table['Center of Mass'][...]}")

    vp = Viewport()
    vp.type = Viewport.Type.Ortho
    vp.camera_pos = (0, -30, 30)
    vp.camera_dir = (0, 1, -1)
    vp.fov = math.radians(1000)

    vp.render_anim(size=(800, 600), filename="animation.mp4", range=(0,num_frames), fps=8)