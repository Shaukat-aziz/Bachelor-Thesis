# App.py Quick Reference - Pentagon + Photonic Simulator

**Version:** 2.1.0 | **Status:** Ready ✓ | **Tested:** Yes ✓

---

## Quick Start (30 Seconds)

```bash
# Navigate to project
cd /home/shaukat/OneDrive/Thesis/Thesis/Code/Python/FILES

# Create alias for easier use (optional)
alias pentagon-sim='/home/shaukat/mambaforge/envs/pymeep_env/bin/python3 app.py'

# Launch application
pentagon-sim

# Or direct command
/home/shaukat/mambaforge/envs/pymeep_env/bin/python3 app.py
```

---

## Common Commands

### 1. **Launch GUI**
```bash
pentagon-sim
# Starts photonic simulator with pentagon structure support
```

### 2. **Check System**
```bash
pentagon-sim --check
# Verifies all dependencies are installed
# Exit code: 0=OK, 1=Missing dependencies
```

### 3. **Check GPU**
```bash
pentagon-sim --gpu
# Shows NVIDIA GPU information
# Reports CUDA capability
```

### 4. **Show Version**
```bash
pentagon-sim --version
# Displays: Pentagon Photonic Crystal Simulator 2.1.0
```

### 5. **Show Pentagon Features**
```bash
pentagon-sim --pentagon
# Lists decay function types:
#   ✓ Exponential - Fast decay near point
#   ✓ Gaussian - Smooth bell curve
#   ✓ Polynomial - Power law
#   ✓ Custom - User equations
```

### 6. **Test Pentagon Structure**
```bash
pentagon-sim --test-pentagon
# Validates all pentagon operations:
#   ✓ Lattice creation with deformation
#   ✓ Transformation matrix generation
#   ✓ Configuration export/import
#   ✓ All decay profiles
```

### 7. **Show Help**
```bash
pentagon-sim --help
# Complete option reference
```

---

## Advanced Usage

### Configuration Management

**Export Current Configuration:**
```bash
pentagon-sim --export-config my_setup.json
# Saves pentagon structure configuration
```

**Import Configuration:**
```bash
pentagon-sim --import-config my_setup.json
# Loads pentagon structure configuration
```

### Debug Mode

**Run with Debugging:**
```bash
pentagon-sim --debug
# Runs in foreground for easy debugging
```

**Verbose Output:**
```bash
pentagon-sim --verbose
# Detailed output for all operations
# Shows dependency versions
# Lists GPU capabilities
```

**Combine Options:**
```bash
pentagon-sim --debug --verbose --pentagon
# Debug mode with verbose output and pentagon info
```

---

## Decay Function Examples

### Understanding Decay Profiles

```
Distance from stretching point: d
Maximum distance (lattice span): d_max
Normalized distance: x = d / d_max

EXPONENTIAL DECAY:
decay = e^(-3*x)
At x=0.5:   0.2231 (22% strength remaining)
At x=0.8:   0.0019 (almost zero)
Use: Fast propagation of deformation

GAUSSIAN DECAY:
decay = e^(-(x/0.35)²)
At x=0.5:   0.1299 (13% strength)
At x=0.8:   0.0001 (negligible)
Use: Smooth, natural-looking falloff

POLYNOMIAL DECAY:
decay = (1-x)³
At x=0.5:   0.1250 (12.5% strength)
At x=0.8:   0.0080 (less than 1%)
Use: Controlled power law effect

CUSTOM DECAY:
decay = your_equation(x)
Example: (1-x²) for quadratic
Uses: Specialized deformation profiles
```

---

## Python API (For Scripts)

### Basic Setup
```python
import sys
sys.path.insert(0, '/home/shaukat/OneDrive/Thesis/Thesis/Code/Python/FILES')

# Import directly
import importlib.util
spec = importlib.util.spec_from_file_location(
    "app_launcher", 
    "/home/shaukat/OneDrive/Thesis/Thesis/Code/Python/FILES/app.py"
)
app_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app_module)

AppLauncher = app_module.AppLauncher
PentagonStructureManager = app_module.PentagonStructureManager
```

### Create Pentagon Manager
```python
manager = PentagonStructureManager(n_cells=5, a_nm=400.0)

# Get decay value
decay = manager.decay_function(5.0, 10.0, 'exponential')
print(f"Decay at 50%: {decay:.4f}")

# Create lattice
atoms, corners, decay_profile = manager.create_lattice_with_deformation()

# Get transformation matrix
matrix = manager.create_transformation_matrix()

# Export configuration
manager.export_configuration('config.json')

# Get summary
summary = manager.get_summary()
print(summary)
```

### Create App Launcher
```python
launcher = AppLauncher()

# Check dependencies
ok = launcher.check_dependencies(verbose=True)

# Check GPU
launcher.check_gpu()

# Launch GUI (programmatically)
success = launcher.launch_gui(debug=False)

# Run with arguments
exit_code = launcher.run(['--pentagon'])
```

---

## Troubleshooting

### Issue: Command not found
**Solution:** Use full path
```bash
/home/shaukat/mambaforge/envs/pymeep_env/bin/python3 app.py
```

### Issue: Missing numpy
**Solution:** Activate environment
```bash
conda activate pymeep_env
python app.py
```

### Issue: testing.py not found
**Solution:** GUI launch will fail gracefully
```bash
# Ensure testing.py is in Python path
export PYTHONPATH=/home/shaukat/OneDrive/Thesis/Thesis/Code/Python/FILES:$PYTHONPATH
```

### Issue: GPU detection fails
**Solution:** Not required for functionality
```bash
# CPU mode still works fine
pentagon-sim
# GPU is optional, CPU mode is default
```

