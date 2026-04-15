# MEEP Electromagnetic Simulation Integration

## Overview

PyMeep electromagnetic simulation has been integrated into the Pentagon Structure GUI, enabling Hz field, electromagnetic wave (EMW), and electromagnetic field wave (EMFW) domain studies for your lattice structures.

**Date:** February 10, 2026  
**Status:** ✓ Fully Implemented and Tested

---

## Features Added

### 1. **MEEP Control Panel**
- New control section in the right panel of GUI
- Complete set of electromagnetic simulation parameters
- Field selection checkboxes (Hz, Ex, Ey)
- Simulation control buttons

### 2. **Electromagnetic Field Calculations**
- **Hz Field**: Magnetic field (z-component) - primary focus for 2D structures
- **Ex Field**: Electric field (x-component)
- **Ey Field**: Electric field (y-component)
- Real-time field extraction and visualization

### 3. **Domain Study Capabilities**
- Frequency domain analysis (configurable frequency/wavelength)
- Spatial resolution control (5-50 pixels per unit)
- Dielectric structure visualization
- Field-structure overlay for interaction analysis

---

## Control Panel Parameters

### Simulation Parameters

| Parameter | Control | Range | Description |
|-----------|---------|-------|-------------|
| **Frequency** | Freq textbox | 0.01-1.0 | Source frequency (1/wavelength) |
| **Wavelength** | λ textbox | 1.0-100.0 | Wavelength (auto-updates with freq) |
| **Resolution** | Res textbox | 5-50 | Pixels per unit length |
| **Cylinder Radius** | R(nm) textbox | 10-200 nm | Atom representation radius |
| **Dielectric Constant** | ε textbox | 1.0-20.0 | Material property for atoms |
| **Runtime** | Time textbox | 50-1000 | Simulation time steps |

### Field Selection

**Checkboxes** (Hz, Ex, Ey):
- ✓ Hz: Magnetic field z-component (default ON)
- ☐ Ex: Electric field x-component
- ☐ Ey: Electric field y-component

---

## Workflow

### Step 1: Setup Simulation
```
1. Adjust your pentagon structure (angle, decay, atoms)
2. Set MEEP parameters:
   - Frequency: 0.15 (default)
   - Resolution: 20 (default)
   - Cylinder radius: 50 nm (default)
   - Dielectric: 12.0 (default)
3. Click "Setup Sim" button
```

**What Happens:**
- Converts all atom positions to MEEP geometry (cylinders)
- Creates simulation domain with proper boundaries
- Adds plane wave source from left side
- Configures PML (Perfectly Matched Layer) boundaries
- Displays setup summary in console

### Step 2: Run Simulation
```
1. Click "Run Sim" button
2. Wait for simulation to complete (time depends on resolution/runtime)
3. Field data automatically extracted
```

**What Happens:**
- Runs electromagnetic simulation for specified time steps
- Extracts Hz, Ex, Ey fields (based on checkbox selection)
- Extracts dielectric structure (ε)
- Stores field data for visualization

### Step 3: Visualize Fields
```
1. Select fields to view (checkboxes)
2. Click "Show Hz" (or Show Ex/Ey) button
3. New window opens with field plots
```

**What's Displayed:**
- Left column: Pure field distribution (RdBu colormap)
- Right column: Field with structure overlay (black contours)
- Multiple fields shown in separate rows
- Colorbars for quantitative analysis

### Step 4: Export Data (Optional)
```
1. Click "Export Fields" button
2. Select save directory
3. All field data saved to .npy files
4. Parameters saved to .txt file
```

**Files Created:**
- `meep_Hz_YYYYMMDD_HHMMSS.npy`
- `meep_Ex_YYYYMMDD_HHMMSS.npy` (if computed)
- `meep_Ey_YYYYMMDD_HHMMSS.npy` (if computed)
- `meep_eps_YYYYMMDD_HHMMSS.npy` (structure)
- `meep_params_YYYYMMDD_HHMMSS.txt` (parameters)

---

## Technical Details

### Geometry Conversion

**Atom → Cylinder Mapping:**
```python
# Each atom position converted to MEEP cylinder
atom_position → cylinder(
    radius = meep_cylinder_radius / scale_factor,
    center = (x_meep, y_meep, 0),
    height = infinite,
    epsilon = meep_epsilon
)
```

**Coordinate Transformation:**
- Lattice coordinates (nm) → MEEP units
- Scale factor: wavelength × 100
- Centering: Domain centered at (0, 0)
- All 5 petals included (full pentagon)

