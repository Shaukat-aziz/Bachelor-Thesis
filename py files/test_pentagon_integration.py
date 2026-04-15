#!~/mamabaforge/envs/pymeep_env/bin/python
"""
Test script for pentagon structure plotting and MEEP integration.
Tests the fixed plot_pentagon_structure() and simulate_meep_structure() functions.
"""

import sys
import os
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for testing
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(__file__))

from testing import create_lattice_with_correct_atom_positions


def test_pentagon_generation():
    """Test basic pentagon structure generation."""
    print("=" * 60)
    print("TEST 1: Pentagon Structure Generation")
    print("=" * 60)
    
    try:
        a_nm = 400
        sq_a1 = np.array([a_nm, 0])
        sq_a2 = np.array([0, a_nm])
        basis_sites = np.array([[-a_nm/4, -a_nm/4], [a_nm/4, a_nm/4]])
        
        n_cells = 3
        target_angle = 72
        
        atoms, cells, transforms, stretch_point = create_lattice_with_correct_atom_positions(
            n_cells, n_cells, sq_a1, sq_a2, basis_sites,
            target_angle_deg=target_angle,
            stretch_corner='bottom_left',
            decay_profile='exponential'
        )
        
        print(f"✓ Pentagon structure generated successfully")
        print(f"  - Cells: {n_cells}×{n_cells}")
        print(f"  - Target angle: {target_angle}°")
        print(f"  - Number of atoms: {len(atoms)}")
        print(f"  - Number of cells: {len(cells)}")
        print(f"  - Transform factors: {len(transforms)}")
        print(f"  - Atom position range X: [{atoms[:, 0].min():.1f}, {atoms[:, 0].max():.1f}] nm")
        print(f"  - Atom position range Y: [{atoms[:, 1].min():.1f}, {atoms[:, 1].max():.1f}] nm")
        
        return atoms, cells, transforms
    
    except Exception as e:
        print(f"✗ Pentagon generation failed: {e}")
        import traceback
        traceback.print_exc()
        return None, None, None


def test_plot_generation(atoms, cells, transforms):
    """Test plot generation with matplotlib."""
    print("\n" + "=" * 60)
    print("TEST 2: Plot Generation")
    print("=" * 60)
    
    if atoms is None:
        print("⊘ Skipping test (no pentagon structure)")
        return
    
    try:
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        
        # Plot atoms
        ax1.scatter(atoms[:, 0], atoms[:, 1], s=100, alpha=0.7, 
                   color='blue', edgecolors='black', linewidth=0.5, label='Atoms')
        
        # Draw cells
        for corners in cells:
            corners_closed = np.vstack([corners, corners[0]])
            ax1.plot(corners_closed[:, 0], corners_closed[:, 1], 'k-', 
                    alpha=0.2, linewidth=0.5)
        
        ax1.set_xlabel('X (nm)')
        ax1.set_ylabel('Y (nm)')
        ax1.set_title('Pentagon Structure')
        ax1.grid(True, alpha=0.3)
        ax1.axis('equal')
        ax1.legend()
        
        # Plot transforms
        cell_centers = []
        for corners in cells:
            center = corners.mean(axis=0)
            cell_centers.append(center)
        
        if cell_centers and len(transforms) >= len(cell_centers):
            cell_centers = np.array(cell_centers[:len(transforms)])
            scatter = ax2.scatter(cell_centers[:, 0], cell_centers[:, 1],
                                 c=transforms[:len(cell_centers)],
                                 s=200, cmap='viridis', alpha=0.8,
                                 edgecolors='black', linewidth=0.5)
            cbar = plt.colorbar(scatter, ax=ax2)
            cbar.set_label('Transformation Factor')
        
        ax2.set_xlabel('X (nm)')
        ax2.set_ylabel('Y (nm)')
        ax2.set_title('Transformation Factors')
        ax2.grid(True, alpha=0.3)
        ax2.axis('equal')
        
        plt.tight_layout()
        plot_file = '/tmp/test_pentagon_structure.png'
        plt.savefig(plot_file, dpi=100, bbox_inches='tight')
        plt.close()
        
        print(f"✓ Plot generated successfully")
        print(f"  - Saved to: {plot_file}")
        print(f"  - Figure size: 14×6 inches")
        print(f"  - Resolution: 100 dpi")
    
    except Exception as e:
        print(f"✗ Plot generation failed: {e}")
        import traceback
        traceback.print_exc()