### Issue: Configuration import fails
**Solution:** Check JSON format
```bash
# Verify JSON is valid
python -m json.tool config.json

# Export fresh config
pentagon-sim --export-config config_new.json
```

---

## Environment Requirements

**Required Packages:**
- numpy (array operations)
- matplotlib (visualization)

**Optional Packages:**
- scipy (scientific computing)
- meep (electromagnetic simulation)

**Check Status:**
```bash
pentagon-sim --check
# Shows what's installed
```

**Install Dependencies:**
```bash
pip install numpy matplotlib scipy
# For full features with meep:
# conda install -c conda-forge pymeep
```

---

## Architecture Components

```
app.py
├── PentagonStructureManager
│   ├── Pentagon lattice operations
│   ├── Four decay function profiles
│   ├── Transformation matrices (36×36)
│   └── JSON serialization
│
├── AppLauncher
│   ├── Dependency management
│   ├── GPU detection
│   ├── GUI launching
│   └── CLI processing
│
└── Integration
    ├── testing.py (GUI)
    ├── photonic_simulator.py (Analysis)
    └── lattice_structures.py (Definitions)
```

---

## Quick Examples

### Example 1: Create Pentagon Lattice
```python
manager = PentagonStructureManager(n_cells=3, a_nm=469.0)
manager.target_angle = 72.0
manager.decay_profile = 'exponential'
atoms, corners, factors = manager.create_lattice_with_deformation()
print(f"Created lattice with {len(atoms)} atoms")
```

### Example 2: Test Different Decay Profiles
```python
manager = PentagonStructureManager()
profiles = ['exponential', 'gaussian', 'polynomial']
for profile in profiles:
    decay = manager.decay_function(5.0, 10.0, profile)
    print(f"{profile:12}: {decay:.4f}")
```

### Example 3: Save Configuration
```python
manager = PentagonStructureManager()
manager.export_configuration('my_pentagon.json')

# Later, restore exactly
manager.import_configuration('my_pentagon.json')
manager.create_lattice_with_deformation()  # Uses same config
```

### Example 4: Batch Processing
```bash
# Create script: process_pentagons.py
for i in {1..5}; do
    /home/shaukat/mambaforge/envs/pymeep_env/bin/python3 app.py \
        --export-config config_$i.json
done
```

---

## File Locations

**Main Application:**
```
/home/shaukat/OneDrive/Thesis/Thesis/Code/Python/FILES/app.py
```

**Related Files:**
```
/home/shaukat/OneDrive/Thesis/Thesis/Code/Python/FILES/testing.py
/home/shaukat/OneDrive/Thesis/Thesis/Code/Python/FILES/photonic_simulator.py
/home/shaukat/OneDrive/Thesis/Thesis/Code/Python/easyunfold/lattice_structures.py
/home/shaukat/OneDrive/Thesis/Thesis/Code/Python/FILES/lattice_visualization.py
```

**Documentation:**
```
/home/shaukat/OneDrive/Thesis/Thesis/Code/Python/FILES/APP_INTEGRATION_COMPLETE.md
/home/shaukat/OneDrive/Thesis/Thesis/Code/Python/FILES/PERIODIC_LATTICE_GUIDE.md
/home/shaukat/OneDrive/Thesis/Thesis/Code/Python/FILES/PERIODIC_LATTICE_QUICKSTART.md
```

---

## Quick Command Reference

| Task | Command |
|------|---------|
| Launch | `pentagon-sim` |
| Check Deps | `pentagon-sim --check` |
| GPU Info | `pentagon-sim --gpu` |
| Version | `pentagon-sim --version` |
| Pentagon Info | `pentagon-sim --pentagon` |
| Test | `pentagon-sim --test-pentagon` |
| Debug | `pentagon-sim --debug` |
| Verbose | `pentagon-sim -v` |
| Help | `pentagon-sim --help` |
| Export Config | `pentagon-sim --export-config file.json` |
| Import Config | `pentagon-sim --import-config file.json` |

---

## System Info

**Python Environment:**
```bash
/home/shaukat/mambaforge/envs/pymeep_env/bin/python3

# Or set in .bashrc for convenience:
export PYTHON_PENTAGON=/home/shaukat/mambaforge/envs/pymeep_env/bin/python3
$PYTHON_PENTAGON app.py
```

**Version Information:**
```
App Version: 2.1.0
Architecture: Pentagon Structure + Photonic Simulator v2.1
Python: 3.11.14
Platform: Linux
```

---

## Pro Tips

1. **Create alias for faster access:**
   ```bash
   alias pent='cd /home/shaukat/OneDrive/Thesis/Thesis/Code/Python/FILES && /home/shaukat/mambaforge/envs/pymeep_env/bin/python3 app.py'
   pent  # Now just type "pent"
   ```

2. **Save common configurations:**
   ```bash
   # Save your favorite setup
   pent --export-config favorite.json
   
   # Quick load later
   pent --import-config favorite.json
   ```

3. **Create helper scripts:**
   ```bash
   # setup_pentagon.sh
   #!/bin/bash
   cd /home/shaukat/OneDrive/Thesis/Thesis/Code/Python/FILES
   /home/shaukat/mambaforge/envs/pymeep_env/bin/python3 app.py "$@"
   ```

4. **Use verbose mode for debugging:**
   ```bash
   pent --verbose --test-pentagon 2>&1 | tee debug.log
   ```

---

## Status Dashboard

Run this to see everything:
```bash
pentagon-sim --verbose --check
pentagon-sim --pentagon
pentagon-sim --gpu
pentagon-sim --test-pentagon
```

---

**Created:** 2024  
**Status:** Complete and Tested ✓  
**Production Ready:** Yes ✓
