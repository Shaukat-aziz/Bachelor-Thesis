# Installing Official PyMeep for Electromagnetic Simulations

## Problem
You encountered this error:
```
ERROR: 'meep' module missing mp.Medium. This is not the official PyMeep package.
ERROR: Setup simulation first (click 'Setup Sim')
```

This occurs when a **wrong/incompatible** `meep` package is installed (e.g., `meep==1.0.6` from PyPI), which is NOT the official PyMeep electromagnetic simulation software.

## Solution

### Option 1: Install via Conda (Recommended - Easiest)

**Step 1: Install Miniconda** (if not already installed)
```bash
# Download Miniconda installer
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh

# Install Miniconda
bash Miniconda3-latest-Linux-x86_64.sh

# Follow prompts (accept license, choose location)
# Initialize conda
conda init bash

# Restart terminal or source bashrc
source ~/.bashrc
```

**Step 2: Install Official PyMeep**
```bash
# Accept conda terms (if needed)
conda tos accept

# Install pymeep from conda-forge channel
conda install -c conda-forge pymeep

# This will install ~2GB of dependencies (BLAS, FFTW, HDF5, etc.)
# Installation may take 10-30 minutes
```

**Step 3: Verify Installation**
```bash
python -c "import meep as mp; print('Medium:', hasattr(mp, 'Medium')); print('Cylinder:', hasattr(mp, 'Cylinder')); print('✓ PyMeep installed correctly!')"
```

Expected output:
```
Medium: True
Cylinder: True
✓ PyMeep installed correctly!
```

### Option 2: Use Docker (Alternative)

If conda installation fails or takes too long, use the official MEEP Docker image:

```bash
# Pull MEEP docker image
docker pull simpetus/meep

# Run your script in docker
docker run -v $(pwd):/work -w /work simpetus/meep python testing.py
```

### Option 3: Build from Source (Advanced)

Follow the official guide: https://meep.readthedocs.io/en/latest/Installation/

**Requirements:**
- C++ compiler (gcc/g++)
- MPI libraries
- BLAS/LAPACK
- HDF5
- FFTW3
- libctl
- harminv

This is complex and time-consuming (~1-2 hours).

## Current Status

✅ **Fixed:** The script now properly detects incompatible MEEP installations
✅ **Fixed:** Clear error messages with installation instructions
✅ **Working:** All non-MEEP features work normally (structure manipulation, visualization)
❌ **Disabled:** Electromagnetic simulation features (until PyMeep is properly installed)

## Testing After Installation

Once PyMeep is installed, test with:

```bash
cd /home/shaukat/OneDrive/Thesis/Thesis/Code/Python/FILES
python testing.py
```

You should see:
```
✓ Official PyMeep detected and ready
```

Then in the GUI:
1. Click "Setup Sim" - should work without errors
2. Click "Run Sim" - runs electromagnetic simulation
3. Click "Show Hz" - displays magnetic field visualization

## Troubleshooting

### Issue: "conda: command not found"
**Solution:** Miniconda not installed or not in PATH
```bash
export PATH="$HOME/miniconda/bin:$PATH"
source ~/.bashrc
```

### Issue: Conda solving environment takes forever
**Solution:** Use mamba (faster conda alternative)
```bash
conda install -c conda-forge mamba
mamba install -c conda-forge pymeep
```

### Issue: "ImportError: libguile" or similar library errors
**Solution:** Conda should handle all dependencies. If errors persist:
```bash
conda install -c conda-forge libctl harminv libgdsii
```

## Why Not pip?

The official PyMeep requires compiled C++ libraries (MEEP core) with Python bindings. These dependencies are complex:
- MEEP C++ library
- MPI (parallel computing)
- HDF5 (data storage)
- FFTW3 (fast Fourier transforms)
- BLAS/LAPACK (linear algebra)

Conda manages all these dependencies automatically. pip cannot handle this complexity for PyMeep.

## References

- **Official PyMeep Documentation:** https://meep.readthedocs.io/
- **Installation Guide:** https://meep.readthedocs.io/en/latest/Installation/
- **GitHub Repository:** https://github.com/NanoComp/meep
- **Python API Reference:** https://meep.readthedocs.io/en/latest/Python_Tutorials/Basics/

## For Immediate Use Without MEEP

The testing.py script works fully **without** MEEP for:
- ✓ Pentagon structure creation and manipulation
- ✓ 5-petal lattice with decay profiles  
- ✓ Real-time stretching/contracting
- ✓ Atom position control
- ✓ Visualization and plotting
- ✓ Export structure data

Only electromagnetic simulation features are disabled.
