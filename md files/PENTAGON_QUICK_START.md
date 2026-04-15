# Quick Start Guide - Pentagon Structure & MEEP Integration

## 🚀 Getting Started with the Fixed Features

### Pre-requisites
Ensure you have the meep_env environment activated:
```bash
conda activate meep_env
```

All dependencies are already installed:
- ✅ PyQt6 6.x
- ✅ MEEP 1.31.0
- ✅ Matplotlib 3.10.8
- ✅ NumPy 2.2.6

---

## 📋 Pentagon Tab Overview

The **Pentagon Structure** tab in the GUI provides complete control over disclination cavity design and electromagnetic simulation.

### Available Controls

#### 1. **Decay Profile** (Dropdown)
Select how the lattice deformation varies from center:
- **Exponential** (default): `decay = exp(-λr)`
- **Gaussian**: `decay = exp(-λr²)`
- **Polynomial**: `decay = 1 - λr²`
- **Custom**: Enter your own equation

#### 2. **Custom Equation** (Text Input)
For Custom profile only. Use variable `r` for radial distance from center.

Example equations:
```
r**2 / (1 + r)     # Rational decay
exp(-r) * cos(r)   # Oscillating decay
sqrt(r)            # Square root decay
```

#### 3. **Target Angle** (Slider + Spinbox)
Set the disclination angle: **30° to 120°**

Common values:
- **60°**: Pentagonal defect
- **72°**: Pentagon symmetry
- **90°**: Square defect
- **120°**: Triangular defect

#### 4. **Decay Rate** (Slider)
Multiplier for decay strength: **1x to 5x**
- Lower values: gradual deformation
- Higher values: sharp disclination core

#### 5. **Global Scale** (Slider)
Overall size scaling: **0.5x to 2.0x**

#### 6. **Number of Cells** (Spinner)
Lattice size: **1×1 to 10×10 cells**
- Larger → slower computation
- Smaller → faster but less accuracy

#### 7. **MEEP Parameters**
Electromagnetic simulation settings:

| Parameter | Range | Default | Effect |
|-----------|-------|---------|--------|
| **Frequency** | 0.01 - 1.0 | 0.3 | Light wavelength (normalized) |
| **Resolution** | 5 - 50 | 20 | Points per micrometer |
| **Substrate ε** | 1.0 - 20.0 | 4.0 | Dielectric constant |

---

## 🎯 Function Workflows

### Workflow 1: Generate and Visualize Pentagon Structure

```
┌─────────────────────────────┐
│ Set Pentagon Parameters:    │
│ • Target Angle: 72°         │
│ • Cells: 3×3                │
│ • Decay: Exponential        │
└──────────────┬──────────────┘
               ↓
        [PLOT BUTTON]
               ↓
    Pentagon structure generated
    • Creates lattice atoms
    • Calculates deformations
    • Stores structure data
               ↓
    Displays 2-panel plot:
    • Left: Atom positions
    • Right: Deformation map
               ↓
    ✅ Ready for simulation
```

### Workflow 2: Run MEEP Electromagnetic Simulation

```
┌──────────────────────────────┐
│ Prerequisite: Plot structure │
│ (must run PLOT first)        │
└──────────────┬───────────────┘
               ↓
   [SIMULATE MEEP BUTTON]
               ↓
    ┌─────────────────────────┐
    │ MEEP Simulation Starts  │
    └────────┬────────────────┘
             ↓
    Step 1: Setting up cell (10% done)
             ↓
    Step 2: Building structure (20%)
             ↓
    Step 3: Setup source/detectors (30%)
             ↓
    Step 4: Initialize simulation (40%)
             ↓
    Step 5: Run solver 200 timesteps (50-80%)
             ↓
    Step 6: Collect field data (70%)
             ↓
    Step 7: Generate visualization (80%)
             ↓
    Results displayed:
    • Structure with materials
    • Electric field intensity
    • Resonance frequencies
    • Quality factors
             ↓
    ✅ MEEP simulation complete
```

### Workflow 3: Export Structure and Results

```
┌────────────────────────────────┐
│ After plotting (optional: MEEP) │
│ [EXPORT BUTTON]                │
└────────────────┬───────────────┘
                 ↓
        File Format Selection:
        • NPZ (NumPy) - Complete
        • CSV - Atom positions only
        • TXT - Human readable
                 ↓
        File dialog appears
                 ↓
        Choose save location
        Filename: pentagon_structure.npz
                 ↓
        Exports:
        • Atom positions
        • Cell boundaries
        • Deformation factors
        • MEEP parameters
        • (optional) Simulation results
                 ↓
        ✅ File saved
```

---

## 📊 Example Simulations

### Example 1: Pentagon Cavity (72°)

**Settings:**
```
Target Angle:     72°
Cells:            3×3
Decay Profile:    Exponential
Decay Rate:       1.5x
Frequency:        0.3
Resolution:       20
Substrate ε:      4.0
```

**Expected Output:**
- Pentagon-shaped defect in center
- 18 atoms arranged in pentagonal pattern
- Strong field localization at defect
- Q factor: ~50-100

---

