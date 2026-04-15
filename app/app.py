#!/usr/bin/env python3
"""]
    
Pentagon Photonic Crystal Simulator - Application Launcher
===========================================================
Main entry point for the standalone application.
Handles environment setup, dependency checking, and GUI launch.

NEW FEATURES (v2.1):
    - Cavity lattice structures with Floquet periodicity
    - Customi lattice parameters (a, d)
    - Air holes at (±d, ±d) with radius 0.2*a
    - Progress bars for "Run Sim" and "Calc Band"
    - Intel Iris GPU support (Arch Linux optimized)
    - Garuda Linux detection and optimization

ARCHITECTURE:
    FILES/
    ├── testing.py              [Original - left untouched]
    ├── app/
    │   ├── app.py              [THIS FILE - main launcher]
    │   ├── photonic_simulator.py [Core GUI + materials + lattice + progress]
    │   ├── materials_manager.py [Material definitions]
    │   ├── lattice_structures.py [Cavity + uniform lattices]
    │   ├── progress_tracker.py [Progress tracking GUI integration]
    │   ├── gpu_accelerator.py   [GPU support + Intel Iris + Arch]
    │   ├── materials/           [XML material database]
    │   │   ├── InGaAsP.xml
    │   │   ├── Silicon.xml
    │   │   └── GaAs.xml
    │   ├── requirements.txt
    │   └── setup.py
    ├── [other files...]
    └── [documentation]
"""

import sys
import os
import subprocess
import platform
import argparse
from pathlib import Path

# Version info
APP_VERSION = "2.1.0"
APP_NAME = "Pentagon Photonic Crystal Simulator"
APP_ARCHITECTURE = "Modular (v2.1) with lattices, progress, Intel Iris support"


