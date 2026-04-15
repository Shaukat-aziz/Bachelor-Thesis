#!/usr/bin/env python3
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
import imageio.v2 as imageio
from typing import Any


# ==========================================
# Volterra C4 -> Cn GIF Generator
# Mirrors the logic used in dxf.py starter script
# ==========================================

# -----------------------------
# PARAMETERS (edit freely)
# -----------------------------
a = 1.0
r_hole = 0.1 * a
offset = 0.34 * a
Rmax = 3
cavity_radius = 3.35
cell_size = 7
n = 5
c = 0.5   # core pull strength (0.0 to 1.0)

d = 0.8  # angular displacement strength (0.0 to 1.0)
s = 0     # parity selector (0 or 1)

# If True, GIF focuses on angular Volterra process only
angular_only = True

# Animation controls
frames_open_cut = 18
frames_insert_sector = 18
frames_compress = 24
frames_core_pull = 16
frames_second_group = 16
hold_frames = 8
fps = 12
out_gif = "volterra_c4_to_cn.gif"


# -----------------------------
# Helpers
# -----------------------------
def draw_frame(coords, title, filename):
    fig, ax = plt.subplots(figsize=(6, 6), dpi=120)
    fig.patch.set_facecolor("#202124")
    ax.set_facecolor("#111111")

    for x, y in coords:
        patch = Circle((float(x), float(y)), float(r_hole), facecolor="#00d4ff", edgecolor="white", linewidth=0.4)
        ax.add_patch(patch)

    half = cell_size / 2
    ax.set_xlim(-half, half)
    ax.set_ylim(-half, half)
    ax.set_aspect("equal")
    ax.tick_params(colors="white")
    ax.set_title(title, color="white")

    for spine in ax.spines.values():
        spine.set_color("#666666")

    plt.tight_layout()
    fig.savefig(filename)
    plt.close(fig)


def lerp(a0, a1, t):
    return (1.0 - t) * a0 + t * a1


def polar_to_cart(r, theta):
    return np.column_stack([r * np.cos(theta), r * np.sin(theta)])


# -----------------------------
# Step 0: Build base C4 lattice
# -----------------------------
c4_basis = [
    (+offset, +offset),
    (+offset, -offset),
    (-offset, +offset),
    (-offset, -offset),
]

base_points = []
for i in range(-Rmax, Rmax + 1):
    for j in range(-Rmax, Rmax + 1):
        for dx, dy in c4_basis:
            x = i * a + dx
            y = j * a + dy
            r = np.sqrt(x**2 + y**2)
            if r < cavity_radius:
                base_points.append((x, y))

base_points = np.array(base_points, dtype=float)


# -----------------------------
# Step 1: Volterra sector insertion for n > 4
# -----------------------------
base_r = np.linalg.norm(base_points, axis=1)
base_theta = np.arctan2(base_points[:, 1], base_points[:, 0])
base_theta = np.where(base_theta < 0, base_theta + 2 * np.pi, base_theta)

base_polar = np.column_stack([base_r, base_theta])

# Excess wedge angle to go from C4 to Cn by insertion
omega = max(0.0, 2 * np.pi * ((n - 4) / 4))
theta_cut = 0.0

if n > 4 and omega > 0:
    opened_theta = base_theta.copy()
    opened_theta[base_theta >= theta_cut] = opened_theta[base_theta >= theta_cut] + omega
    opened_polar = np.column_stack([base_r, opened_theta])

    # Points that will fill the inserted sector [theta_cut, theta_cut + omega)
    insert_mask = (base_theta >= theta_cut) & (base_theta < theta_cut + omega)
    inserted_sector_polar = base_polar[insert_mask]

    sector_added_polar = np.vstack([opened_polar, inserted_sector_polar])
else:
    opened_polar = base_polar.copy()
    inserted_sector_polar = np.empty((0, 2), dtype=float)
    sector_added_polar = base_polar.copy()

coords_opened = np.column_stack([
    opened_polar[:, 0] * np.cos(opened_polar[:, 1]),
    opened_polar[:, 0] * np.sin(opened_polar[:, 1]),
])

coords_inserted_sector = np.column_stack([
    inserted_sector_polar[:, 0] * np.cos(inserted_sector_polar[:, 1]),
    inserted_sector_polar[:, 0] * np.sin(inserted_sector_polar[:, 1]),
]) if inserted_sector_polar.shape[0] > 0 else np.empty((0, 2), dtype=float)

coords_sector_added = np.column_stack([
    sector_added_polar[:, 0] * np.cos(sector_added_polar[:, 1]),
    sector_added_polar[:, 0] * np.sin(sector_added_polar[:, 1]),
])


# -----------------------------
# Step 2: Angular compression back to 2π
# -----------------------------
if n > 4 and omega > 0:
    alpha = (2 * np.pi) / (2 * np.pi + omega)
else:
    alpha = 1.0

compressed_polar = sector_added_polar.copy()
compressed_polar[:, 1] = compressed_polar[:, 1] * alpha

coords_compressed_raw = np.column_stack([
    compressed_polar[:, 0] * np.cos(compressed_polar[:, 1]),
    compressed_polar[:, 0] * np.sin(compressed_polar[:, 1]),
])

coords_compressed = np.unique(np.round(coords_compressed_raw, 6), axis=0)


# -----------------------------
# Step 3: Core Pull (nearest n)
# -----------------------------
coords_after_core = coords_compressed.copy()

