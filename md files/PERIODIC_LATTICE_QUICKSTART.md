# Quick Start - N×N Periodic Lattice Visualization

## 30-Second Summary

The n×n lattice now acts as a **single fabric with periodic boundaries**:
- ✓ All unit cells identical (cohesive fabric)
- ✓ Seamless periodicity at edges (Bloch)
- ✓ Band structure for infinite repetition
- ✓ 3-panel control tab: unit cell + bands + reciprocal space

## Installation

1. **Already included** in the app directory:
   - `lattice_structures.py` - Extended with PeriodicLatticeConfig
   - `photonic_simulator.py` - Extended with visualization methods
   - `lattice_visualization.py` - New visualization module

2. **Dependencies**: numpy, matplotlib (in pymeep_env)

## Usage - 3 Lines of Code

```python
from photonic_simulator import PentagonPhotonicsGUI

gui = PentagonPhotonicsGUI()

# Create 5×5 periodic lattice as single fabric
gui.create_periodic_lattice(n_cells=5, a_um=0.4, hole_radius_nm=80)

# Show control tab with unit cell + band structure + reciprocal space
gui.show_lattice_control_tab()
```

## All Available Methods

### Create Lattice
```python
gui.create_periodic_lattice(
    n_cells=5,              # 5×5 cells (1-10 recommended)
    a_um=0.4,              # Lattice constant: 400 nm
    hole_radius_nm=80      # Hole radius: 80 nm
)
```

### Plot Unit Cell (Periodic Structure)
```python
fig, ax = gui.plot_unit_cell_structure(
    figsize=(8, 8),        # Figure size
    show_grid=True         # Show unit cell boundaries
)
```

### Plot Band Structure (Infinite Periodicity)
```python
fig, ax = gui.plot_band_structure_infinite_periodicity(
    figsize=(10, 6),       # Figure size
    num_kpoints=50         # K-points to sample
)
```

### Create Integrated Control Tab
```python
fig, axes = gui.create_lattice_control_tab()
# Returns dict with: 'unit_cell', 'band_structure', 'reciprocal_space'
# axes['unit_cell']      - Unit cell plot
# axes['band_structure'] - Band structure plot
# axes['reciprocal_space'] - Brillouin zone plot
```

## Visual Explanation

```
UNIT CELL PLOT                BAND STRUCTURE              RECIPROCAL SPACE
─────────────────             ──────────────             ────────────────
   3×3 array                  Frequency
  ┌──┬──┬──┐                     ▲                            ┌────┐
  │●●│●●│●●│                   │╱╱╱╱                        │  M │
  ├──┼──┼──┤  (periodic         │╱╱╱╱                      ──●────●──
  │●●│●●│●●│   boundaries)     │    ●  Band 2           ╱   │    │  ╲
  ├──┼──┼──┤                   │    ●●                  │  X  ●    X  │
  │●●│●●│●●│  (4 holes/cell)  │      ●●●             │    │    │    │
  └──┴──┴──┘                   │        ●●●  Band 1   │    │  Γ  │    │
     ● = hole                  │          ●●●●       │    │    │    │
     • = periodic copy         └─────────────────    │  X  ●    X  │
     ■ = central cell             Γ X M Γ           └────┬────┬───┘
                              (k-point path)          M  M  M
                          (Bloch periodicity)      (Brillouin Zone)
```

## Parameters Explained

| Parameter | Range | Default | Meaning |
|-----------|-------|---------|---------|
| n_cells | 1-10 | 3 | Number of unit cells in each direction |
| a_um | 0.2-1.0 | 0.4 | Lattice constant (micrometers) = 400 nm |
| hole_radius_nm | 20-200 | 80 | Air hole radius (nanometers) |
| num_kpoints | 20-100 | 50 | K-points sampled in band structure |

## What Gets Plotted

### Unit Cell Structure
- **Central cell**: Dark blue (emphasized)
- **Surrounding cells**: Light blue (periodic copies)
- **Grid**: Shows repetition pattern
- **Concept**: As if this unit cell repeats infinitely in all directions

### Band Structure
- **X-axis**: K-point path (Γ → X → M → Γ)
  - Γ (Gamma): Center of Brillouin zone
  - X: Edge midpoint
  - M: Corner
  - Forms hexagonal or rectangular path depending on symmetry
- **Y-axis**: Frequency (normalized)
- **Bands**: 4 curves (can show more per lattice details)
- **Gaps**: Spaces between bands = photonic bandgaps

### Reciprocal Lattice
- **Square boundary**: First Brillouin zone
- **Center point**: Γ (reciprocal space origin)
- **Edge points**: X points
- **Corner points**: M points
- **Dots**: Extended reciprocal lattice

## Physical Meaning: "Single Fabric"

### Traditional View (Rigid Boundaries)
```
Multiple separate problems connected at edges
↓
Each cell needs boundary treatment
↓
Different behavior at edges vs. interior
```

### New View (Bloch Periodicity)
```
ONE repeating unit cell tiled infinitely
↓
No special boundary treatment needed
↓
Same behavior everywhere (fabric properties)
↓
Band structure describes all k-values
```

