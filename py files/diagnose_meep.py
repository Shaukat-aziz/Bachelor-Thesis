#!~/mamabaforge/envs/pymeep_env/bin/python
"""
MEEP Installation Diagnostic Tool
==================================
Checks your MEEP installation and provides fix instructions.
"""

import sys
print("="*80)
print("MEEP INSTALLATION DIAGNOSTIC")
print("="*80)

# Check Python environment
print(f"\n1. Python Environment:")
print(f"   Python: {sys.version}")
print(f"   Executable: {sys.executable}")
print(f"   Virtual env: {sys.prefix}")

# Try to import meep
print(f"\n2. Attempting to import 'meep'...")
try:
    import meep as mp
    print(f"   ✓ 'meep' module imported successfully")
    print(f"   Location: {mp.__file__}")
    
    # Check if it's the official PyMeep
    print(f"\n3. Checking if this is official PyMeep...")
    has_medium = hasattr(mp, 'Medium')
    has_cylinder = hasattr(mp, 'Cylinder')
    has_simulation = hasattr(mp, 'Simulation')
    has_vector3 = hasattr(mp, 'Vector3')
    
    print(f"   mp.Medium: {'✓' if has_medium else '✗'}")
    print(f"   mp.Cylinder: {'✓' if has_cylinder else '✗'}")
    print(f"   mp.Simulation: {'✓' if has_simulation else '✗'}")
    print(f"   mp.Vector3: {'✓' if has_vector3 else '✗'}")
    
    if has_medium and has_cylinder and has_simulation and has_vector3:
        print(f"\n   🎉 SUCCESS! You have official PyMeep installed!")
        print(f"   Version: {mp.__version__ if hasattr(mp, '__version__') else 'Unknown'}")
        print(f"\n   You can now use band structure and EM simulation features.")
    else:
        print(f"\n   ✗ WRONG PACKAGE! This is NOT the official PyMeep.")
        print(f"   You have an incompatible 'meep' package from PyPI.")
        print(f"\n   ⚠️  THE PROBLEM:")
        print(f"   'pip install meep' installs the WRONG package!")
        print(f"   The official PyMeep cannot be installed via pip alone.")
        
except ImportError as e:
    print(f"   ✗ Cannot import 'meep': {e}")
    print(f"\n   This means 'meep' is not installed in this environment.")

# Provide installation instructions
print(f"\n" + "="*80)
print("INSTALLATION INSTRUCTIONS")
print("="*80)

print(f"\n📦 WRONG METHOD (what you did):")
print(f"   pip install meep  ← This installs the WRONG package!")

print(f"\n✅ CORRECT METHOD - Option 1 (Recommended):")
print(f"   Use conda to install official PyMeep:")
print(f"   ")
print(f"   # Install conda if needed:")
print(f"   wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh")
print(f"   bash Miniconda3-latest-Linux-x86_64.sh")
print(f"   ")
print(f"   # Create new conda environment:")
print(f"   conda create -n meep_env python=3.10")
print(f"   conda activate meep_env")
print(f"   ")
print(f"   # Install official PyMeep:")
print(f"   conda install -c conda-forge pymeep")
print(f"   ")
print(f"   # Install other dependencies:")
print(f"   pip install matplotlib numpy")
print(f"   ")
print(f"   # Run your script:")
print(f"   python testing.py")

print(f"\n✅ CORRECT METHOD - Option 2 (If you must use your .venv):")
print(f"   PyMeep from source is very complex, but possible:")
print(f"   ")
print(f"   # First uninstall wrong package:")
print(f"   pip uninstall meep")
print(f"   ")
print(f"   # Install system dependencies (Ubuntu/Debian):")
print(f"   sudo apt-get install build-essential libhdf5-dev libopenmpi-dev")
print(f"   sudo apt-get install libfftw3-dev libgsl-dev libblas-dev liblapack-dev")
print(f"   ")
print(f"   # Then follow: https://meep.readthedocs.io/en/latest/Build_From_Source/")
print(f"   # Warning: This is VERY complicated and error-prone!")

print(f"\n💡 RECOMMENDED QUICK FIX:")
print(f"   1. Uninstall wrong package:")
print(f"      pip uninstall meep")
print(f"   ")
print(f"   2. Use conda (much easier):")
print(f"      conda install -c conda-forge pymeep")
print(f"   ")
print(f"   3. OR just run without MEEP:")
print(f"      The GUI works fine without MEEP!")
print(f"      You just won't have EM simulation features.")

print(f"\n🔍 VERIFY INSTALLATION:")
print(f"   After installing, run this script again:")
print(f"   python diagnose_meep.py")

print(f"\n📚 DOCUMENTATION:")
print(f"   Official PyMeep: https://meep.readthedocs.io/")
print(f"   Installation: https://meep.readthedocs.io/en/latest/Installation/")

print(f"\n" + "="*80)
print("CURRENT STATUS SUMMARY")
print("="*80)

try:
    import meep as mp
    if hasattr(mp, 'Medium') and hasattr(mp, 'Cylinder'):
        print("✅ PyMeep is correctly installed - you're ready to go!")
    else:
        print("❌ Wrong 'meep' package detected - need to reinstall")
        print("   Action: pip uninstall meep, then conda install -c conda-forge pymeep")
except ImportError:
    print("❌ PyMeep not installed")
    print("   Action: conda install -c conda-forge pymeep")

print("="*80 + "\n")
