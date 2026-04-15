# Band Structure and Hz Field Analysis Guide

## Overview
This guide explains how to use PyMeep for photonic band structure calculations and Hz field mode analysis in the pentagon 2D structure.

## Features Added

### 1. Photonic Band Structure Calculation
- **Eigenmode solver**: Uses Harminv method to find resonant frequencies at each k-point
- **K-point sampling**: Automatic interpolation along Γ→X→M→Γ path in reciprocal space
- **Band gap detection**: Automatic identification and analysis of photonic band gaps
- **Customizable parameters**: Number of bands (1-20), k-points (5-100), frequency range

### 2. Hz Field Mode Analysis
- **Field statistics**: Mean, standard deviation, max amplitude, total energy
- **2D FFT analysis**: Power spectrum in reciprocal space
- **Spatial visualization**: Real/imaginary parts, magnitude, energy density
- **Hotspot detection**: Identifies regions of high field concentration
- **Cross-sections**: Horizontal and vertical field profiles

### 3. Export Capabilities
- **Band structure data**: Frequencies, k-points, band gaps → `.npy` files
- **Field data**: Hz, Ex, Ey field arrays → `.npy` files
- **Metadata**: Complete simulation parameters and analysis results → `.txt` files

## Installation

### Prerequisites
```bash
# Required: PyMeep electromagnetic simulation package
conda install -c conda-forge pymeep

# Optional but recommended: HDF5 support
conda install -c conda-forge h5py

# Verify installation
python test_band_structure.py
```

### Troubleshooting
- If `pip install meep` installs wrong package, use conda instead
- PyMeep requires: MPI, HDF5, FFTW, BLAS/LAPACK (handled by conda)
- For custom builds: https://meep.readthedocs.io/en/latest/Installation/

## GUI Controls

### Electromagnetic Simulation Panel
Located in the right panel of the GUI:

#### Basic Field Simulation
- **Freq**: Source frequency (typically 0.10-0.30)
- **λ**: Wavelength in nm (auto-calculated from frequency)
- **Res**: Resolution (pixels per unit, higher = more accurate but slower)
- **R(nm)**: Cylinder radius representing atoms (typically 30-100 nm)
- **ε**: Dielectric constant of atom material (e.g., 12 for Si)
- **Time**: Simulation runtime in time steps (100-500 typical)
- **Hz/Ex/Ey**: Checkboxes to select field components to compute

#### Band Structure Panel
- **Bands**: Number of photonic bands to calculate (default: 8)
- **K-pts**: Number of k-points along path (default: 20)
- **f_min**: Minimum frequency for band diagram (default: 0.0)
- **f_max**: Maximum frequency for band diagram (default: 0.5)

### Buttons

#### Field Simulation Buttons
1. **Setup Sim**: Creates MEEP geometry from current pentagon structure
   - Converts atom positions to dielectric cylinders
   - Sets up PML boundary conditions
   - Adds Gaussian source at center

2. **Run Sim**: Executes time-domain electromagnetic simulation
   - Runs for specified number of time steps
   - Computes selected field components (Hz, Ex, Ey)
   - Stores field data for visualization

3. **Show Hz**: Displays electromagnetic fields
   - Shows real and imaginary parts
   - Overlays structure for context
   - Multiple field components side-by-side

4. **Clear Sim**: Resets simulation data
   - Frees memory
   - Allows reconfiguration

5. **Export Fields**: Saves field data to files
   - Creates `.npy` files for each field component
   - Saves metadata and parameters

#### Band Structure Buttons
1. **Calc Bands**: Calculate photonic band structure
   - Sets up k-point path: Γ→X→M→Γ
   - Uses Harminv eigenmode solver at each k-point
   - Extracts resonant frequencies for each band
   - Typically takes 5-30 minutes depending on parameters

2. **Show Bands**: Visualize band diagram
   - Plots all bands vs. wave vector
   - Marks high-symmetry points (Γ, X, M)
   - Highlights band gaps in red
   - Prints gap analysis to console

3. **Hz Modes**: Detailed Hz field analysis
   - 6-panel comprehensive visualization:
     * Real part
     * Imaginary part
     * Magnitude
     * Power spectrum (2D FFT)
     * Cross-sections
     * Energy density
   - Identifies hotspots (top 5% energy)
   - Computes field statistics

4. **Export Bands**: Save band structure data
   - Frequency array: shape (num_k, num_bands)
   - K-point coordinates
   - Gap analysis report
   - All in timestamped `.npy` and `.txt` files

## Workflow