class AppLauncher:
    """Manages application launch and environment setup."""
    
    def __init__(self):
        """Initialize launcher with proper paths."""
        self.system = platform.system()
        self.python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        
        # Get app directory (where this file is located)
        self.app_dir = Path(__file__).parent
        
        # Parent FILES directory
        self.files_dir = self.app_dir.parent
        
        # Import path setup
        sys.path.insert(0, str(self.app_dir))
        sys.path.insert(0, str(self.files_dir))
        
        self.env = os.environ.copy()
    
    def print_banner(self):
        """Print application banner."""
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
        """Check GPU availability (NVIDIA, Intel Iris, etc.)."""
        print("GPU Detection (NVIDIA + Intel Iris)")
        print("-"*80)
        
        gpu_detected = False
        
        # Check for Intel Iris (Arch Linux specific)
        try:
            from utilities import detect_intel_iris, get_arch_linux_optimizations
            iris_available, iris_name = detect_intel_iris()
            arch_opts = get_arch_linux_optimizations()
            
            if iris_available:
                gpu_detected = True
                print(f"✓ Intel Iris GPU: {iris_name}")
                if arch_opts.get('is_arch_based'):
                    os_type = arch_opts.get('os', 'Arch')
                    print(f"  OS: {os_type.upper()} Linux (optimized)")
        except (ImportError, Exception):
            pass
        
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
            print("  - Intel Iris: Already supported on Arch Linux")
            print("  - NVIDIA CUDA: Install CUDA toolkit + cupy")
            print("  - oneAPI (Intel compute): Install Intel compute runtime")
        
        print()
        return gpu_detected
    
    def check_materials(self):
        """Check materials configuration."""
        print("Materials Configuration")
        print("-"*80)
        
        try:
            from utilities import MaterialManager
            materials_dir = self.app_dir / "materials"
            manager = MaterialManager(str(materials_dir))
            
            mats = manager.list_materials()
            print(f"✓ Material Manager initialized")
            print(f"  Available materials: {len(mats)}")
            print(f"  Materials directory: {materials_dir}")
            
            for mat in mats:
                print(f"    - {mat}")
            
        except Exception as e:
            print(f"✗ Material Manager error: {e}")
        
        print()
    
    def launch_gui(self, debug=False):
        """Launch the photonic simulator GUI."""
        print("Launching Photonic Crystal Simulator v2.1...")
        print("-"*80)
        
        gui_launcher_file = self.app_dir / "gui_launcher.py"
        
        if not gui_launcher_file.exists():
            print(f"❌ ERROR: GUI launcher not found: {gui_launcher_file}")
            return False
        
        try:
            # Set environment variables for GPU if available
            os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # Suppress TensorFlow warnings
            os.environ['CUDA_LAUNCH_BLOCKING'] = '0'   # Async GPU operations

            # Configure Qt plugin discovery for reliable GUI startup
            try:
                from PyQt6.QtCore import QLibraryInfo
                plugins_path = QLibraryInfo.path(QLibraryInfo.LibraryPath.PluginsPath)
                if plugins_path:
                    os.environ.setdefault('QT_QPA_PLATFORM_PLUGIN_PATH', plugins_path)
            except Exception:
                pass

            # Choose a safe Qt platform to prevent hard startup aborts on Linux
            if self.system == 'Linux' and 'QT_QPA_PLATFORM' not in os.environ:
                has_display = bool(os.environ.get('DISPLAY') or os.environ.get('WAYLAND_DISPLAY'))
                selected_platform = 'offscreen'

                if has_display:
                    plugin_path = os.environ.get('QT_QPA_PLATFORM_PLUGIN_PATH', '')
                    xcb_plugin = Path(plugin_path) / 'platforms' / 'libqxcb.so' if plugin_path else None

                    if xcb_plugin and xcb_plugin.exists():
                        try:
                            ldd_result = subprocess.run(
                                ['ldd', str(xcb_plugin)],
                                capture_output=True,
                                text=True,
                                timeout=5
                            )
                            if 'not found' not in (ldd_result.stdout + ldd_result.stderr).lower():
                                selected_platform = 'xcb'
                        except Exception:
                            selected_platform = 'offscreen'

                os.environ['QT_QPA_PLATFORM'] = selected_platform

            # Propagate any runtime environment updates to subprocess launches
            self.env.update(os.environ)

            # Run the Qt GUI launcher in a subprocess to avoid hard process aborts
            cmd = [sys.executable, str(gui_launcher_file)]
            if debug:
                print("Running GUI launcher as subprocess (debug mode)")
            print(f"Running: {' '.join(cmd)}")
            print("-"*80)

            qt_result = subprocess.run(cmd, env=self.env, cwd=str(self.app_dir))
            if qt_result.returncode == 0:
                return True

            print("⚠ Qt GUI launcher exited with error. Trying fallback GUI (testing.py)...")
            fallback_gui = self.files_dir / "testing.py"
            if not fallback_gui.exists():
                print(f"❌ Fallback GUI not found: {fallback_gui}")
                return False

            fallback_cmd = [sys.executable, str(fallback_gui)]
            fallback_env = self.env.copy()
            fallback_env['MPLBACKEND'] = 'TkAgg'
            fallback_env.pop('QT_QPA_PLATFORM', None)
            print(f"Running fallback: {' '.join(fallback_cmd)}")
            print("-"*80)
            fallback_result = subprocess.run(fallback_cmd, env=fallback_env, cwd=str(self.files_dir))
            return fallback_result.returncode == 0
        except Exception as e:
            print(f"❌ ERROR launching application: {e}")
            return False
    
    def show_help(self):
        """Show help information."""
        print(f"\n{APP_NAME} v{APP_VERSION}")
        print("\nUsage: python app.py [OPTIONS]")
        print("\nOptions:")
        print("  --help, -h          Show this help message")
        print("  --check              Check dependencies only, don't launch")
        print("  --gpu               Show GPU information")
        print("  --materials         Show available materials")
        print("  --verbose, -v        Verbose output")
        print("  --debug              Run in debug mode (foreground)")
        print("  --version            Show version information")
        print("\nExamples:")
        print("  python app.py              # Launch application")
        print("  python app.py --check      # Check dependencies")
        print("  python app.py --gpu        # Check GPU availability")
        print("  python app.py --materials  # List available materials")
        print("  python app.py --debug      # Launch in debug mode")
        print()
    
    def show_version(self):
        """Show version and architecture information."""
        print(f"\n{APP_NAME}")
        print(f"Version: {APP_VERSION}")
        print(f"Architecture: {APP_ARCHITECTURE}")
        print(f"\nModules:")
        print(f"  - photonic_simulator.py .... GUI & simulation logic")
        print(f"  - materials_manager.py .... Material definitions")
        print(f"  - gpu_accelerator.py ...... GPU acceleration")
        print(f"  - materials/ .............. XML material database")
        print()
    
    def run(self, args):
        """Run the application launcher."""
        parser = argparse.ArgumentParser(
            description=f"{APP_NAME} v{APP_VERSION}",
            add_help=False
        )
        parser.add_argument('--help', '-h', action='store_true', help='Show help')
        parser.add_argument('--check', action='store_true', help='Check dependencies only')
        parser.add_argument('--gpu', action='store_true', help='Show GPU information')
        parser.add_argument('--materials', action='store_true', help='List materials')
        parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
        parser.add_argument('--debug', action='store_true', help='Debug mode')
        parser.add_argument('--version', action='store_true', help='Show version')
        
        opts = parser.parse_args(args)
        
        # Print banner
        self.print_banner()
        
        # Handle special commands
        if opts.help:
            self.show_help()
            return 0
        
        if opts.version:
            self.show_version()
            return 0
        
        # Check dependencies
        if not self.check_dependencies(verbose=opts.verbose):
            print("\n❌ Cannot launch: Missing required dependencies")
            print("Install with: pip install numpy matplotlib scipy")
            return 1
        
        # GPU check
        if opts.gpu:
            self.check_gpu()
            return 0
        
        # Materials check
        if opts.materials:
            self.check_materials()
            return 0
        
        if opts.check:
            self.check_materials()
            self.check_gpu()
            print("✓ All checks complete")
            return 0
        
        # Launch application
        if opts.gpu or opts.verbose:
            self.check_gpu()
        
        if opts.verbose:
            self.check_materials()
        
        success = self.launch_gui(debug=opts.debug)
        
        return 0 if success else 1


def main():
    """Main entry point."""
    launcher = AppLauncher()
    exit_code = launcher.run(sys.argv[1:])
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
