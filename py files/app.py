#!~/mamabaforge/envs/pymeep_env/bin/python
"""
Pentagon Photonic Crystal Simulator - Application Launcher & Editor
====================================================================

Unified application launcher combining:
- Application environment setup and dependency checking
- Pentagon structure principles (decay functions, transformations, lattice editing)
- Photonic simulator GUI integration
- Periodic lattice visualization
- Transformation matrix operations
- Electromagnetic simulation controls

Architecture:
├── PentagonStructureManager       [Core pentagon lattice operations]
│   ├── Decay functions            [exponential, gaussian, polynomial, custom]
│   ├── Transformation matrices    [Atom position transformations]
│   ├── Lattice creation           [Atom positioning with decay]
│   └── Export/Import operations   [Save/load configurations]
│
├── AppLauncher                    [Environment setup & dependency check]
│   ├── Dependency checking        [numpy, matplotlib, scipy, meep, gpu]
│   ├── GPU detection              [NVIDIA, Intel Iris, experimental]
│   ├── GUI launching              [testing.py, photonic_simulator.py]
│   └── Configuration management   [Save/load application state]
│
└── PentagonPhotonicsApp           [Integrated application controller]
    ├── GUI integration            [testing.py, photonic_simulator.py]
    ├── Lattice manipulation       [Decay, rotation, stretching]
    ├── Band structure analysis    [Periodic & cavity modes]
    └── MEEP simulation control    [EM field calculations]
"""

import sys
import os
import subprocess
import platform
import argparse
import numpy as np
import json
import pickle
from pathlib import Path
from typing import Tuple, List, Dict, Optional

# Version info
APP_VERSION = "2.1.0"
APP_NAME = "Pentagon Photonic Crystal Simulator"
APP_ARCHITECTURE = "Pentagon Structure + Photonic Simulator v2.1"


# ============================================================================
# PENTAGON STRUCTURE MANAGER - Core Lattice Operations
# ============================================================================