### Complete Analysis Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│ STEP 1: Design Structure                                    │
│  • Adjust pentagon angle, decay profile, atom positions    │
│  • Use corner manipulation for fine-tuning                  │
│  • Verify structure visually                                │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 2: Setup MEEP Simulation                               │
│  • Click "Setup Sim" button                                 │
│  • Configure: resolution, cylinder radius, epsilon          │
│  • MEEP converts atoms → dielectric cylinders               │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 3: Field Simulation (Optional)                         │
│  • Set frequency/wavelength                                 │
│  • Click "Run Sim"                                          │
│  • Click "Show Hz" to visualize fields                      │
│  • Click "Hz Modes" for detailed analysis                   │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 4: Band Structure Calculation                          │
│  • Set: Bands=8, K-pts=20, f_min=0.0, f_max=0.5           │
│  • Click "Calc Bands" (wait 5-30 min)                      │
│  • Monitor progress in console                              │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 5: Visualization and Analysis                          │
│  • Click "Show Bands" → see band diagram                   │
│  • Check console for band gap analysis                      │
│  • Identify photonic band gaps (red regions)                │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 6: Export Results                                      │
│  • Click "Export Bands" → save band structure data         │
│  • Click "Export Fields" → save field distributions        │
│  • Use data for further post-processing/ML                  │
└─────────────────────────────────────────────────────────────┘
```

### Quick Start Example

1. **Launch GUI**:
   ```bash
   python testing.py
   ```

2. **Create structure** (or use default 72° pentagon)

3. **Setup simulation**:
   - Resolution: 20
   - Cylinder radius: 50 nm
   - Epsilon: 12
   - Click "Setup Sim"

4. **Calculate bands**:
   - Bands: 8
   - K-points: 20
   - Click "Calc Bands" (wait ~10 minutes)

5. **Visualize**:
   - Click "Show Bands"
   - Look for band gaps (red shaded regions)

6. **Field analysis** (optional):
   - Frequency: 0.15
   - Time: 200
   - Enable Hz checkbox
   - Click "Run Sim"
   - Click "Hz Modes"

## Understanding the Results

### Band Structure Diagram
- **X-axis**: Wave vector along high-symmetry path (Γ→X→M→Γ)
- **Y-axis**: Frequency in units of c/a (speed of light / lattice constant)
- **Bands**: Each colored line represents a photonic band
- **Band Gaps**: Red shaded regions indicate photonic band gaps
  - Complete gap: No propagating modes in any direction
  - Directional gap: Gap along specific k-direction

### Band Gap Analysis
Console output provides:
- Gap frequency range [f_lower, f_upper]
- Gap size: Δf = f_upper - f_lower
- Gap ratio: (Δf/f_center) × 100%

Example output:
```
Band gap between bands 2 and 3:
  Gap: [0.2134, 0.2876]
  Size: 0.0742 (Δf/f_center = 29.6%)
```

### Hz Field Analysis
- **Real/Imaginary parts**: Show oscillating field patterns
- **Magnitude**: Total field strength at each point
- **Power spectrum**: Spatial frequency content (shows periodicity)
- **Energy density**: |Hz|² shows where energy concentrates
- **Hotspots**: Regions with >95th percentile energy
  - Useful for identifying resonant cavities
  - Indicates strong light-matter interaction regions

## Parameter Guidelines

### Resolution
- **Low (10-15)**: Fast, rough estimate, may miss features
- **Medium (20-30)**: Good balance, typical for exploration
- **High (40+)**: Accurate, slow, use for final results

### Number of Bands
- **Few (4-6)**: Quick calculation, see lowest bands
- **Medium (8-12)**: Good overview of band structure
- **Many (15-20)**: Complete picture, very slow

### K-points
- **Sparse (10-15)**: Fast, may miss band extrema
- **Standard (20-30)**: Good resolution of band structure
- **Dense (40+)**: High detail, minimal improvement over 30

### Cylinder Radius
- **Small (20-40 nm)**: Weak photonic crystal effect
- **Medium (50-80 nm)**: Balanced, typical for silicon
- **Large (80+ nm)**: Strong scattering, may create large gaps

### Dielectric Constant (ε)
- **Air**: ε = 1
- **SiO₂**: ε ≈ 2.1
- **Silicon (Si)**: ε ≈ 12
- **GaAs**: ε ≈ 13
- Higher ε → stronger photonic crystal effects

## Applications

### 1. Photonic Crystal Design
- Identify structures with large photonic band gaps
- Tune gap position by adjusting:
  - Pentagon angle (72° → 60° → 90°)
  - Cylinder radius
  - Dielectric constant

### 2. Waveguide Design
- Find defect modes within band gaps
- Design slow-light structures (flat bands)
- Optimize coupling efficiency

### 3. Resonator Design
- Locate high-Q resonances using Hz mode analysis
- Identify field concentration regions (hotspots)
- Design compact optical cavities

### 4. Material Science
- Compare different lattice geometries
- Study effect of disorder (use corner manipulation)
- Validate theoretical models

### 5. Machine Learning
- Export transformation matrices and band structures
- Train ML models to predict photonic properties
- Inverse design: desired bands → structure parameters

## Computational Cost

Typical timing (single core, resolution=20):

| Operation           | Time      | Notes                          |
|---------------------|-----------|--------------------------------|
| Setup Sim           | 1-2 sec   | One-time setup                 |
| Run Sim (200 steps) | 2-5 min   | Per field component            |
| Hz Mode Analysis    | 10-20 sec | After Run Sim                  |
| Calc Bands (8×20)   | 10-30 min | Depends heavily on structure   |
| Show Bands          | 1-2 sec   | Visualization only             |

**Optimization tips**:
- Start with low resolution (10) for testing
- Use fewer k-points (10-15) initially
- Calculate fewer bands (4-6) first
- Increase resolution only for final results
- Use parallel computing if available (requires MPI build)

## File Outputs

### Field Data Files
- `meep_Hz_<timestamp>.npy`: Hz field array (complex)
- `meep_Ex_<timestamp>.npy`: Ex field array (complex)
- `meep_Ey_<timestamp>.npy`: Ey field array (complex)
- `meep_eps_<timestamp>.npy`: Dielectric distribution
- `meep_params_<timestamp>.txt`: Simulation parameters

### Band Structure Files
- `band_frequencies_<timestamp>.npy`: shape (num_k, num_bands)
- `band_kpoints_<timestamp>.npy`: shape (num_k, 3)
- `band_metadata_<timestamp>.txt`: Complete analysis report

### Loading Data in Python
```python
import numpy as np