**Real photonic crystals behave like "single fabric"** even though we see finite arrays!

## Example Scenarios

### Scenario 1: Design Photonic Filter

```python
# Create lattice
gui.create_periodic_lattice(n_cells=6, a_um=0.35, hole_radius_nm=65)

# View band structure
fig, axes = gui.create_lattice_control_tab()

# Look for bandgap between Band 1 (red) and Band 2 (blue)
# Bandgap frequency determines filter wavelength
```

### Scenario 2: Study Dispersion Relations

```python
# High resolution k-point sampling
gui.plot_band_structure_infinite_periodicity(num_kpoints=150)

# Analyze band curvature (group velocity = ∂ω/∂k)
# Flat bands → slow light
# Steep bands → fast light
```

### Scenario 3: Verify Symmetry

```python
# Create 4×4 lattice
gui.create_periodic_lattice(n_cells=4)

# Check unit cell plot
gui.plot_unit_cell_structure()

# Should see 4-fold rotational symmetry (C4 group)
# Holes at (±0.2a, ±0.2a)
```

## Troubleshooting

### "ModuleNotFoundError: matplotlib"
```
Solution: Use pymeep environment
/path/to/pymeep_env/bin/python your_script.py
OR
conda activate pymeep_env
python your_script.py
```

### "No plots showing"
```
Solution: Add plt.show() at end
import matplotlib.pyplot as plt
gui.show_lattice_control_tab()
plt.show()  # ← Add this
```

### "Band structure looks flat"
```
Check: Is bloch_periodicity enabled?
print(gui.lattice_config.bloch_periodicity)  # Should be True

Check: Is num_kpoints large enough?
gui.plot_band_structure_infinite_periodicity(num_kpoints=100)
```

## Advanced Customization

### Custom Hole Pattern

```python
from lattice_structures import PeriodicLatticeConfig

# Define custom hole positions (as fractions of lattice constant a)
custom_holes = [
    (-0.3, -0.3),  # Hole 1
    (0.3, -0.3),   # Hole 2
    (0.3, 0.3),    # Hole 3
    (-0.3, 0.3),   # Hole 4
]

lattice = PeriodicLatticeConfig(
    n_cells_x=5,
    n_cells_y=5,
    unit_cell_a_um=0.4,
    hole_radius_nm=80,
    holes_in_unit_cell=custom_holes,
    periodic_boundary_type="bloch",
    bloch_periodicity=True,
)

# Use with GUI
gui.lattice_config = lattice
gui.show_lattice_control_tab()
```

### Change Materials

```python
# Set substrate material (before creating lattice)
gui.set_substrate_material('Silicon')  # or 'InGaAsP', 'GaAs', etc.

# Then create lattice
gui.create_periodic_lattice(n_cells=5)
```

### Batch Generation

```python
# Create plots for multiple lattice sizes
for n_cells in [3, 4, 5, 6]:
    gui.create_periodic_lattice(n_cells=n_cells)
    fig, axes = gui.create_lattice_control_tab()
    fig.suptitle(f'Band Structure for {n_cells}×{n_cells} Lattice')
    plt.savefig(f'lattice_{n_cells}x{n_cells}.png', dpi=150)
    plt.close()
```

## Testing

Run included test script:

```bash
cd /home/shaukat/OneDrive/Thesis/Thesis/Code/Python/FILES/app

# Test basic functionality
/path/to/pymeep_env/bin/python test_periodic_lattice.py

# Or inline test
/path/to/pymeep_env/bin/python -c "
from lattice_structures import LatticeFactory
l = LatticeFactory.create_default_periodic(5)
print(f'✓ {len(l.get_periodic_array())} holes in 5×5 lattice')
"
```

## Key Differences: Periodic vs. Cavity vs. Uniform

| Feature | Periodic | Cavity | Uniform |
|---------|----------|--------|---------|
| Structure | N×N cells, identical | Central cavity + rings | Simple square |
| Boundaries | Bloch periodic | Floquet + periodic | Rigid |
| Best for | Band structure, PCs | Cavity resonators | Basic testing |
| Holes/cell | 4 (customizable) | 4 + surrounding | 4 (corners) |
| k-space | Full BZ | Partial (cavity) | Limited |

## Performance Notes

- **3×3 lattice**: 36 holes visible, instant
- **5×5 lattice**: 100 holes visible, instant  
- **10×10 lattice**: 400 holes visible, instant (CPU)
- **Band calculation**: O(n_kpoints × n_bands) ≈ 50×4 = 200 operations

No GPU optimization needed for visualization.

## References in Code

- [lattice_structures.py](lattice_structures.py) - PeriodicLatticeConfig, calculations
- [photonic_simulator.py](photonic_simulator.py) - GUI integration
- [lattice_visualization.py](lattice_visualization.py) - Plotting module
- [PERIODIC_LATTICE_GUIDE.md](PERIODIC_LATTICE_GUIDE.md) - Detailed guide

---

**Ready to use!** Start with Example 1 and modify parameters as needed.
