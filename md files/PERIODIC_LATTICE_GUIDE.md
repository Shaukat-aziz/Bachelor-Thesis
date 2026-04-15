# N×N Periodic Lattice as Single Fabric - Implementation Guide

## Overview

The n×n lattice structure now acts as a **single cohesive fabric** with periodic boundary conditions (Bloch periodicity). This means:

1. **All unit cells are identical** - No special boundary handling
2. **Periodic boundaries at edges** - Seamless continuation
3. **Treated as infinite periodic structure** - For band structure calculations
4. **k-point sampling throughout Brillouin zone** - Complete band mapping

## Key Concepts

### Single Fabric Interpretation

Instead of treating an n×n lattice as "n×n separate cells", we now treat it as:
- **One repeating unit cell** that tiles infinitely in space
- **Periodic boundary conditions** at all edges
- **Bloch k-vectors** describing electron/photon states
- **Band structure valid for infinite periodicity**

### Periodic Boundary Conditions (Bloch)

```
Traditional (Rigid):          Periodic (Bloch):
┌─────┐                      ┌─────┐
│ ┌─┐ │                      │ ┌─┐ │
│ └─┘ │ (Hard edges,         │ └─┘ │ (Seamless)
│     │  defect modes)       │     │ (Same structure
└─────┘                      └─────┘  wraps around)
         [Finite]                      [Infinite}
```

## Implementation Files

### 1. **lattice_structures.py** - Core Implementation

#### New Classes

```python
class PeriodicLatticeConfig(BaseLatticeConfig):
    """N×N periodic lattice with Bloch/Floquet boundary conditions."""
    
    n_cells_x: int = 3                          # Cells in X direction
    n_cells_y: int = 3                          # Cells in Y direction
    periodic_boundary_type: str = "bloch"       # 'bloch' or 'rigid'
    bloch_periodicity: bool = True              # Enable Bloch
    floquet_periodicity: bool = False           # Optional out-of-plane
```

#### Key Methods

```python
get_holes_per_unitcell() -> List[HolePosition]
    # Get holes in SINGLE unit cell (repeating pattern)

get_periodic_array() -> List[HolePosition]
    # Get all holes in N×N visible array
    # Treats each cell identically - single fabric concept

get_structure_info() -> dict
    # Returns: dimension, unit_cell_a, holes_per_unit_cell,
    #          total_holes_visible, periodic_boundary_type, etc.
```

#### Utility Functions

```python
calculate_band_structure_with_floquet(lattice_config, k_points, frequencies)
    # Band structure for infinite periodic lattice
    # Supports both Cavity (Floquet) and Periodic (Bloch) lattices
    # Returns: k_points, bands array, boundary_type

get_periodic_lattice_unit_cell_data(lattice_config)
    # Extract unit cell visualization data
    # Returns: holes, unit_cell_size, symmetry info

get_reciprocal_lattice_points(lattice_config, num_points)
    # Calculate k-point path: Γ → X → M → Γ
    # High-symmetry points for band structure plotting
```

### 2. **photonic_simulator.py** - GUI Integration

#### New Methods in PentagonPhotonicsGUI

```python
create_periodic_lattice(n_cells, a_um, hole_radius_nm)
    # Create n×n periodic lattice as single fabric
    # Default: 3×3, 400 nm lattice, 80 nm holes

plot_unit_cell_structure(figsize, show_grid)
    # Plot unit cell with periodic tiling visualization
    # Central cell highlighted, others faded

plot_band_structure_infinite_periodicity(figsize, num_kpoints)
    # Plot band structure for infinite periodic lattice
    # High-symmetry path: Γ → X → M → Γ

create_lattice_control_tab()
    # Create integrated visualization panel:
    # - Unit cell plot (central cell emphasized)
    # - Band structure plot (Bloch bands)
    # Returns: fig, axes dict

show_lattice_control_tab()
    # Display control tab with both visualizations
```

### 3. **lattice_visualization.py** - Visualization Module

```python
class LatticeVisualizationPanel:
    """Creates control tab with unit cell + band structure + reciprocal space."""
    
    create_control_panel() -> Tuple[Figure, Dict[str, Axes]]
        # Create 3-panel visualization:
        # 1. Unit cell structure (periodic tiling)
        # 2. Band structure (Γ → X → M → Γ path)
        # 3. Reciprocal lattice (Brillouin zone)
    
    update_from_lattice_config(new_config)
        # Update all plots after lattice parameter changes
```

## Usage Examples

### Example 1: Create Periodic Lattice

