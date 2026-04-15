# MEEP Installation Quick Fix

## ⚠️ PROBLEM: "pip install meep" installs the WRONG package!

The package on PyPI called "meep" is **NOT** the official PyMeep electromagnetic simulation library.

## ✅ SOLUTION: Use conda instead

### Step 1: Uninstall wrong package (if you ran pip install meep)
```bash
pip uninstall meep
```

### Step 2: Install Miniconda (if you don't have conda)
```bash
# Download Miniconda
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh

# Install
bash Miniconda3-latest-Linux-x86_64.sh

# Follow prompts, then restart terminal
```

### Step 3: Create conda environment and install PyMeep
```bash
# Create environment
conda create -n meep_env python=3.10

# Activate environment
conda activate meep_env

# Install official PyMeep (this is the correct command!)
conda install -c conda-forge pymeep

# Install other required packages
pip install matplotlib numpy scipy
```

### Step 4: Run your script in the conda environment
```bash
# Make sure meep_env is activated
conda activate meep_env

# Run script
cd /home/shaukat/OneDrive/Thesis/Thesis/Code/Python/FILES
python testing.py
```

## 🔍 Verify Installation

Run the diagnostic tool:
```bash
python diagnose_meep.py
```

You should see:
```
✅ PyMeep is correctly installed - you're ready to go!
```

## 🎯 Why conda?

PyMeep has complex dependencies:
- HDF5 (for data I/O)
- MPI (for parallel computing)
- FFTW (for fast Fourier transforms)
- GSL, BLAS, LAPACK (numerical libraries)

Conda handles all these dependencies automatically. With pip, you'd need to manually compile everything from source (very difficult!).

## 🚀 Quick Test

After installation, test PyMeep:
```python
import meep as mp

# Should work without errors:
cell = mp.Vector3(10, 10, 0)
geometry = [mp.Cylinder(radius=1, center=mp.Vector3())]
sim = mp.Simulation(cell_size=cell, geometry=geometry, resolution=10)
print("✓ PyMeep working!")
```

## 💡 Alternative: Run without MEEP

The GUI works perfectly fine **without** MEEP! You just won't have:
- Band structure calculation
- EM field simulation
- Hz mode analysis

All other features work:
- Pentagon structure design
- Corner manipulation
- Transformation matrices
- Atom position control
- Export/import data

```bash
# Just run normally - GUI will work without MEEP
python testing.py
```

## 📚 References

- Official PyMeep docs: https://meep.readthedocs.io/
- Installation guide: https://meep.readthedocs.io/en/latest/Installation/
- Tutorial: https://meep.readthedocs.io/en/latest/Python_Tutorials/

## ❓ Still Having Issues?

1. **Run diagnostic**:
   ```bash
   python diagnose_meep.py
   ```

2. **Check conda environment**:
   ```bash
   conda env list  # See all environments
   conda activate meep_env  # Make sure you're in correct env
   which python  # Should show conda environment path
   ```

3. **Verify imports**:
   ```python
   import meep as mp
   print(mp.__file__)  # Should be in conda env
   print(hasattr(mp, 'Medium'))  # Should print: True
   ```

4. **If all else fails**: Use the GUI without MEEP - it's fully functional for structure design and analysis!