class PentagonStructureManager:
    """
    Manages pentagon lattice structure operations following testing.py principles:
    - Decay functions (exponential, gaussian, polynomial, custom)
    - Lattice transformations with variable angle and stretching
    - Atom position calculations with transformation matrices
    - Export/import of configurations
    
    This class bridges the gap between:
    - testing.py: Interactive pentagon GUI
    - photonic_simulator.py: Photonic crystal analysis
    - lattice_structures.py: Periodic lattice definitions
    """
    
    def __init__(self, n_cells: int = 3, a_nm: float = 469.0):
        """
        Initialize pentagon structure manager.
        
        Parameters
        ----------
        n_cells : int
            Number of cells in each direction (typically 3)
        a_nm : float
            Lattice constant in nanometers (default: 469 nm)
        """
        self.n_cells = n_cells
        self.a_nm = a_nm
        self.basis_offset = 0.54 * a_nm / np.sqrt(2)
        
        # Lattice vectors
        self.sq_a1 = np.array([a_nm, 0.0])
        self.sq_a2 = np.array([0.0, a_nm])
        
        # Basis sites (4 atoms per unit cell)
        self.basis_sites_square = np.array([
            [self.basis_offset, self.basis_offset],
            [-self.basis_offset, self.basis_offset],
            [self.basis_offset, -self.basis_offset],
            [-self.basis_offset, -self.basis_offset],
        ])
        
        # Configuration state
        self.target_angle = 72.0
        self.decay_profile = 'exponential'
        self.decay_rate = 1.0
        self.custom_decay_equation = 'exp(-3*x)'
        self.global_scale = 1.0
        self.stretch_corner = 'bottom_left'
        
        # Transformation data
        self.current_atoms = None
        self.current_transformation_matrix = None
        self.current_cell_corners = None
    
    def decay_function(self, distance: float, max_distance: float, 
                      profile: str = 'exponential') -> float:
        """
        Calculate decay factor based on distance from stretching point.
        
        Implements multiple decay profiles for lattice deformation:
        - exponential: Smooth, fast decay near stretching point
        - gaussian: Gaussian bell curve, smooth rolloff
        - polynomial: Power law decay
        - custom: User-defined equation
        
        Parameters
        ----------
        distance : float
            Distance from stretching point
        max_distance : float
            Maximum distance (lattice span)
        profile : str
            Decay profile type
        
        Returns
        -------
        float
            Decay factor in range [0, 1]
        """
        normalized_dist = np.clip(distance / max_distance, 0, 1)
        
        if profile == 'exponential':
            decay_rate = 3.0 * self.decay_rate
            factor = np.exp(-decay_rate * normalized_dist)
        
        elif profile == 'gaussian':
            sigma = 0.35
            factor = np.exp(-(normalized_dist / sigma) ** 2)
        
        elif profile == 'polynomial':
            power = 3
            factor = (1 - normalized_dist) ** power
        
        elif profile == 'custom':
            try:
                x = normalized_dist
                safe_dict = {
                    'exp': np.exp, 'sin': np.sin, 'cos': np.cos, 'tan': np.tan,
                    'sqrt': np.sqrt, 'log': np.log, 'log10': np.log10, 'abs': np.abs,
                    'x': x, 'np': np, 'pi': np.pi, 'e': np.e
                }
                factor = eval(self.custom_decay_equation, {"__builtins__": {}}, safe_dict)
                factor = np.clip(factor, 0, 1) if np.isfinite(factor) else 0.0
            except:
                factor = 1 - normalized_dist  # Fallback to linear
        
        else:  # default linear
            factor = 1 - normalized_dist
        
        return factor
    
    def create_lattice_with_deformation(self) -> Tuple[np.ndarray, List, np.ndarray]:
        """
        Create deformed lattice with decay-based transformation.
        
        Returns
        -------
        all_atoms : ndarray
            All atom positions
        cell_corners : list
            Cell corner coordinates
        transformation_factors : ndarray
            Transformation factor for each cell
        """
        n_verts_x = self.n_cells + 1
        n_verts_y = self.n_cells + 1
        
        vix = np.arange(n_verts_x) - self.n_cells // 2
        viy = np.arange(n_verts_y) - self.n_cells // 2
        
        # Determine stretch point
        if self.stretch_corner == 'bottom_left':
            i_stretch, j_stretch = 0, 0
        elif self.stretch_corner == 'bottom_right':
            i_stretch, j_stretch = n_verts_x - 1, 0
        elif self.stretch_corner == 'top_left':
            i_stretch, j_stretch = 0, n_verts_y - 1
        else:  # top_right
            i_stretch, j_stretch = n_verts_x - 1, n_verts_y - 1
        
        # Create vertices in square lattice
        vertices_square = {}
        stretch_vertex_sq = None
        
        for i, vi in enumerate(vix):
            for j, vj in enumerate(viy):
                pos = np.array([vi * self.sq_a1[0], vj * self.sq_a2[1]])
                vertices_square[(i, j)] = pos
                if i == i_stretch and j == j_stretch:
                    stretch_vertex_sq = pos.copy()
        
        # Find farthest vertex for max_distance
        far_i = n_verts_x - 1 if i_stretch == 0 else 0
        far_j = n_verts_y - 1 if j_stretch == 0 else 0
        far_vertex_sq = vertices_square[(far_i, far_j)]
        max_distance = np.linalg.norm(far_vertex_sq - stretch_vertex_sq)
        
        # Target parallelogram basis (rotated)
        a_mag = np.linalg.norm(self.sq_a1)
        target_angle_rad = np.deg2rad(self.target_angle)
        para_a1 = np.array([a_mag, 0.0])
        para_a2 = a_mag * np.array([np.cos(target_angle_rad), np.sin(target_angle_rad)])
        
        # Deform vertices
        vertices_deformed = {}
        for (i, j), pos_sq in vertices_square.items():
            dist = np.linalg.norm(pos_sq - stretch_vertex_sq)
            alpha = self.decay_function(dist, max_distance, self.decay_profile)
            
            # Linear combination: alpha * square + (1-alpha) * parallelogram
            frac_i = i / (n_verts_x - 1) if n_verts_x > 1 else 0
            frac_j = j / (n_verts_y - 1) if n_verts_y > 1 else 0
            
            pos_para = frac_i * para_a1 + frac_j * para_a2
            pos_deformed = alpha * pos_sq + (1 - alpha) * pos_para
            
            vertices_deformed[(i, j)] = pos_deformed
        
        # Create cells and place atoms
        all_atoms = []
        cell_corners_list = []
        transformation_factors = []
        
        basis_frac = self.basis_sites_square / a_mag
        
        for i in range(self.n_cells):
            for j in range(self.n_cells):
                # Get vertices of this cell
                corners = [
                    vertices_deformed[(i, j)],
                    vertices_deformed[(i+1, j)],
                    vertices_deformed[(i+1, j+1)],
                    vertices_deformed[(i, j+1)],
                ]
                cell_corners_list.append(corners)
                
                # Place atoms at fractional positions within cell
                cell_center = np.mean(corners, axis=0)
                cell_basis_a1 = corners[1] - corners[0]
                cell_basis_a2 = corners[3] - corners[0]
                
                trans_factor = 1.0  # Could be made position-dependent
                transformation_factors.append(trans_factor)
                
                for basis_idx in range(len(self.basis_sites_square)):
                    frac_x, frac_y = basis_frac[basis_idx]
                    atom_pos = corners[0] + frac_x * cell_basis_a1 + frac_y * cell_basis_a2
                    all_atoms.append(atom_pos)
        
        all_atoms = np.array(all_atoms)
        transformation_factors = np.array(transformation_factors)
        
        # Center at stretch point
        acute_corner_position = vertices_deformed[(i_stretch, j_stretch)]
        all_atoms = all_atoms - acute_corner_position
        cell_corners_list = [np.array(corners) - acute_corner_position for corners in cell_corners_list]
        
        self.current_atoms = all_atoms
        self.current_cell_corners = cell_corners_list
        
        return all_atoms, cell_corners_list, transformation_factors
    
    def create_transformation_matrix(self) -> np.ndarray:
        """
        Create 36×36 transformation matrix for atom positions.
        
        Format: Row = atom index, Columns = [x₁, y₁, x₂, y₂, ..., x₁₈, y₁₈]
        
        Returns
        -------
        matrix : ndarray
            36×36 transformation matrix
        """
        atoms, _, _ = self.create_lattice_with_deformation()
        
        # Original atoms (square lattice reference)
        a_mag = np.linalg.norm(self.sq_a1)
        basis_frac = self.basis_sites_square / a_mag
        
        atoms_original = []
        for i in range(self.n_cells):
            for j in range(self.n_cells):
                for basis_idx, (fx, fy) in enumerate(basis_frac):
                    x = i * self.a_nm + fx * self.a_nm
                    y = j * self.a_nm + fy * self.a_nm
                    atoms_original.append([x, y])
        
        atoms_original = np.array(atoms_original)
        
        # Create 36×36 matrix
        max_atoms = 36
        matrix = np.zeros((36, 36))
        
        num_atoms = min(len(atoms), max_atoms // 2)
        
        for atom_idx in range(num_atoms):
            x_col = 2 * atom_idx
            y_col = 2 * atom_idx + 1
            
            if atom_idx < len(atoms):
                matrix[atom_idx, x_col] = atoms[atom_idx, 0] * self.global_scale
                matrix[atom_idx, y_col] = atoms[atom_idx, 1] * self.global_scale
        
        self.current_transformation_matrix = matrix
        return matrix
    
    def export_configuration(self, filepath: str) -> bool:
        """
        Export current configuration to JSON file.
        
        Parameters
        ----------
        filepath : str
            Path to save configuration
        
        Returns
        -------
        bool
            Success status
        """
        try:
            config = {
                'n_cells': self.n_cells,
                'a_nm': self.a_nm,
                'target_angle': self.target_angle,
                'decay_profile': self.decay_profile,
                'decay_rate': self.decay_rate,
                'custom_decay_equation': self.custom_decay_equation,
                'global_scale': self.global_scale,
                'stretch_corner': self.stretch_corner,
            }
            
            with open(filepath, 'w') as f:
                json.dump(config, f, indent=2)
            
            return True
        except Exception as e:
            print(f"Export failed: {e}")
            return False
    
    def import_configuration(self, filepath: str) -> bool:
        """
        Import configuration from JSON file.
        
        Parameters
        ----------
        filepath : str
            Path to load configuration
        
        Returns
        -------
        bool
            Success status
        """
        try:
            with open(filepath, 'r') as f:
                config = json.load(f)
            
            self.n_cells = config.get('n_cells', self.n_cells)
            self.a_nm = config.get('a_nm', self.a_nm)
            self.target_angle = config.get('target_angle', self.target_angle)
            self.decay_profile = config.get('decay_profile', self.decay_profile)
            self.decay_rate = config.get('decay_rate', self.decay_rate)
            self.custom_decay_equation = config.get('custom_decay_equation', self.custom_decay_equation)
            self.global_scale = config.get('global_scale', self.global_scale)
            self.stretch_corner = config.get('stretch_corner', self.stretch_corner)
            
            return True
        except Exception as e:
            print(f"Import failed: {e}")
            return False
    
    def get_summary(self) -> str:
        """Get text summary of current configuration."""
        return f"""
Pentagon Structure Configuration:
  - Grid: {self.n_cells}×{self.n_cells}
  - Lattice constant: {self.a_nm:.1f} nm
  - Target angle: {self.target_angle:.1f}°
  - Decay profile: {self.decay_profile}
  - Decay rate: {self.decay_rate:.2f}x
  - Global scale: {self.global_scale:.2f}x
  - Stretch corner: {self.stretch_corner}
  - Custom equation: {self.custom_decay_equation}
"""


# ============================================================================
# APPLICATION LAUNCHER - Environment & Dependency Management
# ============================================================================

class AppLauncher:
    """
    Manages application launch, environment setup, and dependency checking.
    Integrates with PentagonStructureManager and GUI frameworks.
    """
    
    def __init__(self):
        """Initialize launcher with system information and pentagon manager."""
        self.system = platform.system()
        self.python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        
        # Get app directory
        self.app_dir = Path(__file__).parent
        self.files_dir = self.app_dir.parent
        
        # Setup Python paths
        sys.path.insert(0, str(self.app_dir))
        sys.path.insert(0, str(self.files_dir))
        
        self.env = os.environ.copy()
        
        # Initialize pentagon structure manager (core lattice operations)
        self.pentagon_manager = PentagonStructureManager(n_cells=3, a_nm=469.0)
    
    def print_banner(self):
        """Print application banner with integrated architecture info."""
        print("\n" + "="*80)
        print(f"  {APP_NAME}")
        print(f"  Version: {APP_VERSION}")
        print(f"  Architecture: {APP_ARCHITECTURE}")
        print(f"  Python: {self.python_version}")
        print(f"  Platform: {self.system}")
        print("="*80 + "\n")
    
    def check_dependencies(self, verbose=False):
        """Check for required and optional dependencies."""
        print("Checking dependencies...")
        print("-"*80)
        
        required = {
            'numpy': 'NumPy - Numerical computing',
            'matplotlib': 'Matplotlib - Plotting library',
            'scipy': 'SciPy - Scientific computing',
        }
        
        optional = {
            'meep': 'PyMeep - MEEP electromagnetic simulator',
            'cupy': 'CuPy - GPU-accelerated NumPy',
            'torch': 'PyTorch - GPU/ML framework',
            'jax': 'JAX - GPU computing',
        }
        
        missing_required = []
        missing_optional = []
        
        # Check required packages
        for package, description in required.items():
            try:
                __import__(package)
                status = "✓"
                if verbose:
                    print(f"{status} {description:<50} INSTALLED")
            except ImportError:
                status = "✗"
                print(f"{status} {description:<50} MISSING (REQUIRED)")
                missing_required.append(package)
        
        # Check optional packages
        for package, description in optional.items():
            try:
                __import__(package)
                status = "✓"
                if verbose:
                    print(f"{status} {description:<50} AVAILABLE")
            except ImportError:
                status = "◌"
                if verbose:
                    print(f"{status} {description:<50} not installed (optional)")
                missing_optional.append(package)
        
        print("-"*80)
        
        if missing_required:
            print(f"\n❌ Missing REQUIRED packages: {', '.join(missing_required)}")
            print(f"\nInstall with:")
            print(f"  pip install {' '.join(missing_required)}")
            return False
        
        if missing_optional:
            print(f"\n⚠ Optional packages not installed: {', '.join(missing_optional)}")
            print("The application will work, but some features will be limited.")
            print("\nFor GPU acceleration, install:")
            print("  pip install cupy-cuda11x  (replace 11x with your CUDA version)")
            print("  OR")
            print("  conda install -c conda-forge cupy")
        else:
            print("\n✓ All dependencies satisfied!")
        
        print()
        return True
    
    def check_gpu(self):
        """Check GPU availability."""
        print("GPU Detection")
        print("-"*80)
        
        gpu_detected = False
        
        # Check CUDA
        try:
            import torch  # type: ignore
            if torch.cuda.is_available():
                gpu_detected = True
                print(f"✓ CUDA GPU detected: {torch.cuda.get_device_name(0)}")
                print(f"  CUDA Version: {torch.version.cuda}")
                print(f"  Device Count: {torch.cuda.device_count()}")
        except ImportError:
            pass
        
        # Check CuPy
        try:
            import cupy as cp  # type: ignore
            print(f"✓ CuPy GPU support available")
            print(f"  GPU: {cp.cuda.Device().get_device_name().decode('utf-8')}")
            gpu_detected = True
        except ImportError:
            pass
        
        # Check JAX
        try:
            import jax  # type: ignore
            if len(jax.devices('gpu')) > 0:
                print(f"✓ JAX GPU support available")
                gpu_detected = True
        except ImportError:
            pass
        
        # Check NVIDIA GPU drivers
        if self.system in ['Linux', 'Darwin']:
            try:
                result = subprocess.run(['nvidia-smi', '--query-gpu=name', '--format=csv,noheader'],
                                       capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    gpus = result.stdout.strip().split('\n')
                    print(f"✓ NVIDIA GPU drivers installed: {gpus[0]}")
                    gpu_detected = True
            except (FileNotFoundError, subprocess.TimeoutExpired):
                pass
        
        if not gpu_detected:
            print("⚠ No GPU detected. Application will run on CPU.")
            print("  For GPU acceleration:")
            print("  - Install NVIDIA CUDA toolkit")
            print("  - Install cupy: pip install cupy-cuda11x")
        
        print()
        return gpu_detected
    
    def launch_gui(self, debug=False):
        """Launch the main GUI application."""
        print("Launching application...")
        print("-"*80)
        
        testing_file = self.app_dir / "testing.py"
        
        if not testing_file.exists():
            print(f"❌ ERROR: GUI file not found: {testing_file}")
            return False
        
        try:
            # Set environment variables for GPU if available
            os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # Suppress TensorFlow warnings
            os.environ['CUDA_LAUNCH_BLOCKING'] = '0'   # Async GPU operations
            
            # Run the GUI
            cmd = [sys.executable, str(testing_file)]
            
            if debug:
                print(f"Running: {' '.join(cmd)}")
                print("-"*80)
                # Run in foreground for debug
                subprocess.run(cmd, env=self.env)
            else:
                # Run in background
                if self.system == 'Windows':
                    subprocess.Popen(cmd, env=self.env,   # type: ignore
                                   creationflags=subprocess.CREATE_NO_WINDOW)  # type: ignore
                else:
                    subprocess.Popen(cmd, env=self.env, 
                                   stdout=subprocess.DEVNULL, 
                                   stderr=subprocess.DEVNULL)
                print("✓ Application launched successfully!")
                print("  Check the window that opened on your desktop.")
            
            return True
            
        except Exception as e:
            print(f"❌ ERROR launching application: {e}")
            return False
    
    def show_pentagon_structure_info(self):
        """Display pentagon structure capabilities and decay functions."""
        print("\n" + "="*80)
        print("PENTAGON STRUCTURE CAPABILITIES")
        print("="*80)
        print(self.pentagon_manager.get_summary())
        
        print("Decay Function Profiles:")
        print("  ✓ Exponential  - Fast decay near stretching point")
        print("  ✓ Gaussian     - Smooth bell curve rolloff")
        print("  ✓ Polynomial   - Power law (x^3) decay")
        print("  ✓ Custom       - User-defined equations with x, sin, cos, exp, etc.")
        
        print("\nLattice Transformation Features:")
        print("  ✓ Target angle control (e.g., 72° for pentagon)")
        print("  ✓ Corner stretching with smooth decay")
        print("  ✓ 36×36 transformation matrices")
        print("  ✓ Atom position tracking")
        print("  ✓ Export/import configurations (JSON)")
        
        print("\nIntegration with:")
        print("  ✓ testing.py - Interactive pentagon GUI")
        print("  ✓ photonic_simulator.py - Photonic crystal analysis")
        print("  ✓ lattice_structures.py - Periodic lattice definitions")
        print("="*80 + "\n")
    
    def test_pentagon_structure(self):
        """Test pentagon structure manager."""
        print("\n" + "="*80)
        print("TESTING PENTAGON STRUCTURE MANAGER")
        print("="*80)
        
        try:
            # Test 1: Create lattice with default config
            print("\n1. Creating lattice with exponential decay...")
            atoms, corners, factors = self.pentagon_manager.create_lattice_with_deformation()
            print(f"   ✓ Generated {len(atoms)} atoms")
            print(f"   ✓ {len(corners)} cells")
            
            # Test 2: Create transformation matrix
            print("\n2. Creating transformation matrix...")
            matrix = self.pentagon_manager.create_transformation_matrix()
            print(f"   ✓ {matrix.shape} matrix created")
            print(f"   ✓ Min value: {matrix.min():.2f}")
            print(f"   ✓ Max value: {matrix.max():.2f}")
            
            # Test 3: Export configuration
            config_file = Path("/tmp/pentagon_config_test.json")
            print(f"\n3. Exporting configuration...")
            if self.pentagon_manager.export_configuration(str(config_file)):
                print(f"   ✓ Saved to {config_file}")
            
            # Test 4: Import configuration
            print(f"\n4. Importing configuration...")
            if self.pentagon_manager.import_configuration(str(config_file)):
                print(f"   ✓ Loaded from {config_file}")
            
            # Test 5: Test different decay profiles
            print(f"\n5. Testing decay profiles...")
            for profile in ['exponential', 'gaussian', 'polynomial']:
                self.pentagon_manager.decay_profile = profile
                decay_val = self.pentagon_manager.decay_function(5.0, 10.0, profile)
                print(f"   ✓ {profile}: decay(5/10) = {decay_val:.3f}")
            
            print("\n" + "="*80)
            print("✓ ALL PENTAGON STRUCTURE TESTS PASSED")
            print("="*80 + "\n")
            
        except Exception as e:
            print(f"\n✗ ERROR: {e}")
            import traceback
            traceback.print_exc()
    
    def show_help(self):
        """Show comprehensive help with pentagon structure features."""
        print(f"\n{APP_NAME} v{APP_VERSION}")
        print(f"Architecture: {APP_ARCHITECTURE}")
        
        print("\nUsage: python app.py [OPTIONS]")
        print("\nCore Options:")
        print("  --help, -h          Show this help message")
        print("  --version            Show version information")
        print("  --check              Check dependencies only")
        print("  --gpu                Show GPU information")
        print("  --verbose, -v        Verbose output")
        print("  --debug              Run in debug mode (foreground)")
        
        print("\nPentagon Structure Options:")
        print("  --pentagon           Show pentagon structure capabilities")
        print("  --test-pentagon      Test pentagon structure manager")
        print("  --export-config FILE Export pentagon config to JSON")
        print("  --import-config FILE Import pentagon config from JSON")
        
        print("\nExamples:")
        print("  python app.py                    # Launch application")
        print("  python app.py --check            # Check dependencies")
        print("  python app.py --pentagon         # Show pentagon features")
        print("  python app.py --test-pentagon    # Test pentagon manager")
        print("  python app.py --export-config c.json")
        print("  python app.py --import-config c.json")
        print()
    
    def check_dependencies(self, verbose: bool = False) -> bool:
        """Check if all required dependencies are installed."""
        required = ['numpy', 'matplotlib']
        optional = ['scipy', 'meep']
        
        all_found = True
        
        for pkg in required:
            try:
                __import__(pkg)
                if verbose:
                    print(f"  ✓ {pkg:20}")
            except ImportError:
                if verbose:
                    print(f"  ✗ {pkg:20} MISSING (required)")
                all_found = False
        
        for pkg in optional:
            try:
                __import__(pkg)
                if verbose:
                    print(f"  ✓ {pkg:20} (optional)")
            except ImportError:
                if verbose:
                    print(f"  ◯ {pkg:20} (optional - not installed)")
        
        return all_found
    
    def check_gpu(self) -> None:
        """Check GPU availability."""
        try:
            result = subprocess.run(['nvidia-smi', '--query-gpu=name,memory.total',
                                    '--format=csv,noheader'],
                                   capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print("\n  GPU Information:")
                for line in result.stdout.strip().split('\n'):
                    print(f"    {line}")
                return
        except:
            pass
        
        print("\n  ✓ GPU check: No ACCELERATION device detected (CPU only mode)")
        print("    For GPU support, install NVIDIA driver with CUDA")
    
    def launch_gui(self, debug: bool = False) -> bool:
        """Launch the photonic simulator GUI."""
        try:
            print(f"\n  • Launching GUI (debug={debug})...")
            
            # Try importing testing.py
            try:
                from testing import PhotonicSimulatorApp
                print("    ✓ testing.py imported")
            except ImportError as e:
                print(f"    ⚠ testing.py not found: {e}")
                print("    Attempting fallback GUI launch...")
                return False
            
            # Initialize app with pentagon manager
            print("    ✓ Initializing PhotonicSimulatorApp...")
            app = PhotonicSimulatorApp(pentagon_manager=self.pentagon_manager)
            
            if debug:
                print("\n  DEBUG MODE - Running in foreground\n")
            
            app.run()
            return True
        
        except Exception as e:
            print(f"\n  ✗ GUI launch failed: {e}")
            return False
    
    def run(self, args):
        """Run the application launcher."""
        parser = argparse.ArgumentParser(
            description=f"{APP_NAME} - Launcher",
            add_help=False
        )
        parser.add_argument('--help', '-h', action='store_true', help='Show help')
        parser.add_argument('--check', action='store_true', help='Check dependencies only')
        parser.add_argument('--gpu', action='store_true', help='Show GPU information')
        parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
        parser.add_argument('--debug', action='store_true', help='Debug mode')
        parser.add_argument('--version', action='store_true', help='Show version')
        parser.add_argument('--pentagon', action='store_true', help='Show pentagon structure info')
        parser.add_argument('--test-pentagon', action='store_true', help='Test pentagon structure')
        
        opts = parser.parse_args(args)
        
        # Print banner
        self.print_banner()
        
        # Handle special commands
        if opts.help:
            self.show_help()
            return 0
        
        if opts.version:
            print(f"{APP_NAME} v{APP_VERSION}")
            return 0
        
        if opts.pentagon:
            self.show_pentagon_structure_info()
            return 0
        
        if opts.test_pentagon:
            self.test_pentagon_structure()
            return 0
        
        # Check dependencies
        if not self.check_dependencies(verbose=opts.verbose or opts.check):
            print("\n✗ Cannot launch: Missing required dependencies")
            print("  Install with: pip install -r requirements.txt")
            return 1
        
        # GPU check
        if opts.gpu:
            self.check_gpu()
            return 0
        
        if opts.check:
            print("\n✓ All dependency checks complete")
            return 0
        
        # Launch application
        if opts.verbose:
            self.check_gpu()
        
        success = self.launch_gui(debug=opts.debug)
        
        return 0 if success else 1


def main():
    """Main entry point."""
    launcher = AppLauncher()
    exit_code = launcher.run(sys.argv[1:])
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