```python
from photonic_simulator import PentagonPhotonicsGUI
from lattice_structures import LatticeType

# Create GUI
gui = PentagonPhotonicsGUI(lattice_type=LatticeType.CAVITY)

# Switch to periodic lattice (5×5 as single fabric)
gui.create_periodic_lattice(
    n_cells=5,              # 5×5 array
    a_um=0.4,              # 400 nm lattice constant
    hole_radius_nm=80      # 80 nm holes
)
```

### Example 2: Plot Unit Cell

```python
# Plot unit cell structure
fig, ax = gui.plot_unit_cell_structure(figsize=(8, 8))
# Shows:
# - Central unit cell highlighted in dark blue
# - Surrounding periodic copies in light blue
# - Grid showing periodicity
```

### Example 3: Plot Band Structure

```python
# Plot band structure for infinite lattice
fig, ax = gui.plot_band_structure_infinite_periodicity(
    figsize=(10, 6),
    num_kpoints=60
)
# Shows:
# - 4 bands along Γ → X → M → Γ path
# - High-symmetry points marked
# - Assumes infinite periodic continuation
```

### Example 4: Integrated Control Tab

```python
# Create complete control panel
fig, axes = gui.create_lattice_control_tab()
# Returns figure with 3 subplots:
# - axes['unit_cell']: Unit cell plot
# - axes['band_structure']: Band structure plot
# - axes['reciprocal_space']: Brillouin zone

# Or show directly
gui.show_lattice_control_tab()
```

## Physical Interpretation

### What "Acting as Single Fabric" Means

**Before (Traditional):**
```
3×3 array = 3×3 separate problems
- Each cell could be different
- Boundary effects at edges
- No k-space analysis
```

**After (Single Fabric):**
```
3×3 array = 1 unit cell repeated infinitely
- All cells IDENTICAL (fabric property)
- NO boundary effects (Bloch periodicity)
- FULL band structure from k-space sampling
```

### Unit Cell vs. Visible Array

| Aspect | Unit Cell | Visible Array |
|--------|-----------|---------------|
| Size | a × a | (n×a) × (n×a) |
| Holes | 4 (typical) | 4n² |
| Periodicity | Repeats at boundaries | Shows n² copies |
| Visualization | Emphasized | Faded copies |
| Band structure | Defines dispersion | Samples full BZ |

### Bloch Periodicity in Band Structure

For a unit cell with lattice constant **a**:
- Reciprocal lattice vector: **b = 2π/a**
- Brillouin zone: **-π/a ≤ k ≤ π/a**
- Band structure path: **Γ(0,0) → X(π/a,0) → M(π/a,π/a) → Γ(0,0)**

Each band is periodic in k-space with period **b**.

## Visualization Details

### Unit Cell Plot
- **Central cell** (0,0): Dark blue, solid lines (emphasized)
- **Surrounding cells**: Light blue, dashed lines (periodic copies)
- **Total visible**: 3×3=9 cells shown, but conceptually infinite
- **Boundary**: Visual indication of periodicity wrapping

### Band Structure Plot
- **Horizontal axis**: K-point path index
- **Vertical axis**: Frequency ω·a/2πc (normalized)
- **4 plots**: 4 bands shown (can extend)
- **Vertical lines**: Mark X and M points (high-symmetry)
- **Continuous curves**: Band dispersions along k-path

### Reciprocal Space Plot
- **Brillouin zone**: Square for square lattice
- **Γ point**: Center (star marker)
- **X points**: Edge midpoints (triangle markers)
- **M points**: Corners (square markers)
- **Reciprocal lattice**: Faint points show full reciprocal lattice

## Configuration Parameters

### PeriodicLatticeConfig

```python
n_cells_x: int = 3                  # Number of cells in X
n_cells_y: int = 3                  # Number of cells in Y
unit_cell_a_um: float = 0.4        # Lattice constant (400 nm default)
air_hole_radius_nm: float = 80.0   # Hole radius (80 nm default)

periodic_boundary_type: str = "bloch"  # "bloch" (recommended) or "rigid"
bloch_periodicity: bool = True         # Enable Bloch periodicity
floquet_periodicity: bool = False      # Out-of-plane periodicity

# Holes positioned as fractions of lattice constant:
# (-0.2, -0.2), (0.2, -0.2), (0.2, 0.2), (-0.2, 0.2) = 4 holes/cell
holes_in_unit_cell: List[Tuple[float, float]]
```

## Band Structure Calculation

### Physical Model

For a periodic lattice, band structure is calculated assuming:

1. **Infinite periodic continuation** in all directions
2. **Bloch theorem** applies:
   ```
   ψ(r + R) = e^(i·k·R) ψ(r)
   ```
   where R is lattice vector, k is Bloch wave vector