### Simulation Domain

**Cell Size:**
```
Domain = (max_x - min_x + 2×padding) × (max_y - min_y + 2×padding)
Padding = 500 nm (default)
PML Thickness = 1.0 MEEP units
```

**Source Configuration:**
- Type: Continuous plane wave
- Component: Hz (out-of-plane magnetic field)
- Position: Left boundary
- Size: Spans entire height

### Field Extraction

**Supported Components:**
- `mp.Hz`: Magnetic field (z-component)
- `mp.Ex`: Electric field (x-component)
- `mp.Ey`: Electric field (y-component)
- `mp.Dielectric`: Structure (ε distribution)

**Data Format:**
- 2D numpy arrays (x, y)
- Resolution determined by simulation resolution
- Complex-valued fields (real part visualized)

---

## Example Use Cases

### 1. Photonic Band Structure Analysis

**Goal:** Study electromagnetic wave propagation through pentagon lattice

**Steps:**
```
1. Create pentagon with desired deformation
2. Set frequency = 0.15 (optical regime)
3. Set resolution = 30 (high quality)
4. Setup → Run → Show Hz
5. Analyze field distribution patterns
```

**Analysis:**
- Look for localized modes (bright spots)
- Check for band gaps (dark regions)
- Observe scattering patterns

### 2. Metamaterial Response Study

**Goal:** Investigate dielectric response at different frequencies

**Workflow:**
```
# Frequency sweep
For freq in [0.05, 0.10, 0.15, 0.20, 0.25]:
    1. Set frequency = freq
    2. Set epsilon = 12.0 (high contrast)
    3. Setup → Run → Export
    4. Analyze field patterns

Compare results across frequencies
```

### 3. Waveguide Mode Analysis

**Goal:** Study electromagnetic field confinement

**Configuration:**
```
- Frequency: 0.15
- Cylinder radius: 100 nm (large atoms)
- Epsilon: 15.0 (high dielectric)
- Resolution: 40 (very high)
- Runtime: 500 (long simulation)
```

**Observations:**
- Hz field concentration between atoms
- Ex/Ey field patterns along edges
- Mode shapes and symmetries

### 4. Defect State Characterization

**Goal:** Introduce defects and study localization

**Method:**
```
1. Drag corners to create asymmetric deformation
2. Setup MEEP simulation
3. Run with high resolution
4. Compare Hz field with undeformed case
5. Identify localized states at defects
```

---

## Visualization Features

### Field Plots

**Left Column: Pure Fields**
- Shows field distribution without structure
- RdBu colormap (red = positive, blue = negative)
- Interpolation: spline36 (smooth)
- Colorbar: Quantitative scale

**Right Column: Structure Overlay**
- Field distribution with atom positions
- Black contours: Dielectric boundaries (ε > 1.5)
- Shows field-structure interaction
- Identify scattering centers

### Multiple Field Comparison

**Simultaneous Display:**
```
If Hz, Ex, Ey all checked:
  - Row 1: Hz (left: field, right: with structure)
  - Row 2: Ex (left: field, right: with structure)
  - Row 3: Ey (left: field, right: with structure)
```

---

## Performance Considerations

### Resolution vs Speed

| Resolution | Quality | Speed | Use Case |
|------------|---------|-------|----------|
| 5-10 | Low | Fast | Quick preview |
| 15-20 | Medium | Moderate | Standard analysis |
| 25-35 | High | Slow | Publication quality |
| 40-50 | Very High | Very Slow | Critical features |

**Recommendation:** Start with resolution=15, increase for final results

### Runtime Guidelines

| Structure Size | Resolution | Runtime | Typical Duration |
|----------------|------------|---------|------------------|
| Small (3×3) | 20 | 200 | ~30 seconds |
| Medium (5×5) | 20 | 300 | ~2 minutes |
| Large (7×7) | 20 | 500 | ~5 minutes |

**Note:** Times depend on CPU. Higher resolution = exponentially longer.

---

## Troubleshooting

### Issue: "MEEP NOT AVAILABLE"

**Solution:**
```bash
pip install meep
# or with conda:
conda install -c conda-forge pymeep
```

### Issue: Simulation takes too long

**Solutions:**
1. Reduce resolution (20 → 15)
2. Reduce runtime (200 → 100)
3. Reduce domain size (smaller padding)

### Issue: Field visualization unclear

**Solutions:**
1. Increase resolution for smoother fields
2. Try different field components (Hz, Ex, Ey)
3. Adjust frequency for better coupling
4. Increase runtime for steady state

