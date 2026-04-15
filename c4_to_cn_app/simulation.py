import meep as mp
import meep.mpb as mpb
import numpy as np

def run_simulation(points, r, R, resolution):

    geometry = []

    for (x, y) in points:
        geometry.append(
            mp.Cylinder(
                radius=r,
                center=mp.Vector3(x, y),
                material=mp.air
            )
        )

    cell = mp.Vector3(2*R, 2*R, 0)

    ms = mpb.ModeSolver(
        geometry_lattice=mp.Lattice(size=cell),
        geometry=geometry,
        resolution=resolution,
        num_bands=1
    )

    ms.run_te()

    hz = ms.get_efield(1)   # TE → Hz stored in Ez component
    freq = ms.freqs[0]

    return hz, freq