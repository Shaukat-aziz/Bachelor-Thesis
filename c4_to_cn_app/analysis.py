import numpy as np

def compute_vortex_charge(hz):

    field = hz[:,:,2]
    phase = np.angle(field)

    center = field.shape[0] // 2
    radius = field.shape[0] // 4

    samples = 300
    angles = []

    for i in range(samples):
        theta = 2*np.pi*i/samples
        x = int(center + radius*np.cos(theta))
        y = int(center + radius*np.sin(theta))
        angles.append(phase[x, y])

    angles = np.unwrap(angles)
    winding = (angles[-1] - angles[0])/(2*np.pi)

    return int(round(winding))