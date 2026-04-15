"""
GPU Acceleration Module
=======================
Detects and manages GPU availability for accelerated computations.
Provides fallback to CPU if GPU unavailable.
"""

import numpy as np
import warnings

# Suppress UserWarning during import
warnings.filterwarnings('ignore')

# ============================================================================
# GPU DETECTION
# ============================================================================

def detect_gpu():
    """
    Detect GPU availability and CUDA support.
    Returns: (gpu_available, gpu_name, compute_capability)
    """
    gpu_available = False
    gpu_name = "None"
    compute_capability = (0, 0)
    
    try:
        import torch
        if torch.cuda.is_available():
            gpu_available = True
            gpu_name = torch.cuda.get_device_name(0)
            compute_capability = torch.cuda.get_device_capability(0)
            print(f"✓ CUDA available: {gpu_name}")
            return gpu_available, gpu_name, compute_capability
    except ImportError:
        pass
    
    try:
        import jax
        gpu_available = len(jax.devices('gpu')) > 0
        if gpu_available:
            gpu_name = str(jax.devices('gpu')[0])
            print(f"✓ JAX GPU available: {gpu_name}")
            return gpu_available, gpu_name, compute_capability
    except ImportError:
        pass
    
    try:
        import cupy as cp
        gpu_available = cp.cuda.is_available()
        if gpu_available:
            gpu_name = cp.cuda.Device().get_device_name().decode('utf-8')
            compute_capability = cp.cuda.Device().compute_capability
            print(f"✓ CuPy available: {gpu_name}")
            return gpu_available, gpu_name, compute_capability
    except ImportError:
        pass
    
    return gpu_available, gpu_name, compute_capability


def init_cupy():
    """Initialize CuPy if available."""
    try:
        import cupy as cp
        return cp
    except ImportError:
        print("⚠ CuPy not available - using NumPy (CPU only)")
        return None


# ============================================================================
# GPU ACCELERATION CLASS
# ============================================================================

class GPUAccelerator:
    """Manages GPU/CPU switching for array operations."""
    
    def __init__(self, use_gpu=False):
        self.use_gpu = use_gpu
        self.gpu_available, self.gpu_name, self.compute_capability = detect_gpu()
        
        # Override if GPU not available
        if not self.gpu_available:
            self.use_gpu = False
            print("⚠ GPU not available - using CPU")
        
        self.cp = None
        self.np_compute = np
        
        if self.use_gpu and self.gpu_available:
            try:
                import cupy as cp
                self.cp = cp
                self.np_compute = cp
                print(f"✓ Using GPU acceleration: {self.gpu_name}")
            except ImportError:
                print("⚠ CuPy import failed - using CPU")
                self.use_gpu = False
    
    def asarray(self, arr, dtype=None):
        """Convert array to GPU or CPU array."""
        if self.use_gpu and self.cp is not None:
            try:
                arr_gpu = self.cp.asarray(arr, dtype=dtype)
                return arr_gpu
            except Exception as e:
                print(f"GPU transfer failed: {e}, using CPU")
                return np.asarray(arr, dtype=dtype)
        return np.asarray(arr, dtype=dtype)
    
    def asnumpy(self, arr):
        """Convert GPU array back to NumPy."""
        if self.use_gpu and self.cp is not None:
            try:
                return self.cp.asnumpy(arr)
            except Exception:
                return np.asarray(arr)
        return np.asarray(arr)
    
    def fft2(self, arr):
        """2D FFT with GPU acceleration if available."""
        if self.use_gpu and self.cp is not None:
            arr_gpu = self.cp.asarray(arr)
            fft_result = self.cp.fft.fft2(arr_gpu)
            return fft_result
        else:
            return np.fft.fft2(arr)
    
    def ifft2(self, arr):
        """Inverse 2D FFT with GPU acceleration if available."""
        if self.use_gpu and self.cp is not None:
            arr_gpu = self.cp.asarray(arr)
            ifft_result = self.cp.fft.ifft2(arr_gpu)
            return ifft_result
        else:
            return np.fft.ifft2(arr)
    
    def matmul(self, a, b):
        """Matrix multiplication with GPU acceleration."""
        if self.use_gpu and self.cp is not None:
            a_gpu = self.cp.asarray(a)
            b_gpu = self.cp.asarray(b)
            result = self.cp.matmul(a_gpu, b_gpu)
            return result
        else:
            return np.matmul(a, b)
    
    def convolve(self, arr, kernel):
        """2D convolution with GPU acceleration."""
        if self.use_gpu and self.cp is not None:
            try:
                from cupyx import scipy
                arr_gpu = self.cp.asarray(arr)
                kernel_gpu = self.cp.asarray(kernel)
                result = scipy.signal.convolve2d(arr_gpu, kernel_gpu, mode='same')
                return result
            except Exception:
                import scipy.signal
                return scipy.signal.convolve2d(arr, kernel, mode='same')
        else:
            import scipy.signal
            return scipy.signal.convolve2d(arr, kernel, mode='same')
    
    def statistics(self, arr):
        """Compute statistics (mean, std, min, max) on GPU if available."""
        if self.use_gpu and self.cp is not None:
            arr_gpu = self.cp.asarray(arr)
            stats = {
                'mean': float(self.cp.mean(arr_gpu)),
                'std': float(self.cp.std(arr_gpu)),
                'min': float(self.cp.min(arr_gpu)),
                'max': float(self.cp.max(arr_gpu))
            }
            return stats
        else:
            stats = {
                'mean': float(np.mean(arr)),
                'std': float(np.std(arr)),
                'min': float(np.min(arr)),
                'max': float(np.max(arr))
            }
            return stats
    
    def get_status(self):
        """Get GPU status string."""
        if self.use_gpu and self.gpu_available:
            return f"GPU Enabled: {self.gpu_name}"
        else:
            return "CPU Only"