# Load band structure
freqs = np.load('band_frequencies_<timestamp>.npy')
k_points = np.load('band_kpoints_<timestamp>.npy')

# Load Hz field
hz_field = np.load('meep_Hz_<timestamp>.npy')

# Access specific band
band_2 = freqs[:, 1]  # Second band (0-indexed)

# Plot custom analysis
import matplotlib.pyplot as plt
plt.plot(band_2)
plt.show()
```

## Troubleshooting

### Issue: "MEEP not available"
**Solution**: Install PyMeep via conda:
```bash
conda install -c conda-forge pymeep
```

### Issue: Simulation very slow
**Solutions**:
- Reduce resolution (20 → 10)
- Reduce runtime (200 → 100)
- Reduce k-points (20 → 10)
- Use fewer bands

### Issue: No band gaps found
**Possible causes**:
- Dielectric contrast too low (increase ε)
- Cylinders too small (increase radius)
- Wrong frequency range (adjust f_min, f_max)
- Structure not periodic enough

### Issue: Harminv finds no modes
**Solutions**:
- Increase runtime (200 → 300)
- Widen frequency range
- Check if source is at node of desired mode
- Increase resolution

### Issue: Bands look noisy/discontinuous
**Solutions**:
- Increase k-points (20 → 40)
- Increase resolution (20 → 30)
- Longer runtime for better frequency resolution

## Advanced Topics

### Custom K-point Paths
To modify the k-point path, edit in `calculate_band_structure()`:
```python
k_points = [
    mp.Vector3(0, 0, 0),      # Γ
    mp.Vector3(0.5, 0, 0),    # X
    mp.Vector3(0.5, 0.5, 0),  # M
    mp.Vector3(0, 0, 0)       # Γ
]
```

For pentagon/hexagonal structures, you might want:
```python
k_points = [
    mp.Vector3(0, 0, 0),             # Γ
    mp.Vector3(1/3, 1/3, 0),         # K
    mp.Vector3(0.5, 0, 0),           # M
    mp.Vector3(0, 0, 0)              # Γ
]
```

### Parallel Computing
If MEEP built with MPI:
```bash
mpirun -np 4 python testing.py
```
Note: GUI may not work well with MPI; export scripts better.

### Frequency-Dependent Materials
Modify setup_meep_simulation() to use:
```python
material = mp.Medium(epsilon=12, 
                    D_conductivity=0.1)  # Loss
```

### 3D Structures
Current code is 2D (Hz polarization). For 3D:
- Change cell_size to have z-component
- Adjust cylinder height
- Use 3D sources
- Much slower computation!

## References

### MEEP Documentation
- Official docs: https://meep.readthedocs.io/
- Tutorial: https://meep.readthedocs.io/en/latest/Python_Tutorials/
- Examples: https://github.com/NanoComp/meep/tree/master/python/examples

### Photonic Crystals
- Joannopoulos et al., "Photonic Crystals: Molding the Flow of Light"
- Johnson & Joannopoulos, Opt. Express 8, 173-190 (2001)

### Band Structure Theory
- Ashcroft & Mermin, "Solid State Physics" (Chapter on reciprocal lattice)
- Kittel, "Introduction to Solid State Physics"

## Citation

If you use this code in research, please cite:
- MEEP: Oskooi et al., Comput. Phys. Commun. 181, 687-702 (2010)
- Your structure/methods as appropriate

## Support

For issues:
1. Check console output for error messages
2. Verify MEEP installation: `python test_band_structure.py`
3. Review this documentation
4. Check MEEP docs: https://meep.readthedocs.io/

## Changelog

**Version 2.0** (Current)
- Added photonic band structure calculation
- Added Hz field mode analysis with 2D FFT
- Added band gap detection and analysis
- Added comprehensive export functionality
- Enhanced field visualization

**Version 1.0**
- Basic electromagnetic field simulation
- Structure manipulation and transformation matrices