if coords_after_core.shape[0] >= n:
    distances = np.linalg.norm(coords_after_core, axis=1)
    nearest_indices = np.argsort(distances)[:n]

    for idx in nearest_indices:
        r = distances[idx]
        theta = np.arctan2(coords_after_core[idx, 1], coords_after_core[idx, 0])
        r_new = (1 - c) * r
        coords_after_core[idx, 0] = r_new * np.cos(theta)
        coords_after_core[idx, 1] = r_new * np.sin(theta)


# -----------------------------
# Step 4: Second-nearest group displacement
# Take 2*n after excluding nearest n
# -----------------------------
coords_final = coords_after_core.copy()

distances = np.linalg.norm(coords_final, axis=1)
sorted_idx = np.argsort(distances)
second_group_indices = sorted_idx[n:3 * n] if coords_final.shape[0] >= 3 * n else np.array([], dtype=int)

if second_group_indices.size > 0:
    ring_points = coords_final[second_group_indices]
    ring_theta = np.arctan2(ring_points[:, 1], ring_points[:, 0])
    ring_r = np.linalg.norm(ring_points, axis=1)

    theta_order = np.argsort(ring_theta)
    delta_theta = d * (np.pi / (2 * n))
    s = int(s) % 2

    for i, local_idx in enumerate(theta_order):
        global_idx = second_group_indices[local_idx]
        theta = ring_theta[local_idx]
        r = ring_r[local_idx]
        theta_new = theta + ((-1) ** (i + s)) * delta_theta
        coords_final[global_idx, 0] = r * np.cos(theta_new)
        coords_final[global_idx, 1] = r * np.sin(theta_new)


# -----------------------------
# Build animation frames
# -----------------------------
png_files = []
frame_id = 0


def emit(coords, title):
    global frame_id
    name = f"_volterra_frame_{frame_id:04d}.png"
    title_with_params = f"{title}\n(c={c:.2f}, d={d:.2f})"
    draw_frame(coords, title_with_params, name)
    png_files.append(name)
    frame_id += 1


# Hold base C4
for _ in range(hold_frames):
    emit(base_points, "Step 0: Base C4 lattice")

# Animate cut opening (base -> opened)
if coords_opened.shape[0] == base_points.shape[0] and n > 4:
    for k in range(frames_open_cut):
        t = k / max(frames_open_cut - 1, 1)
        r_t = base_polar[:, 0]
        theta_t = lerp(base_polar[:, 1], opened_polar[:, 1], t)
        coords_t = polar_to_cart(r_t, theta_t)
        emit(coords_t, f"Step 1: Open cut and insert angular gap  t={t:.2f}")

# Animate sector insertion by progressively adding points into the gap
if n > 4 and coords_inserted_sector.shape[0] > 0:
    total_insert = coords_inserted_sector.shape[0]
    for k in range(frames_insert_sector):
        t = k / max(frames_insert_sector - 1, 1)
        count = int(round(t * total_insert))
        if count > 0:
            coords_t = np.vstack([coords_opened, coords_inserted_sector[:count]])
        else:
            coords_t = coords_opened
        emit(coords_t, f"Step 1b: Add C4 sector for n>4  t={t:.2f}")

# Hold full sector-added state
for _ in range(max(2, hold_frames // 2)):
    emit(coords_sector_added, "Step 1c: Sector-added C4 state")

# Animate angular compression (sector-added -> compressed)
if coords_sector_added.shape[0] == coords_compressed_raw.shape[0]:
    for k in range(frames_compress):
        t = k / max(frames_compress - 1, 1)
        r_t = sector_added_polar[:, 0]
        theta_t = lerp(sector_added_polar[:, 1], compressed_polar[:, 1], t)
        coords_t = polar_to_cart(r_t, theta_t)
        emit(coords_t, f"Step 2: Angular compression to C{n}  t={t:.2f}")
else:
    for _ in range(frames_compress):
        emit(coords_compressed, f"Step 2: Angular compression to C{n}")

if not angular_only:
    # Animate core pull (compressed -> after core)
    for k in range(frames_core_pull):
        t = k / max(frames_core_pull - 1, 1)
        coords_t = coords_compressed.copy()
        if coords_after_core.shape[0] >= n:
            distances = np.linalg.norm(coords_compressed, axis=1)
            nearest_indices = np.argsort(distances)[:n]
            for idx in nearest_indices:
                x0, y0 = coords_compressed[idx]
                x1, y1 = coords_after_core[idx]
                coords_t[idx, 0] = lerp(x0, x1, t)
                coords_t[idx, 1] = lerp(y0, y1, t)
        emit(coords_t, f"Step 3: Core pull  t={t:.2f}")

    # Animate second-group displacement (after core -> final)
    for k in range(frames_second_group):
        t = k / max(frames_second_group - 1, 1)
        coords_t = coords_after_core.copy()
        if second_group_indices.size > 0:
            for idx in second_group_indices:
                x0, y0 = coords_after_core[idx]
                x1, y1 = coords_final[idx]
                coords_t[idx, 0] = lerp(x0, x1, t)
                coords_t[idx, 1] = lerp(y0, y1, t)
        emit(coords_t, f"Step 4: 2n-group angular shift  t={t:.2f}")

# Hold final frame
final_coords = coords_compressed if angular_only else coords_final
for _ in range(hold_frames):
    emit(final_coords, f"Final C{n} (angular process)")


# -----------------------------
# Save GIF
# -----------------------------
images: list[Any] = [imageio.imread(png) for png in png_files]
imageio.mimsave(out_gif, images, fps=fps)

# Cleanup temporary PNGs
for png in png_files:
    try:
        import os
        os.remove(png)
    except OSError:
        pass

print(f"Saved GIF: {out_gif}")