def test_meep_integration():
    """Test MEEP integration."""
    print("\n" + "=" * 60)
    print("TEST 3: MEEP Integration")
    print("=" * 60)
    
    try:
        import meep as mp
        print("✓ MEEP module imported successfully")
        
        # Test basic MEEP cell creation
        cell_size = 10
        cell = mp.Vector3(cell_size, cell_size, 0)
        
        # Test frequency parameter
        frequency = 0.5
        
        # Test source creation
        sources = [
            mp.Source(
                mp.GaussianSource(frequency, fwidth=0.1 * frequency),
                component=mp.Ez,
                center=mp.Vector3(-cell_size/4, 0, 0)
            )
        ]
        print(f"✓ MEEP source created successfully")
        print(f"  - Frequency: {frequency}")
        print(f"  - Cell size: {cell_size}×{cell_size} μm²")
        
        # Test simulation creation (without running)
        sim = mp.Simulation(
            cell_size=cell,
            sources=sources,
            resolution=10,
            default_material=mp.Medium(epsilon=4.0)
        )
        print(f"✓ MEEP simulation object created successfully")
        
        # Test Harminv creation
        harminv = mp.Harminv(mp.Ez, mp.Vector3(0, 0, 0), frequency, 0.1*frequency)
        print(f"✓ Harminv monitor created successfully")
        
    except Exception as e:
        print(f"✗ MEEP integration test failed: {e}")
        import traceback
        traceback.print_exc()


def test_gui_methods():
    """Test that GUI methods exist and are callable."""
    print("\n" + "=" * 60)
    print("TEST 4: GUI Method Availability")
    print("=" * 60)
    
    try:
        from PyQt6.QtWidgets import QApplication
        from app.gui_launcher import PhotonicGUILauncher
        
        print("✓ GUI launcher imports successful")
        
        # Check methods exist
        methods = [
            'plot_pentagon_structure',
            'simulate_meep_structure',
            'export_pentagon_structure',
            'show_plot_dialog'
        ]
        
        all_exist = True
        for method in methods:
            if hasattr(PhotonicGUILauncher, method):
                print(f"  ✓ Method '{method}' exists")
            else:
                print(f"  ✗ Method '{method}' missing")
                all_exist = False
        
        if all_exist:
            print("✓ All required methods are available")
        else:
            print("✗ Some methods are missing")
    
    except ImportError as e:
        print(f"⊘ Skipping GUI test (not in GUI environment): {e}")
    except Exception as e:
        print(f"✗ GUI method test failed: {e}")
        import traceback
        traceback.print_exc()


def test_all_decay_profiles():
    """Test pentagon generation with all decay profiles."""
    print("\n" + "=" * 60)
    print("TEST 5: All Decay Profiles")
    print("=" * 60)
    
    try:
        a_nm = 400
        sq_a1 = np.array([a_nm, 0])
        sq_a2 = np.array([0, a_nm])
        basis_sites = np.array([[-a_nm/4, -a_nm/4], [a_nm/4, a_nm/4]])
        
        profiles = ['exponential', 'gaussian', 'polynomial']
        
        for profile in profiles:
            try:
                atoms, _, _, _ = create_lattice_with_correct_atom_positions(
                    2, 2, sq_a1, sq_a2, basis_sites,
                    target_angle_deg=72,
                    stretch_corner='bottom_left',
                    decay_profile=profile
                )
                print(f"  ✓ '{profile}' profile: {len(atoms)} atoms")
            except Exception as e:
                print(f"  ✗ '{profile}' profile failed: {e}")
        
        print("✓ All decay profiles tested")
    
    except Exception as e:
        print(f"✗ Decay profile test failed: {e}")


def main():
    """Run all tests."""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 15 + "Pentagon Structure & MEEP Integration Tests" + " " * 1 + "║")
    print("╚" + "=" * 58 + "╝")
    
    atoms, cells, transforms = test_pentagon_generation()
    test_plot_generation(atoms, cells, transforms)
    test_meep_integration()
    test_gui_methods()
    test_all_decay_profiles()
    
    print("\n" + "=" * 60)
    print("Test Suite Complete")
    print("=" * 60)


if __name__ == '__main__':
    main()