# ============================================================================
# MEEP GPU OPTIMIZATION
# ============================================================================

def get_meep_gpu_settings():
    """
    Get MEEP environment variables for GPU acceleration.
    Returns dict of environment variables to set.
    """
    settings = {
        'MEEP_CUDA': '1',           # Enable CUDA
        'OPENBLAS_NUM_THREADS': '1',  # Reduce CPU threads
        'OMP_NUM_THREADS': '1',
        'MKL_NUM_THREADS': '1',
    }
    return settings


def enable_meep_gpu():
    """Enable MEEP GPU acceleration via environment variables."""
    import os
    settings = get_meep_gpu_settings()
    for key, value in settings.items():
        os.environ[key] = value
    print("✓ MEEP GPU settings enabled")


# ============================================================================
# PERFORMANCE PROFILER
# ============================================================================

class PerformanceProfiler:
    """Profile GPU vs CPU performance."""
    
    def __init__(self):
        self.timings = {}
    
    def profile_operation(self, name, operation_func, use_gpu=True):
        """Compare performance of an operation on GPU vs CPU."""
        import time
        
        # CPU timing
        start_cpu = time.time()
        result_cpu = operation_func(use_gpu=False)
        time_cpu = time.time() - start_cpu
        
        # GPU timing (if available)
        time_gpu = None
        speedup = 1.0
        if use_gpu:
            try:
                start_gpu = time.time()
                result_gpu = operation_func(use_gpu=True)
                time_gpu = time.time() - start_gpu
                speedup = time_cpu / time_gpu if time_gpu > 0 else 1.0
            except Exception as e:
                print(f"GPU operation failed: {e}")
        
        self.timings[name] = {
            'cpu_ms': time_cpu * 1000,
            'gpu_ms': time_gpu * 1000 if time_gpu else None,
            'speedup': speedup
        }
        
        return self.timings[name]
    
    def print_report(self):
        """Print performance profile report."""
        print("\n" + "="*80)
        print("PERFORMANCE PROFILE REPORT")
        print("="*80)
        print(f"{'Operation':<30} | {'CPU (ms)':<12} | {'GPU (ms)':<12} | {'Speedup':<10}")
        print("-"*80)
        
        total_speedup = 0
        count = 0
        for name, times in self.timings.items():
            cpu_ms = times['cpu_ms']
            gpu_ms = times['gpu_ms'] if times['gpu_ms'] else 'N/A'
            speedup = times['speedup']
            
            print(f"{name:<30} | {cpu_ms:>10.2f} | {str(gpu_ms):>10} | {speedup:>8.2f}x")
            
            if isinstance(gpu_ms, (int, float)):
                total_speedup += speedup
                count += 1
        
        if count > 0:
            avg_speedup = total_speedup / count
            print("-"*80)
            print(f"Average Speedup: {avg_speedup:.2f}x")
        print("="*80 + "\n")