### Issue: Memory error during simulation

**Solutions:**
1. Reduce resolution (30 → 20)
2. Reduce domain size
3. Close other applications
4. Use smaller structure (fewer petals)

---

## Advanced Features

### Custom Frequency Sweeps

**Python Script Example:**
```python
# After setting up GUI
frequencies = np.linspace(0.05, 0.25, 11)
for freq in frequencies:
    gui.meep_frequency = freq
    gui.meep_wavelength = 1.0 / freq
    gui.setup_meep_simulation(None)
    gui.run_meep_simulation(None)
    gui.export_meep_fields(None)
```

### Field Processing

**Load and Analyze:**
```python
import numpy as np
import matplotlib.pyplot as plt

# Load saved field
hz_field = np.load('meep_Hz_20260210_153045.npy')

# Compute intensity
intensity = np.abs(hz_field)**2

# Find peaks
from scipy.signal import find_peaks
peaks = find_peaks(intensity.flatten())

# Fourier analysis
fft_hz = np.fft.fft2(hz_field)
power_spectrum = np.abs(fft_hz)**2
```

---

## Integration with Existing Features

### Compatible Features

✓ **Works with:**
- All decay profiles (exponential, gaussian, polynomial, custom)
- Custom atom positions (Update Atoms)
- Corner dragging (fabric deformation)
- Global scaling
- Matrix export/import
- Plot save/load

✗ **Not affected by:**
- Transformation matrix display
- Selection visibility toggle
- Petal individual scaling (uses composite structure)

### Recommended Workflow

**Complete Analysis:**
```
1. Design Structure
   - Adjust angle, decay, scale
   - Set custom atom positions
   - Drag corners for deformation

2. Export Structure
   - Get Transformation Matrix (36×36)
   - Save Plot (configuration .pkl)
   - Export matrices (.npy)

3. EM Simulation
   - Setup MEEP geometry
   - Run simulation
   - Show Hz/Ex/Ey fields
   - Export field data

4. Analysis
   - Load exported data in Python
   - Compute derived quantities
   - Compare with theory
   - Publish results
```

---

## File Outputs Summary

### From MEEP Export

| File | Format | Content | Size |
|------|--------|---------|------|
| meep_Hz_*.npy | NumPy | Hz field 2D array | ~1-10 MB |
| meep_Ex_*.npy | NumPy | Ex field 2D array | ~1-10 MB |
| meep_Ey_*.npy | NumPy | Ey field 2D array | ~1-10 MB |
| meep_eps_*.npy | NumPy | Dielectric structure | ~1-10 MB |
| meep_params_*.txt | Text | Simulation parameters | ~1 KB |

**Size depends on:** Resolution, domain size, runtime

---

## Limitations

1. **2D Simulation Only**
   - Out-of-plane fields not considered
   - 3D effects approximated

2. **Computational Cost**
   - High resolution simulations slow
   - Memory scales with resolution²

3. **Geometry Approximation**
   - Atoms represented as cylinders
   - Finite radius may overlap

4. **Source Configuration**
   - Fixed plane wave source
   - Custom sources require code modification

---

## Future Enhancements (Potential)

- [ ] 3D simulation support
- [ ] Multiple source types (point, gaussian beam)
- [ ] Frequency sweep automation
- [ ] Band structure calculation
- [ ] S-parameter extraction
- [ ] Time-domain animation
- [ ] Custom boundary conditions
- [ ] Dispersive materials

---

## Citation

If using MEEP simulations in publications:

**MEEP:**
```
Oskooi et al., "MEEP: A flexible free-software package for 
electromagnetic simulations by the FDTD method," 
Computer Physics Communications 181, 687-702 (2010).
```

**This Tool:**
```
Pentagon Structure GUI with MEEP Integration
Version 1.2 (February 2026)
```

---

## Support & Documentation

**MEEP Documentation:**
- Official docs: https://meep.readthedocs.io/
- Tutorial: https://meep.readthedocs.io/en/latest/Python_Tutorials/
- Examples: https://github.com/NanoComp/meep/tree/master/python/examples

**GUI Documentation:**
- Main README: [README.md](README.md)
- Atom Update Fix: [ATOM_UPDATE_FIX.md](ATOM_UPDATE_FIX.md)
- Quick Start: [QUICK_START_ATOMS.md](QUICK_START_ATOMS.md)

---

**Status:** ✓ Fully Implemented, Tested, and Ready for Use  
**Version:** 1.2 (MEEP Integration)  
**Date:** February 10, 2026
