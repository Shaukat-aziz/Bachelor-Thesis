import numpy as np
import math

def generate_c4_lattice(a, R):
    points = []
    N = int(R/a) + 2

    for i in range(-N, N+1):
        for j in range(-N, N+1):
            x = i * a
            y = j * a
            if np.sqrt(x*x + y*y) <= R:
                points.append((x, y))

    return points


def volterra_transform(points, n):
    """
    General symmetric C4 → Cn Volterra shrink
    """
    if n < 3:
        raise ValueError("n must be >= 3")

    kappa = 4.0 / n
    delta = (360 - 360*kappa)/2

    new_points = []

    for (x, y) in points:
        r = math.sqrt(x*x + y*y)
        theta = math.degrees(math.atan2(y, x))
        if theta < 0:
            theta += 360

        if theta <= 180:
            theta_new = delta + kappa*theta
        else:
            theta_new = 180 + kappa*(theta - 180)

        theta_new = math.radians(theta_new)

        x_new = r * math.cos(theta_new)
        y_new = r * math.sin(theta_new)

        new_points.append((x_new, y_new))

    return new_points