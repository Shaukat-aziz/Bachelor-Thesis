"""
Pentagon Photonic Crystal Simulator - Application Package
CONSOLIDATED v2.1 ARCHITECTURE

Module structure after consolidation:
  app/
  ├── app.py          ← Main launcher with CLI
  ├── utilities.py    ← All utilities (materials, GPU, structures)
  └── __init__.py     ← Package exports (this file)

Consolidated from (deleted):
  × photonic_simulator.py (now in testing.py)
  × materials_manager.py (now in utilities.py)
  × lattice_structures.py (now in utilities.py)
  × progress_tracker.py (custom implementation in GUI)
  × gpu_accelerator.py (now in utilities.py)

MODULES IN UTILITIES:
  - Material management (6 predefined + XML import/export)
  - GPU acceleration (NVIDIA CUDA, Intel Iris, Arch Linux)
  - Photonic structures (substrate + air holes)
  - Helper functions

USAGE EXAMPLES:

  # Material Management
  from app.utilities import MaterialManager, MaterialLibrary
  manager = MaterialManager('app/materials')
  silicon = manager.get_material('Silicon')

  # GPU Acceleration
  from app.utilities import GPUAccelerator
  gpu = GPUAccelerator(use_gpu=True, prefer_intel=True)
  print(gpu.get_status())

  # Photonic Structure
  from app.utilities import PhotonicStructureConfig
  structure = PhotonicStructureConfig(
      substrate=MaterialLibrary.INGASP,
      air_hole_radius_nm=80.0
  )
  structure.print_config()

LAUNCHING:
  Via command line:
    python app.py              # Launch GUI
    python app.py --check      # Check dependencies
    python app.py --materials  # List materials
    python app.py --gpu        # Check GPU support

VERSION: 2.1.0 Consolidated
STATUS: Production Ready
"""

import sys
from pathlib import Path

# Add app directory to path for imports
_app_dir = Path(__file__).parent
_files_dir = _app_dir.parent

if str(_app_dir) not in sys.path:
    sys.path.insert(0, str(_app_dir))
if str(_files_dir) not in sys.path:
    sys.path.insert(0, str(_files_dir))

__version__ = "2.1.0"
__app_name__ = "Pentagon Photonic Crystal Simulator"
__architecture__ = "Consolidated (v2.1) - utilities + app"

# ============================================================================
# CORE EXPORTS FROM UTILITIES
# ============================================================================

try:
    # Material Management
    from utilities import (
        Material,
        MaterialLibrary,
        MaterialManager,
        AirHoleConfig,
        PhotonicStructureConfig,
    )
    
    # GPU Acceleration
    from utilities import (
        GPUAccelerator,
        detect_gpu,
        detect_intel_iris,
        get_arch_linux_optimizations,
    )
    
    _utilities_available = True
    _utilities_error = None
    
except ImportError as e:
    _utilities_available = False
    _utilities_error = str(e)


# ============================================================================
# OPTIONAL: PHOTONIC SIMULATOR (from testing.py)
# ============================================================================

def get_photonic_gui():
    """
    Get PentagonPhotonicsGUI class from testing.py.
    
    Returns:
        PentagonPhotonicsGUI class or None if not available
    """
    try:
        sys.path.insert(0, str(_files_dir))
        from testing import PentagonGUI
        return PentagonGUI
    except ImportError:
        return None


# ============================================================================
# SYSTEM STATUS
# ============================================================================

def get_system_status() -> dict:
    """
    Get complete system status including dependencies and GPU.
    
    Returns:
        Dictionary with status information
    """
    import platform
    
    status = {
        'app_version': __version__,
        'app_name': __app_name__,
        'architecture': __architecture__,
        'python_version': f"{platform.python_version()}",
        'platform': platform.system(),
        'utilities_available': _utilities_available,
    }
    
    if not _utilities_available:
        status['utilities_error'] = _utilities_error
    
    # Add GPU status if utilities available
    if _utilities_available:
        try:
            cuda_available, cuda_name, _ = detect_gpu()
            iris_available, iris_name = detect_intel_iris()
            
            status['gpu'] = {
                'cuda_available': cuda_available,
                'cuda_name': cuda_name,
                'iris_available': iris_available,
                'iris_name': iris_name,
            }
        except Exception as e:
            status['gpu_error'] = str(e)
    
    return status


def print_system_status():
    """Print formatted system status."""
    status = get_system_status()
    
    print("\n" + "="*70)
    print(f"Pentagon Photonic Crystal Simulator - System Status")
    print("="*70)
    print(f"App Name: {status['app_name']}")
    print(f"Version: {status['app_version']}")
    print(f"Architecture: {status['architecture']}")
    print(f"Python: {status['python_version']}")
    print(f"Platform: {status['platform']}")
    print(f"Utilities: {'✓ Available' if status['utilities_available'] else '✗ Not available'}")
    
    if 'utilities_error' in status:
        print(f"  Error: {status['utilities_error']}")
    
    if 'gpu' in status:
        print(f"CUDA GPU: {'✓ ' + status['gpu']['cuda_name'] if status['gpu']['cuda_available'] else '✗ Not available'}")
        print(f"Intel Iris: {'✓ ' + status['gpu']['iris_name'] if status['gpu']['iris_available'] else '✗ Not available'}")
    elif 'gpu_error' in status:
        print(f"GPU Status: Error - {status['gpu_error']}")
    
    print("="*70 + "\n")


# ============================================================================
# MODULE-LEVEL API
# ============================================================================

__all__ = [
    # Version info
    '__version__',
    '__app_name__',
    '__architecture__',
    
    # Material Management
    'Material',
    'MaterialLibrary',
    'MaterialManager',
    'AirHoleConfig',
    'PhotonicStructureConfig',
    
    # GPU Acceleration
    'GPUAccelerator',
    'detect_gpu',
    'detect_intel_iris',
    'get_arch_linux_optimizations',
    
    # Functions
    'get_photonic_gui',
    'get_system_status',
    'print_system_status',
]