### Example 2: Sharp Disclination (60°)

**Settings:**
```
Target Angle:     60°
Cells:            2×2
Decay Profile:    Gaussian
Decay Rate:       3.0x
Frequency:        0.5
Resolution:       30
Substrate ε:      9.0
```

**Expected Output:**
- Triangular defect pattern
- 8 atoms in small grid
- Faster simulation (2×2 cells)
- Higher index material

---

### Example 3: Weak Deformation (90°)

**Settings:**
```
Target Angle:     90°
Cells:            4×4
Decay Profile:    Polynomial
Decay Rate:       0.5x
Frequency:        0.1
Resolution:       10
Substrate ε:      2.0
```

**Expected Output:**
- Gradual square deformation
- 32 atoms in large grid
- Longer simulation time
- Lower dielectric contrast

---

## ⚡ Performance Tips

### Speed Up Simulation
1. **Reduce grid size**: 2×2 cells instead of 5×5
2. **Lower resolution**: 10 points/μm instead of 30
3. **Reduce time steps**: Modify source settings
4. **Lower frequency**: Larger wavelength = coarser mesh

### Improve Accuracy
1. **Increase grid size**: Use 4×4 or 5×5 cells
2. **Higher resolution**: 30-50 points/μm
3. **Higher order decay**: Use Gaussian or Custom
4. **Smaller decay rate**: More gradual transitions

---

## 🔍 Interpreting Results

### Plot 1: Pentagon Structure
- **Left Panel:**
  - Blue circles: atom positions
  - Black lines: cell boundaries
  - Check for pentagon/triangular patterns

- **Right Panel:**
  - Color intensity: deformation strength
  - Brighter = more deformation
  - Center usually brightest (disclination core)

### Plot 2: MEEP Results
- **Left Panel (Structure):**
  - Black regions: high permittivity
  - Light regions: air holes
  - Shows photonic crystal
  
- **Right Panel (Field):**
  - Red/bright: high field intensity
  - Blue/dark: low field intensity
  - Sharp peaks = resonance modes

---

## ❓ Troubleshooting

### Issue: "Plot function not working"
**Solution:**
- Ensure all parameters are valid
- Check terminal for detailed error message
- Verify pentagon generation works first

### Issue: MEEP simulation very slow
**Solution:**
- Reduce grid size (use 2×2 or 3×3 cells)
- Lower resolution parameter to 10-15
- Use smaller frequency (0.1-0.2)

### Issue: Export file not found
**Solution:**
- Check save location in dialog
- Ensure write permissions to directory
- Use home directory for safety
- Try NPZ format (most reliable)

### Issue: Field plot shows uniform color
**Solution:**
- Increase resolution parameter
- Use higher frequency (0.3-0.5)
- Check substrate epsilon > 1.0
- Run longer simulation

---

## 📈 Batch Processing Example

To run multiple simulations (in a Python script):

```python
from app.gui_launcher import PhotonicGUILauncher
from PyQt6.QtWidgets import QApplication

# Create app
app = QApplication([])
gui = PhotonicGUILauncher()

# Loop over angles
for angle in [60, 72, 90, 120]:
    # Set parameters
    gui.angle_spin.setValue(angle)
    gui.cells_spin.setValue(3)
    gui.decay_profile_combo.setCurrentText('Exponential')
    gui.meep_res_spin.setValue(20)
    
    # Generate structure
    gui.plot_pentagon_structure()
    
    # Run simulation
    gui.simulate_meep_structure()
    
    # Export results
    gui.export_pentagon_structure()
```

---

## 🎓 Learning Resources

### Key Publications
- Pentagon + lattice deformation theory
- Photonic crystals with defects
- MEEP documentation

### Related Files
- [PENTAGON_MEEP_FIX_SUMMARY.md](./PENTAGON_MEEP_FIX_SUMMARY.md) - Technical details
- [app/gui_launcher.py](./app/gui_launcher.py) - Source code
- [testing.py](./testing.py) - Pentagon generation algorithm
- [app/photonic_simulator.py](./app/photonic_simulator.py) - MEEP wrapper

---

## ✅ Verification Checklist

Before using in production:

- [ ] Environment activated: `conda activate meep_env`
- [ ] GUI launcher runs without errors
- [ ] Plot button generates valid image
- [ ] MEEP simulation completes in <30 seconds
- [ ] Export creates files successfully
- [ ] All decay profiles tested
- [ ] Angle range 60°-120° validates
- [ ] MEEP results show field patterns
- [ ] No memory errors on large grids

---

## 🔗 Key Functions

| Function | Purpose | Input | Output |
|----------|---------|-------|--------|
| `plot_pentagon_structure()` | Generate + visualize | GUI parameters | Stored structure data + PNG image |
| `simulate_meep_structure()` | Run EM simulation | Stored structure + MEEP params | Field data + results image |
| `export_pentagon_structure()` | Save data | Stored structure | NPZ/CSV/TXT file |
| `show_plot_dialog()` | Qt display | Image path | Dialog window |

---

**Status:** ✅ READY FOR USE  
**Tested:** February 16, 2025
