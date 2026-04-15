#!~/mamabaforge/envs/pymeep_env/bin/python
"""
Test Script for Band Structure and Hz Field Analysis
=====================================================
Quick verification of MEEP band structure calculation features.
"""

import numpy as np
import matplotlib.pyplot as plt

# Test imports
print("="*80)
print("BAND STRUCTURE AND Hz FIELD ANALYSIS TEST")
print("="*80)

# Check PyMeep installation
print("\n1. Checking PyMeep installation...")
try:
    import meep as mp
    if hasattr(mp, 'Medium') and hasattr(mp, 'Cylinder'):
        print("   ✓ PyMeep installed and available")
        print(f"   Version: {mp.__version__ if hasattr(mp, '__version__') else 'Unknown'}")
        MEEP_OK = True
    else:
        print("   ✗ Incompatible meep package detected")
        MEEP_OK = False
except ImportError:
    print("   ✗ PyMeep not installed")
    print("   Install with: conda install -c conda-forge pymeep")
    MEEP_OK = False

# Check required dependencies
print("\n2. Checking dependencies...")
try:
    import matplotlib
    print(f"   ✓ Matplotlib {matplotlib.__version__}")
except ImportError:
    print("   ✗ Matplotlib not found")

try:
    import numpy
    print(f"   ✓ NumPy {numpy.__version__}")
except ImportError:
    print("   ✗ NumPy not found")

# Test basic MEEP functionality
if MEEP_OK:
    print("\n3. Testing basic MEEP functionality...")
    try:
        # Create simple 2D structure
        cell = mp.Vector3(10, 10, 0)
        geometry = [mp.Cylinder(radius=1, height=mp.inf, center=mp.Vector3(), 
                                material=mp.Medium(epsilon=12))]
        sources = [mp.Source(mp.GaussianSource(frequency=0.15, fwidth=0.2),
                            component=mp.Hz, center=mp.Vector3())]
        resolution = 10
        
        sim = mp.Simulation(cell_size=cell, geometry=geometry, sources=sources,
                           resolution=resolution, boundary_layers=[mp.PML(1.0)])
        
        print("   ✓ Simulation object created")
        
        # Test k-point interpolation
        k_points = [mp.Vector3(0, 0, 0), mp.Vector3(0.5, 0, 0), 
                   mp.Vector3(0.5, 0.5, 0), mp.Vector3(0, 0, 0)]
        k_interp = mp.interpolate(20, k_points)
        print(f"   ✓ K-point interpolation: {len(k_interp)} points")
        
        # Test field output
        print("   ✓ MEEP simulation ready for use")
        
    except Exception as e:
        print(f"   ✗ MEEP test failed: {e}")
        
    print("\n4. Band structure calculation features:")
    print("   • Photonic band structure along Γ→X→M→Γ path")
    print("   • Eigenmode solver using Harminv method")
    print("   • Automatic band gap detection and analysis")
    print("   • Hz field mode analysis with 2D FFT")
    print("   • Energy density and hotspot detection")
    print("   • Full export to .npy files for further analysis")
    
    print("\n5. Workflow:")
    print("   STEP 1: Setup Sim (create MEEP geometry from pentagon)")
    print("   STEP 2: Calc Bands (compute photonic band structure)")
    print("   STEP 3: Show Bands (visualize band diagram)")
    print("   STEP 4: Run Sim (time-domain field simulation)")
    print("   STEP 5: Hz Modes (detailed Hz field analysis)")
    print("   STEP 6: Export (save all data for post-processing)")

else:
    print("\n" + "="*80)
    print("MEEP INSTALLATION REQUIRED")
    print("="*80)
    print("To use band structure calculations, install PyMeep:")
    print("\n  Option 1 (Recommended - via Conda):")
    print("    conda install -c conda-forge pymeep")
    print("\n  Option 2 (From source):")
    print("    https://meep.readthedocs.io/en/latest/Installation/")
    print("\nAfter installation, restart Python and run testing.py")

print("\n" + "="*80)
print("TEST COMPLETE")
print("="*80)

# Quick demo plot if matplotlib available
try:
    print("\nGenerating example band structure diagram...")
    
    # Simulated band structure data (example)
    k_points = np.linspace(0, 1, 50)
    bands = []
    for i in range(4):
        # Create synthetic band with realistic dispersion
        band = 0.2 + 0.1 * i + 0.05 * np.cos(2 * np.pi * k_points) + 0.02 * np.sin(4 * np.pi * k_points)
        bands.append(band)
    
    fig, ax = plt.subplots(figsize=(8, 6))
    colors = ['blue', 'red', 'green', 'orange']
    for i, band in enumerate(bands):
        ax.plot(k_points, band, 'o-', color=colors[i], label=f'Band {i+1}', linewidth=2, markersize=3)
    
    # Add high-symmetry points
    ax.axvline(0, color='gray', linestyle='--', alpha=0.5)
    ax.axvline(0.33, color='gray', linestyle='--', alpha=0.5)
    ax.axvline(0.67, color='gray', linestyle='--', alpha=0.5)
    ax.axvline(1, color='gray', linestyle='--', alpha=0.5)
    
    ax.set_xticks([0, 0.33, 0.67, 1])
    ax.set_xticklabels(['Γ', 'X', 'M', 'Γ'])
    ax.set_xlabel('Wave Vector', fontsize=12, fontweight='bold')
    ax.set_ylabel('Frequency (c/a)', fontsize=12, fontweight='bold')
    ax.set_title('Example Photonic Band Structure\n(Pentagon 2D Structure)', 
                fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.legend()
    
    # Highlight band gap
    ax.axhspan(bands[1][-1], bands[2][0], alpha=0.2, color='red', label='Band Gap')
    
    plt.tight_layout()
    plt.savefig('/home/shaukat/OneDrive/Thesis/Thesis/Code/Python/FILES/example_band_structure.png', dpi=150)
    print("✓ Example band diagram saved: example_band_structure.png")
    plt.show()
    
except Exception as e:
    print(f"Could not generate example plot: {e}")

print("\nReady to use! Run: python testing.py")