3. **Band dispersion** describes energy vs. k-vector
4. **High-symmetry path** samples important k-points:
   - **Γ**: Zone center (0, 0)
   - **X**: Zone edge (π/a, 0)
   - **M**: Zone corner (π/a, π/a)

### Band Types

- **Bloch bands**: Standard photonic/electronic bands for periodic structure
- **Cavity modes**: Special Floquet-based analysis for cavities
- **Surface modes**: At material boundaries (not shown by default)

## Testing and Validation

Run comprehensive tests:

```bash
cd /home/shaukat/OneDrive/Thesis/Thesis/Code/Python/FILES/app

# Test in pymeep environment
/path/to/pymeep_env/bin/python -c "
from lattice_structures import LatticeFactory
lattice = LatticeFactory.create_default_periodic(5)
print('✓ 5×5 periodic lattice created')
print(f'  Holes: {len(lattice.get_periodic_array())}')
print(f'  Boundary: Bloch (periodic)')
"
```

## Common Use Cases

### 1. Photonic Crystal Design
```python
# Create 7×7 periodic lattice
gui.create_periodic_lattice(n_cells=7, a_um=0.35, hole_radius_nm=70)

# Visualize band structure
fig, axes = gui.create_lattice_control_tab()

# Identify bandgaps between Band 1 and Band 2
# Use for optical filter or waveguide design
```

### 2. Dispersion Relation Study
```python
# Create lattice with custom parameters
gui.create_periodic_lattice(n_cells=4, a_um=0.5, hole_radius_nm=100)

# Plot band structure
gui.plot_band_structure_infinite_periodicity(num_kpoints=100)

# Analyze curvature and group velocity
```

### 3. Bandgap Analysis
```python
# Plot unit cell
gui.plot_unit_cell_structure()

# Overlay band structure
fig, (ax1, ax2) = subplots(1, 2)
# Left: Unit cell (structure)
# Right: Bands (properties)
```

## Troubleshooting

### Issue: Visualization not showing
```python
# Ensure matplotlib is available
# Use pymeep environment or install:
pip install matplotlib

# Then run:
gui.show_lattice_control_tab()
```

### Issue: Band structure looks unusual
```python
# Check lattice parameters:
info = gui.lattice_config.get_structure_info()
print(info)

# Ensure bloch_periodicity = True
print(f"Bloch: {gui.lattice_config.bloch_periodicity}")

# Verify unit cell a and hole radius reasonable
```

### Issue: Too many or too few holes visible
```python
# Check n_cells and a_um:
lattice = gui.lattice_config
expected_holes = 4 * lattice.n_cells_x * lattice.n_cells_y
actual_holes = len(lattice.get_periodic_array())

print(f"Expected: {expected_holes}, Actual: {actual_holes}")
```

## Mathematical Background

### Reciprocal Lattice Vector

For square lattice with constant **a**:
$$\mathbf{b} = \frac{2\pi}{a}$$

### Band Frequency vs K-point

Simplified tight-binding dispersion:
$$\omega(k) = \omega_0 + A \cos(ka)$$

where:
- $\omega_0$: Base frequency
- $A$: Band width (depends on coupling)
- $k$: Bloch wave vector in [-π/a, π/a]

### Brillouin Zone

For 2D square lattice:
$$-\frac{\pi}{a} \leq k_x, k_y \leq \frac{\pi}{a}$$

First Brillouin zone (IBZ) reduced to:
$$0 \leq k_x \leq \frac{\pi}{a}, \quad 0 \leq k_y \leq \frac{\pi}{a}$$

## API Reference Summary

```python
# Main classes
PeriodicLatticeConfig          # N×N periodic lattice configuration
LatticeVisualizationPanel      # Visualization panel creator

# Factory methods
LatticeFactory.create_default_periodic(n_cells)

# Calculation functions
calculate_band_structure_with_floquet()
get_periodic_lattice_unit_cell_data()
get_reciprocal_lattice_points()

# GUI methods
gui.create_periodic_lattice()
gui.plot_unit_cell_structure()
gui.plot_band_structure_infinite_periodicity()
gui.create_lattice_control_tab()
gui.show_lattice_control_tab()
```

## References

- Photonic Crystals: Molding the Flow of Light, Joannopoulos et al.
- Bloch Theorem for periodic structures
- Brillouin zone construction for square lattices
- Plane wave method for photonic band structure

---

**Version**: 2.1  
**Last Updated**: February 2026  
**Status**: Production Ready
