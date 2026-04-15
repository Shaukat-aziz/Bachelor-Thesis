#!~/miniconda/envs/meep_env/bin/python
"""
Interactive GUI for Pentagon Structure Manipulation
====================================================
Manual adjustment of 5-petal 3×3 lattice structure with decay profiles.
Allows stretching/contracting edges and corners in real-time.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from matplotlib.widgets import Slider, Button, RadioButtons, TextBox, CheckButtons
import os
import sys

# GPU acceleration support
try:
    from gpu_accelerator import GPUAccelerator, enable_meep_gpu, detect_gpu
    GPU_MODULE_AVAILABLE = True
except ImportError:
    GPU_MODULE_AVAILABLE = False
    print("⚠ GPU acceleration module not available - CPU only mode")

# PyMeep for electromagnetic simulations
try:
    import meep as mp  # type: ignore
    # Verify this is the official PyMeep (has mp.Medium attribute)
    if hasattr(mp, 'Medium') and hasattr(mp, 'Cylinder'):
        MEEP_AVAILABLE = True
        print("✓ Official PyMeep detected and ready")
    else:
        MEEP_AVAILABLE = False
        print("="*80)
        print("WARNING: Incompatible 'meep' package detected!")
        print("="*80)
        print("The installed 'meep' package is NOT the official PyMeep.")
        print("EM simulation features are DISABLED.")
        print("\nTo enable MEEP electromagnetic simulations:")
        print("  1. Uninstall incorrect package:")
        print("     pip uninstall meep")
        print("  2. Install official PyMeep via conda:")
        print("     conda install -c conda-forge pymeep")
        print("  3. Or follow: https://meep.readthedocs.io/en/latest/Installation/")
        print("="*80)
except ImportError:
    MEEP_AVAILABLE = False
    print("="*80)
    print("INFO: PyMeep not installed - EM simulation features disabled")
    print("="*80)
    print("To enable electromagnetic simulations, install PyMeep:")
    print("  conda install -c conda-forge pymeep")
    print("  Or visit: https://meep.readthedocs.io/en/latest/Installation/")
    print("="*80)


# ============================================================================
# LATTICE PARAMETERS
# ============================================================================
bise_nm = 469.0 
a_nm = 469.0  # lattice constant magnitude in nanometers
basis_offset = 0.54 * a_nm / np.sqrt(2)

# Square lattice vectors (reference)
sq_a1 = np.array([a_nm, 0.0])
sq_a2 = np.array([0.0, a_nm])

# Grid size
n_cells_x = 3
n_cells_y = 3

# Four sites per unit cell (square basis), centered at (0,0)
basis_sites_square = np.array([
    [ basis_offset,  basis_offset],
    [-basis_offset,  basis_offset],
    [ basis_offset, -basis_offset],
    [-basis_offset, -basis_offset],
])


# ============================================================================
# TRANSFORMATION FUNCTIONS
# ============================================================================

def decay_function(distance, max_distance, profile='exponential', custom_equation=None):
    """Calculate decay factor based on distance from the stretching corner."""
    normalized_dist = np.clip(distance / max_distance, 0, 1)
    
    if profile == 'exponential':
        decay_rate = 3.0
        factor = np.exp(-decay_rate * normalized_dist)
    elif profile == 'gaussian':
        sigma = 0.35
        factor = np.exp(-(normalized_dist / sigma)**2)
    elif profile == 'polynomial':
        power = 3
        factor = (1 - normalized_dist)**power
    elif profile == 'custom' and custom_equation:
        try:
            # Safe evaluation of custom equation
            # x is the normalized distance [0, 1]
            x = normalized_dist
            # Allow common math functions
            safe_dict = {
                'exp': np.exp,
                'sin': np.sin,
                'cos': np.cos,
                'tan': np.tan,
                'sqrt': np.sqrt,
                'log': np.log,
                'log10': np.log10,
                'abs': np.abs,
                'x': x,
                'np': np,
                'pi': np.pi,
                'e': np.e
            }
            factor = eval(custom_equation, {"__builtins__": {}}, safe_dict)
            # Ensure result is valid
            if not np.isfinite(factor):
                factor = 0.0
            factor = np.clip(factor, 0, 1)  # Clamp to [0, 1]
        except:
            # Fallback to linear if equation fails
            factor = 1 - normalized_dist
    else:
        factor = 1 - normalized_dist
    
    return factor


def create_lattice_with_correct_atom_positions(n_cells_x, n_cells_y, sq_a1, sq_a2, 
                                               basis_square, target_angle_deg=72.0,
                                               stretch_corner='bottom_left', 
                                               decay_profile='exponential',
                                               custom_equation=None,
                                               custom_basis=None):
    """
    Create lattice where atoms are correctly positioned at unit cell corners.
    The basis_square defines the relative positions within a unit cell.
    
    Parameters
    ----------
    n_cells_x, n_cells_y : int
        Number of cells in x and y directions
    sq_a1, sq_a2 : ndarray
        Square lattice basis vectors
    basis_square : ndarray
        Basis atom positions in square lattice
    target_angle_deg : float
        Target angle for stretched corner (default: 72°)
    stretch_corner : str
        Which corner to stretch ('bottom_left', 'bottom_right', 'top_left', 'top_right')
    decay_profile : str
        Decay function type ('exponential', 'gaussian', 'polynomial')
        
    Returns
    -------
    all_atoms : ndarray
        Positions of all atoms
    cell_corners_list : list
        List of cell corner coordinates
    transformation_factors : ndarray
        Transformation factor for each cell
    stretch_point : ndarray
        Position of stretch point (origin)
    """
    # Create vertex grid and deform
    n_verts_x = n_cells_x + 1
    n_verts_y = n_cells_y + 1
    
    vix = np.arange(n_verts_x) - n_cells_x // 2
    viy = np.arange(n_verts_y) - n_cells_y // 2
    
    if stretch_corner == 'bottom_left':
        i_stretch, j_stretch = 0, 0
    elif stretch_corner == 'bottom_right':
        i_stretch, j_stretch = n_verts_x - 1, 0
    elif stretch_corner == 'top_left':
        i_stretch, j_stretch = 0, n_verts_y - 1
    else:
        i_stretch, j_stretch = n_verts_x - 1, n_verts_y - 1
    
    # Original square vertex positions
    vertices_square = {}
    stretch_vertex_sq = None
    for i, vi in enumerate(vix):
        for j, vj in enumerate(viy):
            pos = np.array([vi * sq_a1[0], vj * sq_a2[1]])
            vertices_square[(i, j)] = pos
            if i == i_stretch and j == j_stretch:
                stretch_vertex_sq = pos.copy()
    
    far_i = n_verts_x - 1 if i_stretch == 0 else 0
    far_j = n_verts_y - 1 if j_stretch == 0 else 0
    far_vertex_sq = vertices_square[(far_i, far_j)]
    max_distance = np.linalg.norm(far_vertex_sq - stretch_vertex_sq)
    
    # Target parallelogram basis
    a_mag = np.linalg.norm(sq_a1)
    target_angle_rad = np.deg2rad(target_angle_deg)
    para_a1 = np.array([a_mag, 0.0])
    para_a2 = a_mag * np.array([np.cos(target_angle_rad), np.sin(target_angle_rad)])
    
    # Deform vertices
    vertices_deformed = {}
    for i, vi in enumerate(vix):
        for j, vj in enumerate(viy):
            v_sq = vertices_square[(i, j)]
            dist = np.linalg.norm(v_sq - stretch_vertex_sq)
            alpha = decay_function(dist, max_distance, decay_profile, custom_equation)
            
            v_para = vi * para_a1 + vj * para_a2
            v_deformed = (1 - alpha) * v_sq + alpha * v_para
            vertices_deformed[(i, j)] = v_deformed
            
            if i == i_stretch and j == j_stretch:
                stretch_vertex_def = v_deformed.copy()
    
    # Create cells and place atoms at corners
    all_atoms = []
    cell_corners_list = []
    transformation_factors = []
    
    # Normalize basis positions to [0,1] range for proper corner placement
    basis_to_use = custom_basis if custom_basis is not None else basis_square
    basis_frac = basis_to_use / a_mag
    
    for i in range(n_cells_x):
        for j in range(n_cells_y):
            # Cell vertices
            v00 = vertices_deformed[(i, j)]      # bottom-left
            v10 = vertices_deformed[(i+1, j)]    # bottom-right
            v11 = vertices_deformed[(i+1, j+1)]  # top-right
            v01 = vertices_deformed[(i, j+1)]    # top-left
            
            corners = np.array([v00, v10, v11, v01])
            cell_corners_list.append(corners)
            
            # Cell's lattice vectors (edges)
            a1_cell = v10 - v00  # bottom edge
            a2_cell = v01 - v00  # left edge
            
            # Place atoms at fractional positions within the deformed cell
            cell_atoms = []
            for atom_frac in basis_frac:
                fx = atom_frac[0] + 0.5  # shift to [0,1] range
                fy = atom_frac[1] + 0.5
                atom_pos = v00 + fx * a1_cell + fy * a2_cell
                cell_atoms.append(atom_pos)
            
            all_atoms.extend(cell_atoms)
            
            # Calculate transformation factor
            center_sq = vertices_square[(i, j)] + 0.5 * (sq_a1 + sq_a2)
            dist = np.linalg.norm(center_sq - stretch_vertex_sq)
            alpha = decay_function(dist, max_distance, decay_profile, custom_equation)
            transformation_factors.append(alpha)
    
    all_atoms = np.array(all_atoms)
    transformation_factors = np.array(transformation_factors)
    
    # Center at acute corner
    acute_corner_position = stretch_vertex_def
    all_atoms = all_atoms - acute_corner_position
    cell_corners_list = [corners - acute_corner_position for corners in cell_corners_list]
    
    return all_atoms, cell_corners_list, transformation_factors, np.zeros(2)


# ============================================================================
# INTERACTIVE GUI CLASS
# ============================================================================

class PentagonGUI:
    """
    Interactive GUI for adjusting 5-petal 3×3 lattice structure.
    Allows manual stretching/contracting edges and corners with 3 decay profiles.
    Supports interactive selection and manipulation of corners/edges.
    """
    
    def __init__(self, n_cells=3, sq_a1=None, sq_a2=None, basis=None):
        """
        Initialize the GUI.
        
        Parameters
        ----------
        n_cells : int
            Number of cells per petal (default: 3)
        sq_a1, sq_a2 : ndarray, optional
            Square lattice basis vectors
        basis : ndarray, optional
            Basis atom positions
        """
        self.n_cells = n_cells
        self.sq_a1 = sq_a1 if sq_a1 is not None else np.array([a_nm, 0])
        self.sq_a2 = sq_a2 if sq_a2 is not None else np.array([0, a_nm])
        self.basis = basis if basis is not None else basis_sites_square
        
        # Initial parameters
        self.current_profile = 'exponential'
        self.target_angle = 72.0
        self.decay_rate = 1.0  # Multiplier for decay strength
        self.petal_scales = [1.0, 1.0, 1.0, 1.0, 1.0]  # Individual petal scaling
        self.global_scale = 1.0
        self.custom_decay_equation = 'exp(-3*x)'  # Default custom equation
        self.atom_size = 50  # Marker size for atoms
        self.custom_basis_positions = None  # Custom atom positions: None = use default
        self.loaded_atoms = None  # Loaded atom positions (from .npy)
        self.plot_data_file = None  # Path to saved plot data file
        self.show_matrix_in_gui = False  # Toggle to show transformation matrix in GUI
        
        # GPU acceleration settings
        self.gpu_available = False
        self.gpu_name = "None"
        self.gpu_enabled = False
        self.gpu_accelerator = None
        
        if GPU_MODULE_AVAILABLE:
            self.gpu_available, self.gpu_name, _ = detect_gpu()
            if self.gpu_available:
                self.gpu_accelerator = GPUAccelerator(use_gpu=False)  # Start disabled
        
        # MEEP electromagnetic simulation parameters
        self.meep_enabled = MEEP_AVAILABLE
        self.meep_resolution = 20  # pixels per unit length
        self.meep_frequency = 0.15  # frequency (1/wavelength)
        self.meep_wavelength = 1.0 / 0.15 if self.meep_enabled else 6.67
        self.meep_sim = None  # MEEP simulation object
        self.meep_field_data = None  # Stored field data
        self.meep_cell_size = None  # MEEP cell size (Vector3)
        self.meep_show_hz = True  # Show Hz field
        self.meep_show_ex = False  # Show Ex field
        self.meep_show_ey = False  # Show Ey field
        self.meep_cylinder_radius = 50.0  # Air hole radius (nm)
        self.meep_epsilon = 12.0  # Substrate dielectric constant
        self.meep_air_epsilon = 1.0  # Air hole dielectric constant
        self.meep_runtime = 200  # Simulation time steps
        self.meep_use_gpu = False  # Use GPU for MEEP (if available)
        
        # Band structure parameters
        self.meep_num_bands = 8  # Number of bands to calculate
        self.meep_k_points = 20  # Number of k-points along path
        self.meep_band_data = None  # Stored band structure data
        self.meep_k_path = None  # K-point path for band structure
        self.meep_freq_min = 0.0  # Minimum frequency for band diagram
        self.meep_freq_max = 0.5  # Maximum frequency for band diagram
        
        # Interactive selection state (always active)
        self.show_selection = True  # Toggle for showing selection markers
        self.selected_petal = None  # 0-4
        self.selected_type = None   # 'corner' or 'edge'
        self.selected_index = None  # which corner (0-3) or edge (0-3)
        self.corner_offsets = {}    # {corner_idx: [dx, dy]} - applies to all petals
        self.edge_scales = {}       # {edge_idx: scale_factor} - applies to all petals
        
        # Cache for interactive manipulation
        self.petal_corners_cache = {}  # Store corner positions for each petal
        self.dragging = False
        self.drag_start = None
        self.arrow_step = 5.0  # Step size for arrow key adjustments (nm)
        
        # Setup figure with control panel
        self.fig = plt.figure(figsize=(18, 11))
        
        # Main plot area
        self.ax_main = self.fig.add_axes((0.05, 0.30, 0.9, 0.65))
        
        # Control panel area (bottom)
        self.setup_controls()
        
        # Connect mouse events
        self.fig.canvas.mpl_connect('button_press_event', self.on_click)
        self.fig.canvas.mpl_connect('motion_notify_event', self.on_motion)
        self.fig.canvas.mpl_connect('button_release_event', self.on_release)
        self.fig.canvas.mpl_connect('key_press_event', self.on_key_press)
        
        # Initial plot
        self.update_plot()
    
    def setup_controls(self):
        """Create control panels: LEFT (decay, angle, scale, matrix) and RIGHT (atoms)"""
        
        # ============ LEFT PANEL ============
        # Radio buttons for decay profile (TOP LEFT)
        ax_radio = self.fig.add_axes((0.1, 0.25, 0.12, 0.15))
        self.radio = RadioButtons(ax_radio, ('Exponential', 'Gaussian', 'Polynomial', 'Custom'),
                                   active=0)
        self.radio.on_clicked(self.update_profile)
        
        # Custom decay equation input (below radio buttons)
        ax_custom_eq = self.fig.add_axes((0.1, 0.19, 0.15, 0.04))
        self.textbox_custom_eq = TextBox(ax_custom_eq, 'Custom Eq:', initial=self.custom_decay_equation,
                                         label_pad=0.01)
        self.textbox_custom_eq.on_submit(self.update_custom_equation)
        
        # Row 1: Angle & Decay textboxes
        ax_angle = self.fig.add_axes((0.1, 0.14, 0.15, 0.04))
        self.textbox_angle = TextBox(ax_angle, 'Angle°:', initial=str(self.target_angle),
                                     label_pad=0.01)
        self.textbox_angle.on_submit(self.update_angle_text)
        
        # Decay rate text input
        ax_decay = self.fig.add_axes((0.1, 0.09, 0.15, 0.04))
        self.textbox_decay = TextBox(ax_decay, 'Decay:', initial=str(self.decay_rate),
                                     label_pad=0.01)
        self.textbox_decay.on_submit(self.update_decay_text)
        
        # Global scale text input
        ax_gscale = self.fig.add_axes((0.1, 0.04, 0.08, 0.04))
        self.textbox_gscale = TextBox(ax_gscale, 'Scale:', initial=str(self.global_scale),
                                      label_pad=0.01)
        self.textbox_gscale.on_submit(self.update_scale_text)
        

        # Removed petal sliders P0-P4 for clean layout
        
        # ========== CONTROL BUTTONS LAYOUT (1/3 to 2/3 horizontal) ==========
        # ROW 1 (TOP): Export & Action Buttons
        # Export Matrices button
        ax_export_matrices = self.fig.add_axes((0.332, 0.08, 0.07, 0.04))
        self.btn_export_matrices = Button(ax_export_matrices, 'Export')
        self.btn_export_matrices.on_clicked(self.export_matrices)
        self.btn_export_matrices.color = '#FFE5B4'
        
        # Get 36×36 Matrix button
        ax_get_matrix = self.fig.add_axes((0.412, 0.08, 0.07, 0.04))
        self.btn_get_matrix = Button(ax_get_matrix, 'Get Matrix')
        self.btn_get_matrix.on_clicked(self.get_transformation_matrix)
        self.btn_get_matrix.color = '#ADD8E6'
        
        # Selection visibility toggle
        ax_select_toggle = self.fig.add_axes((0.492, 0.08, 0.07, 0.04))
        self.btn_select_toggle = Button(ax_select_toggle, 'Select: ON')
        self.btn_select_toggle.on_clicked(self.toggle_selection_visibility)
        self.btn_select_toggle.color = 'lightgreen'
        
        # Reset button
        ax_reset = self.fig.add_axes((0.574, 0.08, 0.07, 0.04))
        self.btn_reset = Button(ax_reset, 'Reset')
        self.btn_reset.on_clicked(self.reset)
        self.btn_reset.color = '#FFB6C6'
        
        # ROW 2 (BOTTOM): Load Matrix Buttons
        # Load Initial Matrix button
        ax_load_initial = self.fig.add_axes((0.33, 0.03, 0.10, 0.04))
        self.btn_load_initial = Button(ax_load_initial, 'Load Initial')
        self.btn_load_initial.on_clicked(self.load_initial_matrix)
        self.btn_load_initial.color = '#E0FFE0'
        
        # Load Transformation Matrix button
        ax_load_transform = self.fig.add_axes((0.44, 0.03, 0.10, 0.04))
        self.btn_load_transform = Button(ax_load_transform, 'Load Transform')
        self.btn_load_transform.on_clicked(self.load_transformation_matrix)
        self.btn_load_transform.color = '#E0FFE0'
        
        # Load Final Matrix button
        ax_load_final = self.fig.add_axes((0.549, 0.03, 0.10, 0.04))
        self.btn_load_final = Button(ax_load_final, 'Load Final')
        self.btn_load_final.on_clicked(self.load_final_matrix)
        self.btn_load_final.color = '#E0FFE0'
        
        # Save Plot Data button
        ax_save_plot = self.fig.add_axes((0.349, 0.13, 0.07, 0.04))
        self.btn_save_plot = Button(ax_save_plot, 'Save Plot')
        self.btn_save_plot.on_clicked(self.save_plot_data)
        self.btn_save_plot.color = '#FFFACD'
        
        # Load Plot Data button
        ax_load_plot = self.fig.add_axes((0.455, 0.13, 0.07, 0.04))
        self.btn_load_plot = Button(ax_load_plot, 'Load Plot')
        self.btn_load_plot.on_clicked(self.load_plot_data)
        self.btn_load_plot.color = '#F0E68C'
        
        # Show/Hide Matrix Display button
        ax_show_matrix = self.fig.add_axes((0.566, 0.13, 0.07, 0.04))
        self.btn_show_matrix = Button(ax_show_matrix, 'Matrix: OFF')
        self.btn_show_matrix.on_clicked(self.toggle_matrix_display)
        self.btn_show_matrix.color = '#E6E6FA'
        

        # ============ RIGHT PANEL ============
        # Atom size slider
        ax_atom_size = self.fig.add_axes((0.70, 0.20, 0.25, 0.025))
        self.slider_atom_size = Slider(ax_atom_size, 'Atom Size', 10, 200, 
                                       valinit=50, valstep=5)
        self.slider_atom_size.on_changed(self.update_atom_size)
        
        # Custom basis position editor
        self.basis_textboxes = []
        basis_labels = ['Atom 1 X:', 'Atom 1 Y:', 'Atom 2 X:', 'Atom 2 Y:', 
                       'Atom 3 X:', 'Atom 3 Y:', 'Atom 4 X:', 'Atom 4 Y:']
        y_start = 0.18
        for idx, (label, basis_site) in enumerate(zip(basis_labels, 
                                                       [item for atom in self.basis for item in atom])):
            row = idx // 2
            col = idx % 2
            y_pos = y_start - row * 0.03
            x_pos = 0.70 + col * 0.14
            
            # Label
            self.fig.text(x_pos - 0.01, y_pos, label, fontsize=8, va='center')
            
            # Textbox
            ax_tb = self.fig.add_axes((x_pos + 0.03, y_pos - 0.007, 0.08, 0.02))
            tb = TextBox(ax_tb, '', initial=f"{basis_site:.2f}")
            atom_idx = idx // 2
            coord = 'x' if idx % 2 == 0 else 'y'
            tb.on_submit(lambda text, ai=atom_idx, c=coord: self.update_atom_position(ai, c, text))
            self.basis_textboxes.append((coord, atom_idx, tb))
        
        # Reset basis button
        ax_reset_basis = self.fig.add_axes((0.70, 0.01, 0.12, 0.03))
        self.btn_reset_basis = Button(ax_reset_basis, 'Reset Basis')
        self.btn_reset_basis.on_clicked(self.reset_basis_positions)
        
        # Update atoms button
        ax_update_atoms = self.fig.add_axes((0.83, 0.01, 0.12, 0.03))
        self.btn_update_atoms = Button(ax_update_atoms, 'Update Atoms')
        self.btn_update_atoms.on_clicked(self.apply_atom_position_updates)
        self.btn_update_atoms.color = '#FFE0B4'
        
        # ============ MEEP SIMULATION CONTROLS (Far Right Panel) ============
        if self.meep_enabled:
            # Title
            self.fig.text(0.71, 0.66, 'ELECTROMAGNETIC SIMULATION (MEEP)', 
                         fontsize=9, fontweight='bold', color='darkblue')
            
            # GPU Toggle Button (Top right)
            if self.gpu_available:
                ax_gpu_toggle = self.fig.add_axes((0.93, 0.655, 0.06, 0.02))
                self.btn_gpu_toggle = Button(ax_gpu_toggle, 'GPU: OFF')
                self.btn_gpu_toggle.on_clicked(self.toggle_gpu_acceleration)
                self.btn_gpu_toggle.color = '#FFB0B0'  # Light red initially
                
                # GPU status text
                self.fig.text(0.71, 0.645, f'GPU: {self.gpu_name}', 
                             fontsize=7, color='gray', style='italic')
            
            # Frequency/Wavelength input
            ax_freq = self.fig.add_axes((0.71, 0.625, 0.10, 0.02))
            self.textbox_freq = TextBox(ax_freq, 'Freq:', initial=f"{self.meep_frequency:.3f}",
                                       label_pad=0.01)
            self.textbox_freq.on_submit(self.update_meep_frequency)
            
            ax_wl = self.fig.add_axes((0.85, 0.625, 0.10, 0.02))
            self.textbox_wavelength = TextBox(ax_wl, 'λ:', initial=f"{self.meep_wavelength:.2f}",
                                             label_pad=0.01)
            self.textbox_wavelength.on_submit(self.update_meep_wavelength)
            
            # Resolution and cylinder radius
            ax_res = self.fig.add_axes((0.71, 0.6, 0.10, 0.02))
            self.textbox_resolution = TextBox(ax_res, 'Res:', initial=str(self.meep_resolution),
                                             label_pad=0.01)
            self.textbox_resolution.on_submit(self.update_meep_resolution)
            
            ax_cyl = self.fig.add_axes((0.85, 0.6, 0.10, 0.02))
            self.textbox_cylinder = TextBox(ax_cyl, 'R(nm):', initial=f"{self.meep_cylinder_radius:.1f}",
                                           label_pad=0.01)
            self.textbox_cylinder.on_submit(self.update_meep_cylinder_radius)
            
            # Epsilon and runtime
            ax_eps = self.fig.add_axes((0.71, 0.575, 0.10, 0.02))
            self.textbox_epsilon = TextBox(ax_eps, 'ε:', initial=f"{self.meep_epsilon:.1f}",
                                          label_pad=0.01)
            self.textbox_epsilon.on_submit(self.update_meep_epsilon)
            
            ax_runtime = self.fig.add_axes((0.85, 0.575, 0.10, 0.02))
            self.textbox_runtime = TextBox(ax_runtime, 'Time:', initial=str(self.meep_runtime),
                                          label_pad=0.01)
            self.textbox_runtime.on_submit(self.update_meep_runtime)
            
            # Field selection checkboxes
            ax_fields = self.fig.add_axes((0.70, 0.515, 0.08, 0.05))
            self.check_fields = CheckButtons(ax_fields, ['Hz', 'Ex', 'Ey'],
                                            [self.meep_show_hz, self.meep_show_ex, self.meep_show_ey])
            self.check_fields.on_clicked(self.update_meep_field_selection)
            
            # Simulation control buttons (Row 1)
            ax_meep_setup = self.fig.add_axes((0.70, 0.475, 0.08, 0.03))
            self.btn_meep_setup = Button(ax_meep_setup, 'Setup Sim')
            self.btn_meep_setup.on_clicked(self.setup_meep_simulation)
            self.btn_meep_setup.color = '#B0E0FF'
            
            ax_meep_run = self.fig.add_axes((0.79, 0.475, 0.08, 0.03))
            self.btn_meep_run = Button(ax_meep_run, 'Run Sim')
            self.btn_meep_run.on_clicked(self.run_meep_simulation)
            self.btn_meep_run.color = '#90EE90'
            
            ax_meep_show = self.fig.add_axes((0.88, 0.475, 0.07, 0.03))
            self.btn_meep_show = Button(ax_meep_show, 'Show Hz')
            self.btn_meep_show.on_clicked(self.show_meep_fields)
            self.btn_meep_show.color = '#FFD700'
            
            # Additional controls (Row 2)
            ax_meep_clear = self.fig.add_axes((0.70, 0.445, 0.08, 0.03))
            self.btn_meep_clear = Button(ax_meep_clear, 'Clear Sim')
            self.btn_meep_clear.on_clicked(self.clear_meep_simulation)
            self.btn_meep_clear.color = '#FFB6C6'
            
            ax_meep_export = self.fig.add_axes((0.79, 0.445, 0.16, 0.03))
            self.btn_meep_export = Button(ax_meep_export, 'Export Fields')
            self.btn_meep_export.on_clicked(self.export_meep_fields)
            self.btn_meep_export.color = '#FFE5B4'
            
            # Band structure controls (NEW SECTION)
            self.fig.text(0.71, 0.41, 'BAND STRUCTURE ANALYSIS', 
                         fontsize=9, fontweight='bold', color='darkgreen')
            
            # Number of bands and k-points
            ax_num_bands = self.fig.add_axes((0.71, 0.375, 0.10, 0.02))
            self.textbox_num_bands = TextBox(ax_num_bands, 'Bands:', initial=str(self.meep_num_bands),
                                            label_pad=0.01)
            self.textbox_num_bands.on_submit(self.update_num_bands)
            
            ax_k_points = self.fig.add_axes((0.85, 0.375, 0.10, 0.02))
            self.textbox_k_points = TextBox(ax_k_points, 'K-pts:', initial=str(self.meep_k_points),
                                           label_pad=0.01)
            self.textbox_k_points.on_submit(self.update_k_points)
            
            # Frequency range for band diagram
            ax_freq_min = self.fig.add_axes((0.71, 0.350, 0.10, 0.02))
            self.textbox_freq_min = TextBox(ax_freq_min, 'f_min:', initial=f"{self.meep_freq_min:.2f}",
                                           label_pad=0.01)
            self.textbox_freq_min.on_submit(self.update_freq_min)
            
            ax_freq_max = self.fig.add_axes((0.85, 0.350, 0.10, 0.02))
            self.textbox_freq_max = TextBox(ax_freq_max, 'f_max:', initial=f"{self.meep_freq_max:.2f}",
                                           label_pad=0.01)
            self.textbox_freq_max.on_submit(self.update_freq_max)
            
            # Band structure calculation buttons
            ax_calc_bands = self.fig.add_axes((0.748, 0.315, 0.08, 0.03))
            self.btn_calc_bands = Button(ax_calc_bands, 'Calc Bands')
            self.btn_calc_bands.on_clicked(self.calculate_band_structure)
            self.btn_calc_bands.color = '#98FB98'
            
            ax_show_bands = self.fig.add_axes((0.838, 0.315, 0.08, 0.03))
            self.btn_show_bands = Button(ax_show_bands, 'Show Bands')
            self.btn_show_bands.on_clicked(self.show_band_structure)
            self.btn_show_bands.color = '#87CEEB'
            
            # Hz field mode analysis button
            ax_hz_modes = self.fig.add_axes((0.748, 0.280, 0.08, 0.03))
            self.btn_hz_modes = Button(ax_hz_modes, 'Hz Modes')
            self.btn_hz_modes.on_clicked(self.analyze_hz_modes)
            self.btn_hz_modes.color = '#DDA0DD'
            
            # Export band structure
            ax_export_bands = self.fig.add_axes((0.838, 0.280, 0.08, 0.03))
            self.btn_export_bands = Button(ax_export_bands, 'Export Bands')
            self.btn_export_bands.on_clicked(self.export_band_structure)
            self.btn_export_bands.color = '#F0E68C'
        else:
            # Show disabled message if MEEP not available
            self.fig.text(0.70, 0.595, 'MEEP NOT AVAILABLE', 
                         fontsize=9, fontweight='bold', color='red')
            self.fig.text(0.70, 0.575, 'Install: pip install meep', 
                         fontsize=8, color='gray')
    
    def clear_selection(self):
        """Clear current selection"""
        self.selected_petal = None
        self.selected_type = None
        self.selected_index = None
        self.update_plot()
    
    def update_atom_size(self, val):
        """Update atom marker size"""
        self.atom_size = int(self.slider_atom_size.val)
        self.update_plot()
    
    def update_atom_position(self, atom_idx, coord, text):
        """Update custom atom position coordinate"""
        try:
            value = float(text)
            # Initialize custom basis if not already done
            if self.custom_basis_positions is None:
                self.custom_basis_positions = self.basis.copy()
            
            # Update the specific coordinate
            if coord == 'x':
                self.custom_basis_positions[atom_idx][0] = value
            else:  # 'y'
                self.custom_basis_positions[atom_idx][1] = value
            
            self.loaded_atoms = None
            self.update_plot()
        except ValueError:
            print(f"Invalid coordinate input for Atom {atom_idx+1} {coord.upper()}: {text}")
    
    def reset_basis_positions(self, event):
        """Reset atom positions to default"""
        self.custom_basis_positions = None
        # Reset textboxes to default values
        for coord, atom_idx, tb in self.basis_textboxes:
            default_val = self.basis[atom_idx][0] if coord == 'x' else self.basis[atom_idx][1]
            tb.set_val(f"{default_val:.2f}")
        self.update_plot()
    
    def apply_atom_position_updates(self, event):
        """Apply all filled atom position coordinates to update the unit cell"""
        try:
            # Initialize custom basis if not already done
            if self.custom_basis_positions is None:
                self.custom_basis_positions = self.basis.copy()
            
            # Collect all coordinates from textboxes
            updated_basis = np.zeros_like(self.basis)
            
            for coord, atom_idx, tb in self.basis_textboxes:
                try:
                    value = float(tb.text)
                    if coord == 'x':
                        updated_basis[atom_idx][0] = value
                    else:  # 'y'
                        updated_basis[atom_idx][1] = value
                except ValueError:
                    print(f"Warning: Invalid value in Atom {atom_idx+1} {coord.upper()} textbox: {tb.text}")
                    # Keep previous value
                    if coord == 'x':
                        updated_basis[atom_idx][0] = self.custom_basis_positions[atom_idx][0]
                    else:
                        updated_basis[atom_idx][1] = self.custom_basis_positions[atom_idx][1]
            
            # Apply the updated basis
            self.custom_basis_positions = updated_basis
            self.loaded_atoms = None
            
            print("✓ Atom positions updated from textboxes")
            print(f"  Atom 1: ({updated_basis[0][0]:.2f}, {updated_basis[0][1]:.2f})")
            print(f"  Atom 2: ({updated_basis[1][0]:.2f}, {updated_basis[1][1]:.2f})")
            print(f"  Atom 3: ({updated_basis[2][0]:.2f}, {updated_basis[2][1]:.2f})")
            print(f"  Atom 4: ({updated_basis[3][0]:.2f}, {updated_basis[3][1]:.2f})")
            
            self.update_plot()
            
        except Exception as e:
            print(f"Error applying atom position updates: {e}")
    
    def save_plot_data(self, event):
        """Save current plot configuration including all parameters and atom positions"""
        print("\n" + "="*100)
        print("SAVE PLOT DATA")
        print("="*100)
        
        try:
            import tkinter as tk
            from tkinter import filedialog
            import pickle
            
            root = tk.Tk()
            root.withdraw()
            save_path = filedialog.asksaveasfilename(
                title="Save plot data as",
                defaultextension=".pkl",
                filetypes=[("Pickle files", "*.pkl"), ("All files", "*.*")]
            )
            root.destroy()
            
            if not save_path:
                print("Save cancelled - no path selected")
                return
            
            # Collect all current state
            plot_data = {
                'target_angle': self.target_angle,
                'current_profile': self.current_profile,
                'decay_rate': self.decay_rate,
                'global_scale': self.global_scale,
                'custom_decay_equation': self.custom_decay_equation,
                'atom_size': self.atom_size,
                'custom_basis_positions': self.custom_basis_positions.copy() if self.custom_basis_positions is not None else None,
                'loaded_atoms': self.loaded_atoms.copy() if self.loaded_atoms is not None else None,
                'corner_offsets': dict(self.corner_offsets),
                'edge_scales': dict(self.edge_scales),
                'petal_scales': self.petal_scales.copy(),
                'show_selection': self.show_selection,
            }
            
            with open(save_path, 'wb') as f:
                pickle.dump(plot_data, f)
            
            self.plot_data_file = save_path
            print(f"✓ Plot data saved to: {save_path}")
            print(f"  Angle: {self.target_angle}°")
            print(f"  Profile: {self.current_profile}")
            print(f"  Decay Rate: {self.decay_rate}")
            print(f"  Global Scale: {self.global_scale}")
            print(f"  Corner Offsets: {self.corner_offsets}")
            if self.custom_basis_positions is not None:
                print(f"  Custom Basis: Enabled")
            if self.loaded_atoms is not None:
                print(f"  Loaded Atoms: {len(self.loaded_atoms)} atoms")
            print("="*100 + "\n")
            
        except Exception as e:
            print(f"ERROR during save: {e}")
    
    def load_plot_data(self, event):
        """Load previously saved plot configuration"""
        print("\n" + "="*100)
        print("LOAD PLOT DATA")
        print("="*100)
        
        try:
            import tkinter as tk
            from tkinter import filedialog
            import pickle
            
            root = tk.Tk()
            root.withdraw()
            load_path = filedialog.askopenfilename(
                title="Load plot data from",
                filetypes=[("Pickle files", "*.pkl"), ("All files", "*.*")]
            )
            root.destroy()
            
            if not load_path:
                print("Load cancelled - no path selected")
                return
            
            with open(load_path, 'rb') as f:
                plot_data = pickle.load(f)
            
            # Restore all parameters
            self.target_angle = plot_data.get('target_angle', 72.0)
            self.current_profile = plot_data.get('current_profile', 'exponential')
            self.decay_rate = plot_data.get('decay_rate', 1.0)
            self.global_scale = plot_data.get('global_scale', 1.0)
            self.custom_decay_equation = plot_data.get('custom_decay_equation', 'exp(-3*x)')
            self.atom_size = plot_data.get('atom_size', 50)
            self.custom_basis_positions = plot_data.get('custom_basis_positions')
            self.loaded_atoms = plot_data.get('loaded_atoms')
            self.corner_offsets = plot_data.get('corner_offsets', {})
            self.edge_scales = plot_data.get('edge_scales', {})
            self.petal_scales = plot_data.get('petal_scales', [1.0, 1.0, 1.0, 1.0, 1.0])
            self.show_selection = plot_data.get('show_selection', True)
            
            # Update UI elements
            self.textbox_angle.set_val(str(self.target_angle))
            self.textbox_decay.set_val(str(self.decay_rate))
            self.textbox_gscale.set_val(str(self.global_scale))
            self.textbox_custom_eq.set_val(self.custom_decay_equation)
            self.slider_atom_size.set_val(self.atom_size)
            
            # Update radio button for profile
            profile_map = {'exponential': 0, 'gaussian': 1, 'polynomial': 2, 'custom': 3}
            if self.current_profile in profile_map:
                self.radio.set_active(profile_map[self.current_profile])
            
            # Update selection button state
            if self.show_selection:
                self.btn_select_toggle.label.set_text('Selection: ON')
                self.btn_select_toggle.color = 'lightgreen'
            else:
                self.btn_select_toggle.label.set_text('Selection: OFF')
                self.btn_select_toggle.color = '0.85'
            
            self.plot_data_file = load_path
            print(f"✓ Plot data loaded from: {load_path}")
            print(f"  Angle: {self.target_angle}°")
            print(f"  Profile: {self.current_profile}")
            print(f"  Decay Rate: {self.decay_rate}")
            print(f"  Global Scale: {self.global_scale}")
            print(f"  Corner Offsets: {self.corner_offsets}")
            if self.custom_basis_positions is not None:
                print(f"  Custom Basis: Enabled")
            if self.loaded_atoms is not None:
                print(f"  Loaded Atoms: {len(self.loaded_atoms)} atoms")
            print("="*100 + "\n")
            
            self.update_plot()
            
        except FileNotFoundError:
            print(f"ERROR: File not found")
        except Exception as e:
            print(f"ERROR during load: {e}")
    
    def toggle_matrix_display(self, event):
        """Toggle display of transformation matrix in GUI area"""
        self.show_matrix_in_gui = not self.show_matrix_in_gui
        if self.show_matrix_in_gui:
            self.btn_show_matrix.label.set_text('Matrix: ON')
            self.btn_show_matrix.color = '#B0E0E6'
        else:
            self.btn_show_matrix.label.set_text('Matrix: OFF')
            self.btn_show_matrix.color = '#E6E6FA'
        self.update_plot()
    
    def toggle_selection_visibility(self, event):
        """Toggle visibility of selection markers"""
        self.show_selection = not self.show_selection
        if self.show_selection:
            self.btn_select_toggle.label.set_text('Selection: ON')
            self.btn_select_toggle.color = 'lightgreen'
        else:
            self.btn_select_toggle.label.set_text('Selection: OFF')
            self.btn_select_toggle.color = '0.85'
        self.fig.canvas.draw_idle()
        self.update_plot()
    
    def update_angle_text(self, text):
        """Update target angle from text input"""
        try:
            angle = float(text)
            if 30.0 <= angle <= 150.0:  # Reasonable range
                self.target_angle = angle
                self.update_plot()
            else:
                print(f"Warning: Angle {angle}° outside reasonable range [30-150]")
        except ValueError:
            print(f"Invalid angle input: {text}")
    
    def update_decay_text(self, text):
        """Update decay rate from text input"""
        try:
            value = float(text)
            if 0.1 <= value <= 3.0:
                self.decay_rate = value
                self.update_plot()
            else:
                print(f"Warning: Decay rate {value} outside range [0.1-3.0]")
        except ValueError:
            print(f"Invalid decay rate input: {text}")
    
    def update_scale_text(self, text):
        """Update global scale from text input"""
        try:
            value = float(text)
            if 0.5 <= value <= 2.0:
                self.global_scale = value
                self.update_plot()
            else:
                print(f"Warning: Global scale {value} outside range [0.5-2.0]")
        except ValueError:
            print(f"Invalid global scale input: {text}")
    
    def update_custom_equation(self, text):
        """Update custom decay equation"""
        self.custom_decay_equation = text
        if self.current_profile == 'custom':
            self.update_plot()
    
    def export_matrices(self, event):
        """Export current transformation matrices to .npy files"""
        print("\n" + "="*100)
        print("EXPORT TRANSFORMATION MATRICES")
        print("="*100)
        
        try:
            import tkinter as tk
            from tkinter import filedialog
            
            # Create file dialog to select save directory
            root = tk.Tk()
            root.withdraw()
            save_dir = filedialog.askdirectory(
                title="Select directory to save matrices"
            )
            root.destroy()
            
            if not save_dir:
                print("Export cancelled - no directory selected")
                return
            
            basis_to_use = self.custom_basis_positions if self.custom_basis_positions is not None else self.basis

            # Get base lattice (transformed, one petal)
            if self.loaded_atoms is not None:
                atoms_base = np.array(self.loaded_atoms)
            else:
                atoms_base, corners_base, _, _ = create_lattice_with_correct_atom_positions(
                    self.n_cells, self.n_cells,
                    self.sq_a1 * self.global_scale,
                    self.sq_a2 * self.global_scale,
                    basis_to_use,
                    target_angle_deg=self.target_angle,
                    stretch_corner='bottom_left',
                    decay_profile=self.current_profile,
                    custom_equation=self.custom_decay_equation if self.current_profile == 'custom' else None,
                    custom_basis=self.custom_basis_positions
                )
            
            # Original square lattice atom positions (reference state)
            a_mag = np.linalg.norm(self.sq_a1 * self.global_scale)
            basis_frac = basis_to_use / a_mag
            
            atoms_original = []
            for i in range(self.n_cells):
                for j in range(self.n_cells):
                    cell_center = np.array([
                        (i - self.n_cells//2) * a_mag,
                        (j - self.n_cells//2) * a_mag
                    ])
                    for bf in basis_frac:
                        atom_pos = cell_center + bf * a_mag
                        atoms_original.append(atom_pos)
            
            atoms_original = np.array(atoms_original)
            
            # Create 36×36 matrices
            max_atoms = 36
            matrix_initial = np.zeros((36, 36))
            matrix_final = np.zeros((36, 36))
            
            num_atoms = min(len(atoms_original), max_atoms // 2)
            
            for atom_idx in range(num_atoms):
                x_col = atom_idx * 2
                y_col = atom_idx * 2 + 1
                
                if atom_idx < len(atoms_original):
                    # Initial state (original square lattice)
                    matrix_initial[atom_idx, x_col] = atoms_original[atom_idx, 0]
                    matrix_initial[atom_idx, y_col] = atoms_original[atom_idx, 1]
                    
                    # Final state (transformed)
                    matrix_final[atom_idx, x_col] = atoms_base[atom_idx, 0]
                    matrix_final[atom_idx, y_col] = atoms_base[atom_idx, 1]
            
            # Transformation matrix = Final - Initial
            matrix_transformation = matrix_final - matrix_initial
            
            # Create filename with timestamp
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Save matrices
            initial_file = f"{save_dir}/matrix_initial_{timestamp}.npy"
            final_file = f"{save_dir}/matrix_final_{timestamp}.npy"
            transform_file = f"{save_dir}/matrix_transformation_{timestamp}.npy"
            
            np.save(initial_file, matrix_initial)
            np.save(final_file, matrix_final)
            np.save(transform_file, matrix_transformation)
            
            print(f"✓ Initial matrix saved: {initial_file}")
            print(f"  Shape: {matrix_initial.shape}, Data type: {matrix_initial.dtype}")
            print(f"\n✓ Final matrix saved: {final_file}")
            print(f"  Shape: {matrix_final.shape}, Data type: {matrix_final.dtype}")
            print(f"\n✓ Transformation matrix saved: {transform_file}")
            print(f"  Shape: {matrix_transformation.shape}, Data type: {matrix_transformation.dtype}")
            
            # Also save a summary file
            summary_file = f"{save_dir}/export_summary_{timestamp}.txt"
            with open(summary_file, 'w') as f:
                f.write("="*100 + "\n")
                f.write("MATRIX EXPORT SUMMARY\n")
                f.write("="*100 + "\n")
                f.write(f"Export Date/Time: {timestamp}\n")
                f.write(f"Configuration: Angle={self.target_angle}°, Profile={self.current_profile}\n")
                f.write(f"Global Scale={self.global_scale}, Decay Rate={self.decay_rate}\n")
                f.write(f"Number of atoms: {num_atoms}\n")
                f.write(f"\nMatrix Files:\n")
                f.write(f"  Initial:       matrix_initial_{timestamp}.npy\n")
                f.write(f"  Final:         matrix_final_{timestamp}.npy\n")
                f.write(f"  Transformation: matrix_transformation_{timestamp}.npy\n")
                f.write(f"\nMatrix Format:\n")
                f.write(f"  Shape: 36×36\n")
                f.write(f"  Row index: atom ID (0-{num_atoms-1})\n")
                f.write(f"  Columns: [x₁, y₁, x₂, y₂, ..., x₁₈, y₁₈]\n")
                f.write(f"  Non-filled rows and atoms: zero-padded\n")
                f.write("="*100 + "\n")
            
            print(f"\n✓ Summary saved: {summary_file}")
            print(f"\n{'='*100}")
            print("Export complete! All matrices saved successfully.")
            print(f"{'='*100}\n")
            
        except Exception as e:
            print(f"ERROR during export: {e}")
    
    def get_transformation_matrix(self, event):
        """Extract and display 36×36 transformation matrices for atom positions"""
        print("\n" + "="*100)
        print("36×36 TRANSFORMATION MATRIX SYSTEM")
        print("="*100)
        print(f"Configuration: Angle={self.target_angle}°, Profile={self.current_profile}")
        print(f"Global Scale={self.global_scale}, Decay Rate={self.decay_rate}")
        print(f"Custom Basis: {self.custom_basis_positions}")
        
        basis_to_use = self.custom_basis_positions if self.custom_basis_positions is not None else self.basis

        # Get base lattice (transformed, one petal)
        if self.loaded_atoms is not None:
            atoms_base = np.array(self.loaded_atoms)
        else:
            atoms_base, corners_base, _, _ = create_lattice_with_correct_atom_positions(
                self.n_cells, self.n_cells,
                self.sq_a1 * self.global_scale,
                self.sq_a2 * self.global_scale,
                basis_to_use,
                target_angle_deg=self.target_angle,
                stretch_corner='bottom_left',
                decay_profile=self.current_profile,
                custom_equation=self.custom_decay_equation if self.current_profile == 'custom' else None,
                custom_basis=self.custom_basis_positions
            )
        
        # Original square lattice atom positions (reference state)
        a_mag = np.linalg.norm(self.sq_a1 * self.global_scale)
        basis_frac = basis_to_use / a_mag
        
        atoms_original = []
        for i in range(self.n_cells):
            for j in range(self.n_cells):
                cell_center = np.array([
                    (i - self.n_cells//2) * a_mag,
                    (j - self.n_cells//2) * a_mag
                ])
                for bf in basis_frac:
                    atom_pos = cell_center + bf * a_mag
                    atoms_original.append(atom_pos)
        
        atoms_original = np.array(atoms_original)
        
        # Create 36×36 matrices: row=atom_index, columns=[x, y] × 18 atoms
        # Pad to 36 rows if fewer atoms
        max_atoms = 36
        
        # Initialize matrices with zeros (36×36)
        matrix_initial = np.zeros((36, 36))
        matrix_final = np.zeros((36, 36))
        
        # Fill matrices: each atom gets 2 columns for [x, y]
        num_atoms = min(len(atoms_original), max_atoms // 2)
        
        for atom_idx in range(num_atoms):
            x_col = atom_idx * 2
            y_col = atom_idx * 2 + 1
            
            if atom_idx < len(atoms_original):
                # Initial state (original square lattice)
                matrix_initial[atom_idx, x_col] = atoms_original[atom_idx, 0]
                matrix_initial[atom_idx, y_col] = atoms_original[atom_idx, 1]
                
                # Final state (transformed)
                matrix_final[atom_idx, x_col] = atoms_base[atom_idx, 0]
                matrix_final[atom_idx, y_col] = atoms_base[atom_idx, 1]
        
        # Transformation matrix = Final - Initial
        matrix_transformation = matrix_final - matrix_initial
        
        print(f"\n{'-'*100}")
        print(f"MATRIX DIMENSIONS: 36×36")
        print(f"FORMAT: Row index = atom ID, Columns = [x₁, y₁, x₂, y₂, ..., x₁₈, y₁₈]")
        print(f"ATOMS ENCODED: {num_atoms} atoms (rows 0-{num_atoms-1})")
        print(f"{'-'*100}")
        
        # Display initial state matrix (36×36)
        print(f"\n📍 INITIAL STATE MATRIX (36×36) - Original Square Lattice:")
        print(f"{'-'*100}")
        np.set_printoptions(precision=2, suppress=True, linewidth=200)
        print(matrix_initial)
        
        # Display final state matrix (36×36)
        print(f"\n✨ FINAL STATE MATRIX (36×36) - Transformed/Customized Configuration:")
        print(f"{'-'*100}")
        print(matrix_final)
        
        # Display transformation matrix (36×36)
        print(f"\n🔄 TRANSFORMATION MATRIX (36×36) - Displacement Field (Final - Initial):")
        print(f"{'-'*100}")
        print(matrix_transformation)
        
        # Statistics
        print(f"\n{'-'*100}")
        print(f"TRANSFORMATION STATISTICS:")
        print(f"{'-'*100}")
        max_displacement = np.max(np.abs(matrix_transformation[matrix_transformation != 0]))
        mean_displacement = np.mean(np.abs(matrix_transformation[matrix_transformation != 0]))
        non_zero_elements = np.count_nonzero(matrix_transformation)
        
        print(f"Non-zero elements in transformation: {non_zero_elements}/{36*36}")
        print(f"Mean displacement magnitude: {mean_displacement:.4f} nm")
        print(f"Max displacement magnitude: {max_displacement:.4f} nm")
        
        # Per-atom analysis
        print(f"\n{'-'*100}")
        print(f"PER-ATOM TRANSFORMATION ANALYSIS:")
        print(f"{'-'*100}")
        print(f"{'Atom':>4} | {'Original Position':>20} | {'Final Position':>20} | {'Displacement':>20} | {'|Δ|':>8}")
        print(f"{'-'*100}")
        
        for idx in range(num_atoms):
            orig_pos = atoms_original[idx]
            final_pos = atoms_base[idx]
            displacement = final_pos - orig_pos
            dist = np.linalg.norm(displacement)
            print(f"{idx:4d} | [{orig_pos[0]:8.2f}, {orig_pos[1]:8.2f}] | "
                  f"[{final_pos[0]:8.2f}, {final_pos[1]:8.2f}] | "
                  f"[{displacement[0]:8.2f}, {displacement[1]:8.2f}] | {dist:8.2f}")
        
        # Corner deformations (if any)
        if self.corner_offsets:
            print(f"\n{'-'*100}")
            print(f"CORNER OFFSET ADJUSTMENTS (Fabric Deformation):")
            print(f"{'-'*100}")
            for corner_idx, offset in self.corner_offsets.items():
                print(f"  Corner {corner_idx}: Δx={offset[0]:8.2f}, Δy={offset[1]:8.2f} nm")
        
        # Custom basis (if modified)
        if self.custom_basis_positions is not None:
            print(f"\n{'-'*100}")
            print(f"CUSTOM BASIS POSITIONS (User-Modified Atoms):")
            print(f"{'-'*100}")
            for atom_idx in range(len(self.custom_basis_positions)):
                pos = self.custom_basis_positions[atom_idx]
                orig = self.basis[atom_idx % len(self.basis)]
                print(f"  Atom {atom_idx}: Original={orig} → Custom={pos}")
        
        print(f"\n{'='*100}")
        print(f"36×36 MATRIX DATA EXPORT COMPLETE")
        print(f"Matrices ready for transformation pipeline or ML training")
        print(f"{'='*100}\n")
    
    def load_transformation_matrix(self, event):
        """Load a 36×36 transformation matrix and apply it to current structure"""
        print("\n" + "="*100)
        print("LOAD TRANSFORMATION MATRIX")
        print("="*100)
        print("Enter transformation matrix as numpy array (36×36)")
        print("Expected format: [[dx₁₁, dy₁₁, dx₁₂, dy₁₂, ...], [row2], ...]")
        print("Or load from file: Enter 'file:/path/to/matrix.npy' or press Enter for console input")
        print("-"*100)
        
        try:
            # Try to get input from user - for now use a file dialog approach
            import tkinter as tk
            from tkinter import filedialog
            
            root = tk.Tk()
            root.withdraw()
            file_path = filedialog.askopenfilename(
                title="Select transformation matrix .npy file",
                filetypes=[("NumPy files", "*.npy"), ("All files", "*.*")]
            )
            root.destroy()
            
            if not file_path:
                print("No file selected. Transformation matrix loading cancelled.")
                return
            
            # Load the matrix
            transform_matrix = np.load(file_path)
            
            if transform_matrix.shape != (36, 36):
                print(f"ERROR: Expected 36×36 matrix, got {transform_matrix.shape}")
                return
            
            print(f"✓ Loaded transformation matrix from: {file_path}")
            print(f"  Matrix shape: {transform_matrix.shape}")
            print(f"  Data type: {transform_matrix.dtype}")
            
            # Apply transformation to current atoms
            # Get base atoms
            atoms_base, _, _, _ = create_lattice_with_correct_atom_positions(
                self.n_cells, self.n_cells,
                self.sq_a1 * self.global_scale,
                self.sq_a2 * self.global_scale,
                self.basis,
                target_angle_deg=self.target_angle,
                stretch_corner='bottom_left',
                decay_profile=self.current_profile
            )
            
            # Extract atom positions from transformation matrix
            num_atoms = min(18, len(atoms_base))
            atoms_transformed = []
            
            for atom_idx in range(num_atoms):
                x_col = atom_idx * 2
                y_col = atom_idx * 2 + 1
                
                if x_col < 36 and y_col < 36:
                    dx = transform_matrix[atom_idx, x_col]
                    dy = transform_matrix[atom_idx, y_col]
                    
                    # Apply transformation: new_pos = base_pos + transformation
                    if atom_idx < len(atoms_base):
                        new_pos = atoms_base[atom_idx] + np.array([dx, dy])
                        atoms_transformed.append(new_pos)
            
            # Store and plot transformed atoms
            if atoms_transformed:
                # Store transformation for visualization
                self.loaded_atoms = np.array(atoms_transformed)
                self.custom_basis_positions = None
                print(f"✓ Applied transformation to {len(atoms_transformed)} atoms")
                
                self.update_plot()
                print(f"✓ Plot updated with transformed structure")
            else:
                print("ERROR: Could not extract atom positions from transformation matrix")
            
            print("="*100 + "\n")
            
        except FileNotFoundError:
            print("ERROR: File not found")
        except ValueError as e:
            print(f"ERROR: Invalid matrix format - {e}")
        except Exception as e:
            print(f"ERROR: {e}")
    
    def load_final_matrix(self, event):
        """Load a 36×36 final matrix and plot the resulting structure"""
        print("\n" + "="*100)
        print("LOAD FINAL MATRIX")
        print("="*100)
        print("Enter final state matrix (36×36) to plot the resulting structure")
        print("Expected format: [[x₁, y₁, x₂, y₂, ...], [row2], ...]")
        print("Select .npy file containing the final matrix")
        print("-"*100)
        
        try:
            import tkinter as tk
            from tkinter import filedialog
            
            root = tk.Tk()
            root.withdraw()
            file_path = filedialog.askopenfilename(
                title="Select final matrix .npy file",
                filetypes=[("NumPy files", "*.npy"), ("All files", "*.*")]
            )
            root.destroy()
            
            if not file_path:
                print("No file selected. Final matrix loading cancelled.")
                return
            
            # Load the matrix
            final_matrix = np.load(file_path)
            
            if final_matrix.shape != (36, 36):
                print(f"ERROR: Expected 36×36 matrix, got {final_matrix.shape}")
                return
            
            print(f"✓ Loaded final matrix from: {file_path}")
            print(f"  Matrix shape: {final_matrix.shape}")
            print(f"  Data type: {final_matrix.dtype}")
            
            # Extract atom positions from final matrix
            atoms_final = []
            num_atoms = 18
            
            for atom_idx in range(num_atoms):
                x_col = atom_idx * 2
                y_col = atom_idx * 2 + 1
                
                if x_col < 36 and y_col < 36:
                    x = final_matrix[atom_idx, x_col]
                    y = final_matrix[atom_idx, y_col]
                    
                    # Only add non-zero positions
                    if x != 0 or y != 0:
                        atoms_final.append([x, y])
            
            # Store and plot final atoms
            if atoms_final:
                atoms_final = np.array(atoms_final)
                self.loaded_atoms = atoms_final
                self.custom_basis_positions = None
                print(f"✓ Extracted {len(atoms_final)} atoms from final matrix")
                self.update_plot()
                print(f"✓ Plot updated with final matrix structure")
            else:
                print("ERROR: No valid atom positions found in final matrix")
            
            print("="*100 + "\n")
            
        except FileNotFoundError:
            print("ERROR: File not found")
        except ValueError as e:
            print(f"ERROR: Invalid matrix format - {e}")
        except Exception as e:
            print(f"ERROR: {e}")
    
    def load_initial_matrix(self, event):
        """Load a 36×36 initial matrix and plot the original structure"""
        print("\n" + "="*100)
        print("LOAD INITIAL MATRIX")
        print("="*100)
        print("Enter initial state matrix (36×36) to plot the original structure")
        print("Expected format: [[x₁, y₁, x₂, y₂, ...], [row2], ...]")
        print("Select .npy file containing the initial matrix")
        print("-"*100)
        
        try:
            import tkinter as tk
            from tkinter import filedialog
            
            root = tk.Tk()
            root.withdraw()
            file_path = filedialog.askopenfilename(
                title="Select initial matrix .npy file",
                filetypes=[("NumPy files", "*.npy"), ("All files", "*.*")]
            )
            root.destroy()
            
            if not file_path:
                print("No file selected. Initial matrix loading cancelled.")
                return
            
            # Load the matrix
            initial_matrix = np.load(file_path)
            
            if initial_matrix.shape != (36, 36):
                print(f"ERROR: Expected 36×36 matrix, got {initial_matrix.shape}")
                return
            
            print(f"✓ Loaded initial matrix from: {file_path}")
            print(f"  Matrix shape: {initial_matrix.shape}")
            print(f"  Data type: {initial_matrix.dtype}")
            
            # Extract atom positions from initial matrix
            atoms_initial = []
            num_atoms = 18
            
            for atom_idx in range(num_atoms):
                x_col = atom_idx * 2
                y_col = atom_idx * 2 + 1
                
                if x_col < 36 and y_col < 36:
                    x = initial_matrix[atom_idx, x_col]
                    y = initial_matrix[atom_idx, y_col]
                    
                    # Only add non-zero positions
                    if x != 0 or y != 0:
                        atoms_initial.append([x, y])
            
            # Store and plot initial atoms
            if atoms_initial:
                atoms_initial = np.array(atoms_initial)
                self.loaded_atoms = atoms_initial
                self.custom_basis_positions = None
                print(f"✓ Extracted {len(atoms_initial)} atoms from initial matrix")
                self.update_plot()
                print(f"✓ Plot updated with initial matrix structure")
            else:
                print("ERROR: No valid atom positions found in initial matrix")
            
            print("="*100 + "\n")
            
        except FileNotFoundError:
            print("ERROR: File not found")
        except ValueError as e:
            print(f"ERROR: Invalid matrix format - {e}")
        except Exception as e:
            print(f"ERROR: {e}")
    
    # ========================================================================
    # MEEP ELECTROMAGNETIC SIMULATION METHODS
    # ========================================================================
    
    def update_meep_frequency(self, text):
        """Update MEEP simulation frequency"""
        try:
            freq = float(text)
            if 0.01 <= freq <= 1.0:
                self.meep_frequency = freq
                self.meep_wavelength = 1.0 / freq
                self.textbox_wavelength.set_val(f"{self.meep_wavelength:.2f}")
                print(f"✓ Frequency set to {freq:.3f} (λ = {self.meep_wavelength:.2f})")
            else:
                print(f"Invalid frequency: {freq} (must be 0.01-1.0)")
        except ValueError:
            print(f"Invalid frequency input: {text}")
    
    def update_meep_wavelength(self, text):
        """Update MEEP simulation wavelength"""
        try:
            wl = float(text)
            if 1.0 <= wl <= 100.0:
                self.meep_wavelength = wl
                self.meep_frequency = 1.0 / wl
                self.textbox_freq.set_val(f"{self.meep_frequency:.3f}")
                print(f"✓ Wavelength set to {wl:.2f} (f = {self.meep_frequency:.3f})")
            else:
                print(f"Invalid wavelength: {wl} (must be 1.0-100.0)")
        except ValueError:
            print(f"Invalid wavelength input: {text}")
    
    def update_meep_resolution(self, text):
        """Update MEEP resolution"""
        try:
            res = int(text)
            if 5 <= res <= 50:
                self.meep_resolution = res
                print(f"✓ Resolution set to {res} pixels/unit")
            else:
                print(f"Invalid resolution: {res} (must be 5-50)")
        except ValueError:
            print(f"Invalid resolution input: {text}")
    
    def update_meep_cylinder_radius(self, text):
        """Update MEEP cylinder radius"""
        try:
            radius = float(text)
            if 10.0 <= radius <= 200.0:
                self.meep_cylinder_radius = radius
                print(f"✓ Cylinder radius set to {radius:.1f} nm")
            else:
                print(f"Invalid radius: {radius} (must be 10-200 nm)")
        except ValueError:
            print(f"Invalid radius input: {text}")
    
    def update_meep_epsilon(self, text):
        """Update MEEP dielectric constant"""
        try:
            eps = float(text)
            if 1.0 <= eps <= 20.0:
                self.meep_epsilon = eps
                print(f"✓ Dielectric constant set to {eps:.1f}")
            else:
                print(f"Invalid epsilon: {eps} (must be 1.0-20.0)")
        except ValueError:
            print(f"Invalid epsilon input: {text}")
    
    def update_meep_runtime(self, text):
        """Update MEEP runtime"""
        try:
            runtime = int(text)
            if 50 <= runtime <= 1000:
                self.meep_runtime = runtime
                print(f"✓ Runtime set to {runtime} time steps")
            else:
                print(f"Invalid runtime: {runtime} (must be 50-1000)")
        except ValueError:
            print(f"Invalid runtime input: {text}")
    
    def update_meep_field_selection(self, label):
        """Update field visualization selection"""
        if label == 'Hz':
            self.meep_show_hz = not self.meep_show_hz
        elif label == 'Ex':
            self.meep_show_ex = not self.meep_show_ex
        elif label == 'Ey':
            self.meep_show_ey = not self.meep_show_ey
        
        # Update button label
        fields = []
        if self.meep_show_hz:
            fields.append('Hz')
        if self.meep_show_ex:
            fields.append('Ex')
        if self.meep_show_ey:
            fields.append('Ey')
        
        if fields:
            self.btn_meep_show.label.set_text(f"Show {','.join(fields)}")
        else:
            self.btn_meep_show.label.set_text("Show Fields")
    
    def toggle_gpu_acceleration(self, event):
        """Toggle GPU acceleration for simulations"""
        if not self.gpu_available:
            print("⚠ GPU not available on this system")
            return
        
        self.gpu_enabled = not self.gpu_enabled
        
        if self.gpu_enabled:
            # Initialize GPU accelerator
            self.gpu_accelerator = GPUAccelerator(use_gpu=True)
            self.btn_gpu_toggle.label.set_text('GPU: ON')
            self.btn_gpu_toggle.color = '#B0FFB0'  # Light green
            
            # Enable MEEP GPU if available
            if self.meep_enabled:
                enable_meep_gpu()
            
            print(f"\n{'='*80}")
            print(f"✓ GPU ACCELERATION ENABLED")
            print(f"{'='*80}")
            print(f"Device: {self.gpu_name}")
            print(f"Status: {self.gpu_accelerator.get_status()}")
            print(f"\nAccelerated operations:")
            print(f"  - Band structure FFT calculations")
            print(f"  - Hz field mode analysis")
            print(f"  - Large array operations")
            print(f"  - MEEP electromagnetic simulation (if supported)")
            print(f"{'='*80}\n")
        else:
            # Disable GPU accelerator
            self.gpu_accelerator = None
            self.btn_gpu_toggle.label.set_text('GPU: OFF')
            self.btn_gpu_toggle.color = '#FFB0B0'  # Light red
            
            print(f"\n{'='*80}")
            print(f"⚠ GPU ACCELERATION DISABLED - Using CPU")
            print(f"{'='*80}\n")
        
        self.fig.canvas.draw_idle()
    
    def setup_meep_simulation(self, event):
        """Setup MEEP simulation with current pentagon structure"""
        if not self.meep_enabled:
            print("\n" + "="*80)
            print("ERROR: MEEP electromagnetic simulation not available")
            print("="*80)
            print("PyMeep is not properly installed or incompatible version detected.")
            print("\n🔧 INSTALLATION INSTRUCTIONS:")
            print("  1. Install Miniconda/Anaconda if not available:")
            print("     wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh")
            print("     bash Miniconda3-latest-Linux-x86_64.sh")
            print("\n  2. Install official PyMeep:")
            print("     conda install -c conda-forge pymeep")
            print("\n  3. Restart Python and run this script again")
            print("\n📖 Full documentation:")
            print("     https://meep.readthedocs.io/en/latest/Installation/")
            print("="*80)
            return
        
        print("\n" + "="*80)
        print("MEEP ELECTROMAGNETIC SIMULATION SETUP")
        print("="*80)
        
        if self.gpu_enabled:
            print(f"GPU Acceleration: ENABLED ({self.gpu_name})")
        else:
            print(f"GPU Acceleration: DISABLED (CPU only)")
        print("-"*80)
        
        try:
            # Validate MEEP API availability (ensure official pymeep)
            if not hasattr(mp, 'Medium'):
                print("ERROR: 'meep' module missing mp.Medium. This is not the official PyMeep package.")
                print("Install official PyMeep: https://meep.readthedocs.io/en/latest/Installation/")
                return
            if not (hasattr(mp, 'Cylinder') or hasattr(mp, 'Block')):
                print("ERROR: 'meep' module missing geometry primitives (Cylinder/Block).")
                print("Install official PyMeep: https://meep.readthedocs.io/en/latest/Installation/")
                return

            # Validate key inputs
            if self.meep_frequency <= 0:
                print("ERROR: Frequency must be > 0. Check Freq input.")
                return
            if self.meep_resolution <= 0:
                print("ERROR: Resolution must be > 0. Check Res input.")
                return
            if self.meep_wavelength <= 0:
                print("ERROR: Wavelength must be > 0. Check λ input.")
                return
            if self.meep_cylinder_radius <= 0:
                print("ERROR: Cylinder radius must be > 0. Check R(nm) input.")
                return

            # Get all atom positions from current structure
            all_atoms = []
            for i in range(5):
                angle = i * 72.0
                rot_rad = np.deg2rad(angle)
                cos_a, sin_a = np.cos(rot_rad), np.sin(rot_rad)
                rot_matrix = np.array([[cos_a, -sin_a], [sin_a, cos_a]])
                
                atoms, _ = self.create_single_petal()
                if self.loaded_atoms is not None:
                    atoms = np.array(self.loaded_atoms)
                
                petal_scale = self.petal_scales[i]
                atoms_scaled = atoms * petal_scale
                atoms_rot = (rot_matrix @ atoms_scaled.T).T
                all_atoms.extend(atoms_rot)
            
            all_atoms = np.array(all_atoms)
            if all_atoms.size == 0:
                print("ERROR: No atom positions found. Check lattice/atom settings.")
                return
            if not np.isfinite(all_atoms).all():
                print("ERROR: Atom positions contain invalid values (NaN/Inf).")
                return
            
            # Calculate simulation domain
            x_min, y_min = all_atoms.min(axis=0)
            x_max, y_max = all_atoms.max(axis=0)
            padding = 500  # nm padding
            
            cell_sx = (x_max - x_min + 2 * padding)
            cell_sy = (y_max - y_min + 2 * padding)
            if cell_sx <= 0 or cell_sy <= 0:
                print("ERROR: Invalid simulation domain size. Check atom positions.")
                return
            
            # Normalize coordinates to MEEP units (divide by wavelength scale)
            scale_factor = self.meep_wavelength * 100  # Scale to reasonable MEEP units
            if scale_factor <= 0:
                print("ERROR: Invalid scale factor from wavelength. Check λ input.")
                return
            cell_sx_meep = cell_sx / scale_factor
            cell_sy_meep = cell_sy / scale_factor
            if cell_sx_meep <= 0 or cell_sy_meep <= 0:
                print("ERROR: Invalid MEEP cell size. Check λ/scale inputs.")
                return
            
            print(f"Domain: {cell_sx:.1f} × {cell_sy:.1f} nm")
            print(f"MEEP cell: {cell_sx_meep:.2f} × {cell_sy_meep:.2f} units")
            print(f"Atoms: {len(all_atoms)}")
            print(f"Frequency: {self.meep_frequency:.3f}, Wavelength: {self.meep_wavelength:.2f}")
            print(f"Resolution: {self.meep_resolution}, Hole radius: {self.meep_cylinder_radius:.1f} nm")
            print(f"Substrate epsilon: {self.meep_epsilon:.1f}")
            print(f"Air hole epsilon: {self.meep_air_epsilon:.1f}")
            
            # Create MEEP geometry
            geometry = []
            center_x = (x_max + x_min) / 2
            center_y = (y_max + y_min) / 2
            
            for atom_pos in all_atoms:
                # Convert to MEEP coordinates (centered at origin)
                x_meep = (atom_pos[0] - center_x) / scale_factor
                y_meep = (atom_pos[1] - center_y) / scale_factor
                r_meep = self.meep_cylinder_radius / scale_factor
                if r_meep <= 0:
                    print("ERROR: Cylinder radius in MEEP units must be > 0.")
                    return

                # Create air holes at lattice sites (Cylinder preferred, Block fallback)
                material = mp.Medium(epsilon=self.meep_air_epsilon)
                if hasattr(mp, 'Cylinder'):
                    geometry.append(mp.Cylinder(
                        radius=r_meep,
                        center=mp.Vector3(x_meep, y_meep, 0),
                        height=mp.inf,
                        material=material
                    ))
                elif hasattr(mp, 'Block'):
                    side = 2 * r_meep
                    print("Warning: mp.Cylinder not available. Using mp.Block as fallback.")
                    geometry.append(mp.Block(
                        size=mp.Vector3(side, side, mp.inf),
                        center=mp.Vector3(x_meep, y_meep, 0),
                        material=material
                    ))
                else:
                    print("ERROR: MEEP geometry primitives not available. Install the official pymeep package.")
                    return
            
            print(f"Created {len(geometry)} cylinders")
            
            # Create MEEP cell (2D simulation)
            cell = mp.Vector3(cell_sx_meep, cell_sy_meep, 0)
            self.meep_cell_size = cell
            
            # Add source (plane wave from left)
            sources = [mp.Source(
                mp.ContinuousSource(frequency=self.meep_frequency),
                component=mp.Hz,
                center=mp.Vector3(-cell_sx_meep/2 + 1, 0, 0),
                size=mp.Vector3(0, cell_sy_meep, 0)
            )]
            
            # Create PML boundary layers
            pml_layers = [mp.PML(1.0)]
            
            # Create simulation
            substrate_material = mp.Medium(epsilon=self.meep_epsilon)
            self.meep_sim = mp.Simulation(
                cell_size=cell,
                geometry=geometry,
                sources=sources,
                boundary_layers=pml_layers,
                resolution=self.meep_resolution,
                dimensions=2,
                default_material=substrate_material
            )
            
            print(f"✓ MEEP simulation configured")
            print(f"  Cell: {cell_sx_meep:.2f} × {cell_sy_meep:.2f}")
            print(f"  Geometry: {len(geometry)} objects")
            print(f"  Source: Plane wave Hz at frequency {self.meep_frequency:.3f}")
            print(f"  PML boundaries: 1.0 thickness")
            print("="*80 + "\n")
            
        except Exception as e:
            print(f"ERROR during MEEP setup: {e}")
            import traceback
            traceback.print_exc()
    
    def run_meep_simulation(self, event):
        """Run MEEP simulation"""
        if not self.meep_enabled:
            print("ERROR: MEEP not available")
            return
        
        if self.meep_sim is None:
            print("ERROR: Setup simulation first (click 'Setup Sim')")
            return
        if self.meep_cell_size is None:
            print("ERROR: Simulation cell not initialized. Please click 'Setup Sim' again.")
            return
        
        print("\n" + "="*80)
        print("RUNNING MEEP SIMULATION")
        print("="*80)
        
        try:
            # Run simulation
            print(f"Running {self.meep_runtime} time steps...")
            self.meep_sim.run(until=self.meep_runtime)
            
            # Extract field data
            self.meep_field_data = {
                'Hz': None,
                'Ex': None,
                'Ey': None,
                'eps': None
            }
            
            # Get Hz field
            if self.meep_show_hz or True:  # Always get Hz
                hz_data = self.meep_sim.get_array(
                    component=mp.Hz,
                    vol=mp.Volume(center=mp.Vector3(), size=self.meep_cell_size)
                )
                self.meep_field_data['Hz'] = hz_data
                print(f"✓ Hz field extracted: shape {hz_data.shape}")
            
            # Get Ex field
            if self.meep_show_ex:
                ex_data = self.meep_sim.get_array(
                    component=mp.Ex,
                    vol=mp.Volume(center=mp.Vector3(), size=self.meep_cell_size)
                )
                self.meep_field_data['Ex'] = ex_data
                print(f"✓ Ex field extracted: shape {ex_data.shape}")
            
            # Get Ey field
            if self.meep_show_ey:
                ey_data = self.meep_sim.get_array(
                    component=mp.Ey,
                    vol=mp.Volume(center=mp.Vector3(), size=self.meep_cell_size)
                )
                self.meep_field_data['Ey'] = ey_data
                print(f"✓ Ey field extracted: shape {ey_data.shape}")
            
            # Get epsilon (structure)
            eps_data = self.meep_sim.get_array(
                component=mp.Dielectric,
                vol=mp.Volume(center=mp.Vector3(), size=self.meep_cell_size)
            )
            self.meep_field_data['eps'] = eps_data
            print(f"✓ Dielectric structure extracted: shape {eps_data.shape}")
            
            print("="*80)
            print("✓ SIMULATION COMPLETE")
            print("Click 'Show Hz' (or Show Ex/Ey) to visualize fields")
            print("="*80 + "\n")
            
        except Exception as e:
            print(f"ERROR during MEEP simulation: {e}")
            import traceback
            traceback.print_exc()
    
    def show_meep_fields(self, event):
        """Display MEEP electromagnetic fields"""
        if self.meep_field_data is None:
            print("ERROR: Run simulation first (click 'Run Sim')")
            return
        
        print("\n" + "="*80)
        print("VISUALIZING ELECTROMAGNETIC FIELDS")
        print("="*80)
        
        try:
            # Create new figure for field visualization
            fig_fields = plt.figure(figsize=(16, 12))
            
            fields_to_plot = []
            if self.meep_show_hz and self.meep_field_data['Hz'] is not None:
                fields_to_plot.append(('Hz', self.meep_field_data['Hz']))
            if self.meep_show_ex and self.meep_field_data['Ex'] is not None:
                fields_to_plot.append(('Ex', self.meep_field_data['Ex']))
            if self.meep_show_ey and self.meep_field_data['Ey'] is not None:
                fields_to_plot.append(('Ey', self.meep_field_data['Ey']))
            
            if not fields_to_plot:
                # Default to Hz if nothing selected
                if self.meep_field_data['Hz'] is not None:
                    fields_to_plot = [('Hz', self.meep_field_data['Hz'])]
            
            n_fields = len(fields_to_plot)
            
            for idx, (field_name, field_data) in enumerate(fields_to_plot):
                ax = fig_fields.add_subplot(n_fields, 2, idx*2 + 1)
                
                # Plot field
                im = ax.imshow(np.transpose(field_data), interpolation='spline36', 
                              cmap='RdBu', origin='lower')
                ax.set_title(f'{field_name} Field (Real)', fontsize=12, fontweight='bold')
                ax.set_xlabel('x')
                ax.set_ylabel('y')
                plt.colorbar(im, ax=ax, label=f'{field_name}')
                
                # Plot structure overlay
                ax_struct = fig_fields.add_subplot(n_fields, 2, idx*2 + 2)
                if self.meep_field_data['eps'] is not None:
                    # Show field with structure overlay
                    im2 = ax_struct.imshow(np.transpose(field_data), interpolation='spline36',
                                          cmap='RdBu', origin='lower', alpha=0.7)
                    eps_plot = np.transpose(self.meep_field_data['eps'])
                    ax_struct.contour(eps_plot, levels=[1.5], colors='black', linewidths=1.5)
                    ax_struct.set_title(f'{field_name} with Structure', fontsize=12, fontweight='bold')
                    ax_struct.set_xlabel('x')
                    ax_struct.set_ylabel('y')
                    plt.colorbar(im2, ax=ax_struct, label=f'{field_name}')
            
            # Add overall title
            fig_fields.suptitle(f'Electromagnetic Field Visualization (f={self.meep_frequency:.3f}, λ={self.meep_wavelength:.2f})',
                              fontsize=14, fontweight='bold')
            
            plt.tight_layout()
            plt.show()
            
            print(f"✓ Displayed {n_fields} field component(s)")
            print("="*80 + "\n")
            
        except Exception as e:
            print(f"ERROR during field visualization: {e}")
            import traceback
            traceback.print_exc()
    
    def clear_meep_simulation(self, event):
        """Clear MEEP simulation data"""
        self.meep_sim = None
        self.meep_field_data = None
        print("✓ MEEP simulation data cleared")
    
    def export_meep_fields(self, event):
        """Export MEEP field data to files"""
        if self.meep_field_data is None:
            print("ERROR: No field data to export. Run simulation first.")
            return
        
        print("\n" + "="*80)
        print("EXPORT MEEP FIELD DATA")
        print("="*80)
        
        try:
            import tkinter as tk
            from tkinter import filedialog
            
            root = tk.Tk()
            root.withdraw()
            save_dir = filedialog.askdirectory(
                title="Select directory to save MEEP field data"
            )
            root.destroy()
            
            if not save_dir:
                print("Export cancelled")
                return
            
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Save field data
            for field_name, field_data in self.meep_field_data.items():
                if field_data is not None:
                    filename = f"{save_dir}/meep_{field_name}_{timestamp}.npy"
                    np.save(filename, field_data)
                    print(f"✓ {field_name} saved: {filename}")
            
            # Save simulation parameters
            params_file = f"{save_dir}/meep_params_{timestamp}.txt"
            with open(params_file, 'w') as f:
                f.write(f"MEEP Simulation Parameters\n")
                f.write(f"==========================\n")
                f.write(f"Frequency: {self.meep_frequency:.3f}\n")
                f.write(f"Wavelength: {self.meep_wavelength:.2f}\n")
                f.write(f"Resolution: {self.meep_resolution}\n")
                f.write(f"Cylinder radius: {self.meep_cylinder_radius:.1f} nm\n")
                f.write(f"Dielectric constant: {self.meep_epsilon:.1f}\n")
                f.write(f"Runtime: {self.meep_runtime} steps\n")
                f.write(f"Timestamp: {timestamp}\n")
            
            print(f"✓ Parameters saved: {params_file}")
            print("="*80 + "\n")
            
        except Exception as e:
            print(f"ERROR during export: {e}")
    
    # ========================================================================
    # BAND STRUCTURE CALCULATION METHODS
    # ========================================================================
    
    def update_num_bands(self, text):
        """Update number of bands to calculate"""
        try:
            value = int(text)
            if 1 <= value <= 20:
                self.meep_num_bands = value
                print(f"Number of bands: {self.meep_num_bands}")
            else:
                print("Number of bands must be between 1 and 20")
        except ValueError:
            print(f"Invalid number of bands: {text}")
    
    def update_k_points(self, text):
        """Update number of k-points"""
        try:
            value = int(text)
            if 5 <= value <= 100:
                self.meep_k_points = value
                print(f"Number of k-points: {self.meep_k_points}")
            else:
                print("Number of k-points must be between 5 and 100")
        except ValueError:
            print(f"Invalid number of k-points: {text}")
    
    def update_freq_min(self, text):
        """Update minimum frequency for band diagram"""
        try:
            value = float(text)
            if 0.0 <= value < self.meep_freq_max:
                self.meep_freq_min = value
                print(f"Minimum frequency: {self.meep_freq_min}")
            else:
                print(f"Minimum frequency must be >= 0 and < {self.meep_freq_max}")
        except ValueError:
            print(f"Invalid frequency: {text}")
    
    def update_freq_max(self, text):
        """Update maximum frequency for band diagram"""
        try:
            value = float(text)
            if value > self.meep_freq_min:
                self.meep_freq_max = value
                print(f"Maximum frequency: {self.meep_freq_max}")
            else:
                print(f"Maximum frequency must be > {self.meep_freq_min}")
        except ValueError:
            print(f"Invalid frequency: {text}")
    
    def calculate_band_structure(self, event):
        """Calculate photonic band structure using MEEP eigenmode solver"""
        if not self.meep_enabled:
            print("MEEP not available. Cannot calculate band structure.")
            return
        
        if self.meep_sim is None:
            print("No simulation setup. Run 'Setup Sim' first.")
            return
        
        print("\n" + "="*80)
        print("CALCULATING PHOTONIC BAND STRUCTURE")
        print("="*80)
        print(f"Number of bands: {self.meep_num_bands}")
        print(f"Number of k-points: {self.meep_k_points}")
        print(f"Frequency range: [{self.meep_freq_min}, {self.meep_freq_max}]")
        
        try:
            # Calculate center frequency and width for Harminv
            freq_center = (self.meep_freq_max + self.meep_freq_min) / 2
            freq_width = self.meep_freq_max - self.meep_freq_min
            
            # Source needs to be broader than Harminv range
            source_fwidth = freq_width * 1.2  # 20% wider
            
            print(f"Source center frequency: {freq_center:.3f}")
            print(f"Source bandwidth: {source_fwidth:.3f}")
            print(f"Harminv search range: [{self.meep_freq_min:.3f}, {self.meep_freq_max:.3f}]")
            
            # Define k-point path in reciprocal space
            # For 2D pentagon structure, we sample key symmetry points
            # Γ (0,0) → X (0.5,0) → M (0.5,0.5) → Γ (0,0)
            
            k_points = [
                mp.Vector3(0, 0, 0),          # Γ point
                mp.Vector3(0.5, 0, 0),        # X point
                mp.Vector3(0.5, 0.5, 0),      # M point
                mp.Vector3(0, 0, 0)           # Back to Γ
            ]
            
            # Interpolate k-points
            k_interp = mp.interpolate(self.meep_k_points, k_points)
            self.meep_k_path = k_interp
            
            print(f"K-point path: Γ → X → M → Γ ({len(k_interp)} points)")
            print("Running eigenmode solver...")
            print("Note: This may take 5-30 minutes depending on parameters.")
            
            # Use harminv to find resonant frequencies at each k-point
            freqs = []
            
            for k_idx, k in enumerate(k_interp):
                try:
                    # Reset simulation for this k-point
                    self.meep_sim.reset_meep()
                    
                    # Set Bloch-periodic boundary conditions
                    self.meep_sim.k_point = k
                    
                    # Add broadband Gaussian source at center
                    sources = [mp.Source(mp.GaussianSource(freq_center, fwidth=source_fwidth),
                                        component=mp.Hz,
                                        center=mp.Vector3(0, 0, 0))]
                    self.meep_sim.change_sources(sources)
                    
                    # Use harminv to find eigenmodes
                    # Harminv searches for resonances within [fcen-df/2, fcen+df/2]
                    harminv_instance = mp.Harminv(mp.Hz, mp.Vector3(0, 0, 0), 
                                                 freq_center,  # Center frequency
                                                 freq_width)   # Frequency range to search
                    
                    # Run simulation until source is finished, then continue for Harminv
                    runtime = max(self.meep_runtime, 200)  # At least 200 steps
                    self.meep_sim.run(mp.after_sources(harminv_instance), 
                                     until_after_sources=runtime)
                    
                    # Extract resonant frequencies
                    k_freqs = []
                    for mode in harminv_instance.modes:
                        f = mode.freq.real
                        # Filter: positive frequency within our search range
                        if self.meep_freq_min <= f <= self.meep_freq_max:
                            k_freqs.append(f)
                    
                    # Sort and take first num_bands
                    k_freqs.sort()
                    k_freqs = k_freqs[:self.meep_num_bands]
                    
                    # Pad with NaN if fewer modes found
                    while len(k_freqs) < self.meep_num_bands:
                        k_freqs.append(np.nan)
                    
                    freqs.append(k_freqs)
                    
                    if (k_idx + 1) % 5 == 0 or k_idx == 0:
                        print(f"  Progress: {k_idx + 1}/{len(k_interp)} k-points | "
                              f"Found {len([f for f in k_freqs if not np.isnan(f)])} modes at this k")
                
                except Exception as k_error:
                    print(f"  Warning: Error at k-point {k_idx}: {k_error}")
                    # Pad with NaN for failed k-point
                    freqs.append([np.nan] * self.meep_num_bands)
            
            # Store band structure data
            self.meep_band_data = {
                'frequencies': np.array(freqs),  # Shape: (num_k, num_bands)
                'k_points': k_interp,
                'k_labels': ['Γ', 'X', 'M', 'Γ'],
                'k_indices': [0, self.meep_k_points // 3, 2 * self.meep_k_points // 3, self.meep_k_points - 1]
            }
            
            # Calculate statistics
            freqs_array = np.array(freqs)
            valid_freqs = freqs_array[~np.isnan(freqs_array)]
            
            print(f"\n✓ Band structure calculation complete!")
            print(f"  Bands calculated: {self.meep_num_bands}")
            print(f"  K-points sampled: {len(k_interp)}")
            if len(valid_freqs) > 0:
                print(f"  Frequency range: [{np.nanmin(freqs):.4f}, {np.nanmax(freqs):.4f}]")
                print(f"  Valid frequency points: {len(valid_freqs)}/{freqs_array.size}")
            else:
                print(f"  WARNING: No valid frequencies found!")
                print(f"  Try adjusting frequency range or increasing runtime.")
            print("="*80 + "\n")
            
        except Exception as e:
            print(f"ERROR calculating band structure: {e}")
            import traceback
            traceback.print_exc()
    
    def show_band_structure(self, event):
        """Visualize photonic band structure diagram"""
        if self.meep_band_data is None:
            print("No band structure data. Run 'Calc Bands' first.")
            return
        
        print("\n" + "="*80)
        print("VISUALIZING BAND STRUCTURE")
        print("="*80)
        
        try:
            fig_bands = plt.figure(figsize=(10, 8))
            ax_bands = fig_bands.add_subplot(111)
            
            freqs = self.meep_band_data['frequencies']
            num_k = freqs.shape[0]
            k_indices = np.arange(num_k)
            
            # Plot each band
            cmap = plt.get_cmap('viridis')
            colors = cmap(np.linspace(0, 1, self.meep_num_bands))
            for band_idx in range(self.meep_num_bands):
                band_freqs = freqs[:, band_idx]
                ax_bands.plot(k_indices, band_freqs, 'o-', 
                            color=colors[band_idx], 
                            linewidth=2, markersize=3,
                            label=f'Band {band_idx + 1}')
            
            # Add vertical lines at high-symmetry points
            k_labels = self.meep_band_data['k_labels']
            k_label_indices = self.meep_band_data['k_indices']
            
            for k_idx in k_label_indices[1:-1]:  # Skip first and last
                ax_bands.axvline(k_idx, color='gray', linestyle='--', alpha=0.5, linewidth=1)
            
            # Set x-axis labels
            ax_bands.set_xticks(k_label_indices)
            ax_bands.set_xticklabels(k_labels)
            
            ax_bands.set_xlabel('Wave Vector', fontsize=14, fontweight='bold')
            ax_bands.set_ylabel('Frequency (c/a)', fontsize=14, fontweight='bold')
            ax_bands.set_title(f'Photonic Band Structure - Pentagon 2D Structure\n'
                             f'{self.meep_num_bands} bands, Resolution={self.meep_resolution}',
                             fontsize=14, fontweight='bold')
            ax_bands.grid(True, alpha=0.3)
            ax_bands.legend(loc='best', fontsize=9)
            
            # Add band gap analysis
            print("\nBAND GAP ANALYSIS:")
            print("-" * 80)
            for band_idx in range(self.meep_num_bands - 1):
                upper_band = freqs[:, band_idx + 1]
                lower_band = freqs[:, band_idx]
                
                # Find minimum of upper band and maximum of lower band
                upper_min = np.nanmin(upper_band)
                lower_max = np.nanmax(lower_band)
                
                if upper_min > lower_max:
                    gap_size = upper_min - lower_max
                    gap_center = (upper_min + lower_max) / 2
                    gap_ratio = gap_size / gap_center * 100
                    
                    print(f"Band gap between bands {band_idx + 1} and {band_idx + 2}:")
                    print(f"  Gap: [{lower_max:.4f}, {upper_min:.4f}]")
                    print(f"  Size: {gap_size:.4f} (Δf/f_center = {gap_ratio:.2f}%)")
                    
                    # Highlight gap on plot
                    ax_bands.axhspan(lower_max, upper_min, alpha=0.2, color='red', 
                                   label=f'Gap {band_idx + 1}-{band_idx + 2}')
            
            plt.tight_layout()
            plt.show()
            
            print("\n" + "="*80)
            print("Band structure visualization complete!")
            print("="*80 + "\n")
            
        except Exception as e:
            print(f"ERROR showing band structure: {e}")
            import traceback
            traceback.print_exc()
    
    def analyze_hz_modes(self, event):
        """Analyze Hz field modes and spatial distribution"""
        if self.meep_field_data is None:
            print("No field data available. Run 'Run Sim' first.")
            return
        
        if 'Hz' not in self.meep_field_data or self.meep_field_data['Hz'] is None:
            print("Hz field not computed. Enable Hz in field selection.")
            return
        
        print("\n" + "="*80)
        print("Hz FIELD MODE ANALYSIS")
        print("="*80)
        
        try:
            hz_field = self.meep_field_data['Hz']
            
            # Compute field statistics
            hz_mean = np.mean(hz_field)
            hz_std = np.std(hz_field)
            hz_max = np.max(np.abs(hz_field))
            hz_energy = np.sum(np.abs(hz_field)**2)
            
            print(f"Field Statistics:")
            print(f"  Mean: {hz_mean:.4e}")
            print(f"  Std Dev: {hz_std:.4e}")
            print(f"  Max |Hz|: {hz_max:.4e}")
            print(f"  Total Energy: {hz_energy:.4e}")
            
            # Perform 2D FFT to analyze spatial frequencies
            hz_fft = np.fft.fft2(hz_field)
            hz_fft_shifted = np.fft.fftshift(hz_fft)
            hz_power_spectrum = np.abs(hz_fft_shifted)**2
            
            # Create comprehensive visualization
            fig_modes = plt.figure(figsize=(16, 10))
            
            # 1. Real part of Hz field
            ax1 = fig_modes.add_subplot(2, 3, 1)
            im1 = ax1.imshow(np.transpose(hz_field.real), cmap='RdBu', origin='lower')
            ax1.set_title('Hz Field - Real Part', fontsize=12, fontweight='bold')
            ax1.set_xlabel('x')
            ax1.set_ylabel('y')
            plt.colorbar(im1, ax=ax1)
            
            # 2. Imaginary part
            ax2 = fig_modes.add_subplot(2, 3, 2)
            im2 = ax2.imshow(np.transpose(hz_field.imag), cmap='RdBu', origin='lower')
            ax2.set_title('Hz Field - Imaginary Part', fontsize=12, fontweight='bold')
            ax2.set_xlabel('x')
            ax2.set_ylabel('y')
            plt.colorbar(im2, ax=ax2)
            
            # 3. Magnitude
            ax3 = fig_modes.add_subplot(2, 3, 3)
            im3 = ax3.imshow(np.transpose(np.abs(hz_field)), cmap='hot', origin='lower')
            ax3.set_title('Hz Field - Magnitude', fontsize=12, fontweight='bold')
            ax3.set_xlabel('x')
            ax3.set_ylabel('y')
            plt.colorbar(im3, ax=ax3)
            
            # 4. Power spectrum (log scale)
            ax4 = fig_modes.add_subplot(2, 3, 4)
            im4 = ax4.imshow(np.transpose(np.log10(hz_power_spectrum + 1e-10)), cmap='viridis', origin='lower')
            ax4.set_title('Power Spectrum (log scale)', fontsize=12, fontweight='bold')
            ax4.set_xlabel('k_x')
            ax4.set_ylabel('k_y')
            plt.colorbar(im4, ax=ax4, label='log10(Power)')
            
            # 5. Cross-section through center
            ax5 = fig_modes.add_subplot(2, 3, 5)
            center_y = hz_field.shape[0] // 2
            center_x = hz_field.shape[1] // 2
            ax5.plot(hz_field[center_y, :].real, 'b-', label='Real (horizontal)')
            ax5.plot(hz_field[:, center_x].real, 'r-', label='Real (vertical)')
            ax5.set_title('Field Cross-Sections', fontsize=12, fontweight='bold')
            ax5.set_xlabel('Position')
            ax5.set_ylabel('Hz (real)')
            ax5.legend()
            ax5.grid(True, alpha=0.3)
            
            # 6. Field energy distribution
            ax6 = fig_modes.add_subplot(2, 3, 6)
            im6 = ax6.imshow(np.transpose(np.abs(hz_field)**2), cmap='plasma', origin='lower')
            ax6.set_title('Energy Density |Hz|²', fontsize=12, fontweight='bold')
            ax6.set_xlabel('x')
            ax6.set_ylabel('y')
            plt.colorbar(im6, ax=ax6)
            
            plt.tight_layout()
            plt.show()
            
            # Identify hot spots (high field concentration)
            energy_density = np.abs(hz_field)**2
            threshold = np.percentile(energy_density, 95)  # Top 5%
            hotspots = np.where(energy_density > threshold)
            
            print(f"\nHot Spots (top 5% energy density):")
            print(f"  Number of points: {len(hotspots[0])}")
            print(f"  Threshold: {threshold:.4e}")
            print(f"  Max energy density: {np.max(energy_density):.4e}")
            
            print("\n" + "="*80)
            print("Hz mode analysis complete!")
            print("="*80 + "\n")
            
        except Exception as e:
            print(f"ERROR analyzing Hz modes: {e}")
            import traceback
            traceback.print_exc()
    
    def export_band_structure(self, event):
        """Export band structure data to files"""
        if self.meep_band_data is None:
            print("No band structure data. Run 'Calc Bands' first.")
            return
        
        print("\n" + "="*80)
        print("EXPORT BAND STRUCTURE DATA")
        print("="*80)
        
        try:
            import tkinter as tk
            from tkinter import filedialog
            
            root = tk.Tk()
            root.withdraw()
            save_dir = filedialog.askdirectory(title="Select directory to save band structure")
            root.destroy()
            
            if not save_dir:
                print("Export cancelled")
                return
            
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Save frequency data
            freq_file = f"{save_dir}/band_frequencies_{timestamp}.npy"
            np.save(freq_file, self.meep_band_data['frequencies'])
            print(f"✓ Saved frequencies: {freq_file}")
            
            # Save k-point data
            k_file = f"{save_dir}/band_kpoints_{timestamp}.npy"
            k_array = np.array([[k.x, k.y, k.z] for k in self.meep_band_data['k_points']])
            np.save(k_file, k_array)
            print(f"✓ Saved k-points: {k_file}")
            
            # Save metadata and analysis
            meta_file = f"{save_dir}/band_metadata_{timestamp}.txt"
            with open(meta_file, 'w') as f:
                f.write("PHOTONIC BAND STRUCTURE DATA\n")
                f.write("="*80 + "\n\n")
                f.write(f"Timestamp: {timestamp}\n")
                f.write(f"Number of bands: {self.meep_num_bands}\n")
                f.write(f"Number of k-points: {self.meep_k_points}\n")
                f.write(f"K-path: {' → '.join(self.meep_band_data['k_labels'])}\n")
                f.write(f"Frequency range: [{self.meep_freq_min}, {self.meep_freq_max}]\n")
                f.write(f"Resolution: {self.meep_resolution}\n")
                f.write(f"Structure: Pentagon 2D (angle={self.target_angle}°)\n\n")
                
                # Band gap analysis
                freqs = self.meep_band_data['frequencies']
                f.write("BAND GAP ANALYSIS:\n")
                f.write("-" * 80 + "\n")
                for band_idx in range(self.meep_num_bands - 1):
                    upper_band = freqs[:, band_idx + 1]
                    lower_band = freqs[:, band_idx]
                    upper_min = np.nanmin(upper_band)
                    lower_max = np.nanmax(lower_band)
                    
                    if upper_min > lower_max:
                        gap_size = upper_min - lower_max
                        gap_center = (upper_min + lower_max) / 2
                        gap_ratio = gap_size / gap_center * 100
                        f.write(f"\nBand gap {band_idx + 1}-{band_idx + 2}:\n")
                        f.write(f"  Range: [{lower_max:.6f}, {upper_min:.6f}]\n")
                        f.write(f"  Size: {gap_size:.6f}\n")
                        f.write(f"  Ratio: {gap_ratio:.2f}%\n")
            
            print(f"✓ Saved metadata: {meta_file}")
            print("="*80 + "\n")
            
        except Exception as e:
            print(f"ERROR exporting band structure: {e}")
    
    def on_click(self, event):
        """Handle mouse click for selection"""
        if event.inaxes != self.ax_main:
            return
        
        click_pos = np.array([event.xdata, event.ydata])
        
        # Find nearest corner or edge
        min_dist = float('inf')
        selected = None
        
        for petal_idx in range(5):
            if petal_idx not in self.petal_corners_cache:
                continue
            
            corners = self.petal_corners_cache[petal_idx]
            
            # Check corners
            for corner_idx, corner_pos in enumerate(corners):
                dist = np.linalg.norm(click_pos - corner_pos)
                if dist < min_dist and dist < 100:  # 100 nm threshold
                    min_dist = dist
                    selected = (petal_idx, 'corner', corner_idx, corner_pos)
            
            # Check edges (midpoints)
            for edge_idx in range(len(corners)):
                p1 = corners[edge_idx]
                p2 = corners[(edge_idx + 1) % len(corners)]
                edge_mid = (p1 + p2) / 2
                dist = np.linalg.norm(click_pos - edge_mid)
                if dist < min_dist and dist < 100:
                    min_dist = dist
                    selected = (petal_idx, 'edge', edge_idx, edge_mid)
        
        if selected:
            self.selected_petal, self.selected_type, self.selected_index, pos = selected
            self.dragging = True
            self.drag_start = click_pos
            self.update_plot()
    
    def on_motion(self, event):
        """Handle mouse motion for dragging"""
        if not self.dragging or event.inaxes != self.ax_main:
            return
        
        if self.selected_type == 'corner' and self.selected_petal is not None:
            current_pos = np.array([event.xdata, event.ydata])
            delta = current_pos - self.drag_start
            
            # Transform delta to be relative to the selected petal's local coordinate system
            # First, rotate delta back to the reference frame (undo the petal rotation)
            petal_angle = self.selected_petal * 72.0
            angle_rad = -np.deg2rad(petal_angle)  # Negative to undo rotation
            cos_a, sin_a = np.cos(angle_rad), np.sin(angle_rad)
            rot_matrix_inv = np.array([[cos_a, -sin_a], [sin_a, cos_a]])
            
            # Delta in local coordinates (relative to unrotated petal center)
            delta_local = rot_matrix_inv @ delta
            
            # Apply to ALL petals with same corner index (stored in local coordinates)
            current_offset = self.corner_offsets.get(self.selected_index, np.array([0.0, 0.0]))
            new_offset = current_offset + delta_local
            
            self.corner_offsets[self.selected_index] = new_offset
            self.drag_start = current_pos
            self.update_plot()
    
    def on_release(self, event):
        """Handle mouse release"""
        self.dragging = False
    
    def on_key_press(self, event):
        """Handle keyboard input for fine adjustments"""
        if self.selected_petal is None or self.selected_type != 'corner':
            return
        
        # Map arrow keys to movement
        delta_local = np.array([0.0, 0.0])
        
        if event.key == 'left':
            delta_local[0] = -self.arrow_step
        elif event.key == 'right':
            delta_local[0] = self.arrow_step
        elif event.key == 'up':
            delta_local[1] = self.arrow_step
        elif event.key == 'down':
            delta_local[1] = -self.arrow_step
        elif event.key == 'shift+left':
            delta_local[0] = -self.arrow_step * 0.2  # Fine adjustment
        elif event.key == 'shift+right':
            delta_local[0] = self.arrow_step * 0.2
        elif event.key == 'shift+up':
            delta_local[1] = self.arrow_step * 0.2
        elif event.key == 'shift+down':
            delta_local[1] = -self.arrow_step * 0.2
        else:
            return
        
        # Apply offset in local coordinates
        current_offset = self.corner_offsets.get(self.selected_index, np.array([0.0, 0.0]))
        new_offset = current_offset + delta_local
        self.corner_offsets[self.selected_index] = new_offset
        self.update_plot()
    
    def update_profile(self, label):
        """Update decay profile selection"""
        self.current_profile = label.lower()
        self.update_plot()
    
    def update_petal_scale(self, idx, val):
        """Update individual petal scale (now fixed at 1.0)"""
        self.petal_scales[idx] = 1.0
        self.update_plot()
    
    def reset(self, event):
        """Reset all parameters to defaults"""
        self.current_profile = 'exponential'
        self.radio.set_active(0)
        self.target_angle = 72.0
        self.textbox_angle.set_val(str(self.target_angle))
        self.decay_rate = 1.0
        self.textbox_decay.set_val(str(self.decay_rate))
        self.global_scale = 1.0
        self.textbox_gscale.set_val(str(self.global_scale))
        self.slider_atom_size.reset()
        self.petal_scales = [1.0, 1.0, 1.0, 1.0, 1.0]
        self.corner_offsets = {}
        self.edge_scales = {}
        self.custom_basis_positions = None
        self.loaded_atoms = None
        self.reset_basis_positions(None)
        self.clear_selection()
        self.update_plot()
    
    def create_single_petal(self):
        """Create one deformed petal with current parameters and apply fabric-like corner deformations"""
        # First create base deformed lattice
        # Scale custom basis if provided
        scaled_custom_basis = None
        if self.custom_basis_positions is not None:
            scaled_custom_basis = self.custom_basis_positions * self.global_scale
        
        atoms_base, corners_list_base, factors, _ = create_lattice_with_correct_atom_positions(
            self.n_cells, self.n_cells,
            self.sq_a1 * self.global_scale,
            self.sq_a2 * self.global_scale,
            self.basis,
            target_angle_deg=self.target_angle,
            stretch_corner='bottom_left',
            decay_profile=self.current_profile,
            custom_equation=self.custom_decay_equation if self.current_profile == 'custom' else None,
            custom_basis=scaled_custom_basis
        )
        
        # Apply fabric-like deformation if there are corner offsets
        if self.corner_offsets:
            # Get unique corners from cells
            all_corners = []
            for cell_corners in corners_list_base:
                for corner in cell_corners:
                    all_corners.append(corner)
            
            # Find unique corners
            unique_corners = []
            tolerance = 10.0
            for corner in all_corners:
                is_unique = True
                for uc in unique_corners:
                    if np.linalg.norm(corner - uc) < tolerance:
                        is_unique = False
                        break
                if is_unique:
                    unique_corners.append(corner.copy())
            
            # Apply corner offsets and compute fabric deformation
            # For each corner offset, compute deformation field
            deformation_field = {}
            
            for corner_idx, offset_local in self.corner_offsets.items():
                if corner_idx >= len(unique_corners):
                    continue
                
                moved_corner = unique_corners[corner_idx]
                
                # Calculate deformation influence on all corners
                for i, corner in enumerate(unique_corners):
                    dist = np.linalg.norm(corner - moved_corner)
                    max_dist = np.max([np.linalg.norm(uc - moved_corner) for uc in unique_corners])
                    
                    # Fabric-like falloff: closer corners move more
                    if max_dist > 0:
                        influence = np.exp(-2.0 * dist / max_dist)  # Exponential falloff
                    else:
                        influence = 1.0 if i == corner_idx else 0.0
                    
                    if i not in deformation_field:
                        deformation_field[i] = np.array([0.0, 0.0])
                    deformation_field[i] += offset_local * influence
            
            # Apply deformation field to all cell corners
            corners_list_deformed = []
            for cell_corners in corners_list_base:
                deformed_corners = []
                for corner in cell_corners:
                    # Find which unique corner this matches and apply its deformation
                    corner_offset = np.array([0.0, 0.0])
                    for uc_idx, uc in enumerate(unique_corners):
                        if np.linalg.norm(corner - uc) < tolerance:
                            if uc_idx in deformation_field:
                                corner_offset = deformation_field[uc_idx]
                            break
                    deformed_corners.append(corner + corner_offset)
                corners_list_deformed.append(np.array(deformed_corners))
            
            # Recalculate atom positions based on deformed cells
            a_mag = np.linalg.norm(self.sq_a1 * self.global_scale)
            
            # Use scaled custom basis if provided, otherwise use default basis scaled by global_scale
            if scaled_custom_basis is not None:
                basis_to_use = scaled_custom_basis
            else:
                basis_to_use = self.basis * self.global_scale
            
            basis_frac = basis_to_use / a_mag
            
            atoms_deformed = []
            for cell_corners in corners_list_deformed:
                v00 = cell_corners[0]  # bottom-left
                v10 = cell_corners[1]  # bottom-right
                v01 = cell_corners[3]  # top-left
                
                a1_cell = v10 - v00
                a2_cell = v01 - v00
                
                # Place atoms at fractional positions
                for atom_frac in basis_frac:
                    fx = atom_frac[0] + 0.5
                    fy = atom_frac[1] + 0.5
                    atom_pos = v00 + fx * a1_cell + fy * a2_cell
                    atoms_deformed.append(atom_pos)
            
            return np.array(atoms_deformed), corners_list_deformed
        
        return atoms_base, corners_list_base

    
    def update_plot(self):
        """Redraw the pentagon with current parameters"""
        self.ax_main.clear()
        self.petal_corners_cache = {}
        
        # Create and rotate 5 petals
        colors = ['red', 'blue', 'green', 'orange', 'purple']
        
        for i in range(5):
            angle = i * 72.0
            rot_rad = np.deg2rad(angle)
            cos_a, sin_a = np.cos(rot_rad), np.sin(rot_rad)
            rot_matrix = np.array([[cos_a, -sin_a], [sin_a, cos_a]])
            
            # Create petal (already includes fabric deformation)
            atoms, corners_list = self.create_single_petal()
            if self.loaded_atoms is not None:
                atoms = np.array(self.loaded_atoms)
            
            # Apply individual petal scale
            petal_scale = self.petal_scales[i]
            atoms_scaled = atoms * petal_scale
            corners_scaled = [corners * petal_scale for corners in corners_list]
            
            # Rotate entire petal (this applies the relative transformations)
            atoms_rot = (rot_matrix @ atoms_scaled.T).T
            corners_rot = [(rot_matrix @ corners.T).T for corners in corners_scaled]
            
            # Get unique corners for this petal (for selection)
            all_corners_flat = []
            for cell_corners in corners_rot:
                for corner in cell_corners:
                    all_corners_flat.append(corner)
            
            unique_corners = []
            tolerance = 10.0
            for corner in all_corners_flat:
                is_unique = True
                for uc in unique_corners:
                    if np.linalg.norm(corner - uc) < tolerance:
                        is_unique = False
                        break
                if is_unique:
                    unique_corners.append(corner.copy())
            
            self.petal_corners_cache[i] = unique_corners
            
            # Plot cells
            for cell_corners in corners_rot:
                poly = Polygon(cell_corners, fill=False, edgecolor=colors[i], 
                             linewidth=1.5, alpha=0.7)
                self.ax_main.add_patch(poly)
            
            # Plot atoms
            self.ax_main.scatter(atoms_rot[:, 0], atoms_rot[:, 1], 
                               c=colors[i], s=self.atom_size, alpha=0.6, edgecolors='black',
                               linewidths=0.5)
            
            # Draw corner markers (visible only if show_selection is True)
            if self.show_selection:
                for corner_idx, corner in enumerate(unique_corners):
                    self.ax_main.plot(corner[0], corner[1], 'o',
                                    color=colors[i], markersize=8,
                                    markeredgecolor='white', markeredgewidth=1.5,
                                    alpha=0.7, zorder=15)
            
            # Highlight selected corner/edge on THIS petal
            if self.selected_petal == i:
                if self.selected_type == 'corner' and self.selected_index is not None and self.selected_index < len(unique_corners):
                    corner_pos = unique_corners[self.selected_index]
                    
                    self.ax_main.plot(corner_pos[0], corner_pos[1], 'y*', 
                                    markersize=20, markeredgecolor='black', 
                                    markeredgewidth=2, zorder=20)
                    self.ax_main.text(corner_pos[0], corner_pos[1] + 150, 
                                    f'C{self.selected_index} (All Petals)',
                                    ha='center', fontsize=10, fontweight='bold',
                                    bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.8))
                
                elif self.selected_type == 'edge' and self.selected_index is not None and self.selected_index < len(unique_corners):
                    p1 = unique_corners[self.selected_index]
                    p2 = unique_corners[(self.selected_index + 1) % len(unique_corners)]
                    edge_mid = (p1 + p2) / 2
                    self.ax_main.plot(edge_mid[0], edge_mid[1], 'ys', 
                                    markersize=15, markeredgecolor='black',
                                    markeredgewidth=2, zorder=20)
                    self.ax_main.text(edge_mid[0], edge_mid[1] + 150,
                                    f'E{self.selected_index}',
                                    ha='center', fontsize=10, fontweight='bold',
                                    bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.8))
        
        self.ax_main.set_aspect('equal')
        self.ax_main.grid(True, alpha=0.3)
        self.ax_main.set_xlabel('x (nm)', fontsize=12)
        self.ax_main.set_ylabel('y (nm)', fontsize=12)
        
        selection_text = ''
        if self.selected_petal is not None and self.selected_type is not None and self.selected_index is not None:
            selection_text = f' | Selected: {self.selected_type.upper()[0]}{self.selected_index} (affects ALL petals)'
        
        title_text = f'Interactive Pentagon Structure - Drag Any Corner{selection_text}\n'
        title_text += f'Profile: {self.current_profile} | Angle: {self.target_angle}° | '
        title_text += f'Decay: {self.decay_rate:.1f}× | Scale: {self.global_scale:.2f}×'
        
        # Add matrix info to title if display is enabled
        if self.show_matrix_in_gui:
            title_text += '\n[TRANSFORMATION MATRIX DISPLAY ENABLED]'
        
        self.ax_main.set_title(title_text, fontsize=13, fontweight='bold')
        
        # Display transformation matrix in GUI if enabled
        if self.show_matrix_in_gui:
            # Calculate transformation matrix
            basis_to_use = self.custom_basis_positions if self.custom_basis_positions is not None else self.basis
            
            # Get base lattice (one petal)
            if self.loaded_atoms is not None:
                atoms_base = np.array(self.loaded_atoms)
            else:
                atoms_base, _, _, _ = create_lattice_with_correct_atom_positions(
                    self.n_cells, self.n_cells,
                    self.sq_a1 * self.global_scale,
                    self.sq_a2 * self.global_scale,
                    basis_to_use,
                    target_angle_deg=self.target_angle,
                    stretch_corner='bottom_left',
                    decay_profile=self.current_profile,
                    custom_equation=self.custom_decay_equation if self.current_profile == 'custom' else None,
                    custom_basis=self.custom_basis_positions
                )
            
            # Original square lattice
            a_mag = np.linalg.norm(self.sq_a1 * self.global_scale)
            basis_frac = basis_to_use / a_mag
            
            atoms_original = []
            for i in range(self.n_cells):
                for j in range(self.n_cells):
                    cell_center = np.array([
                        (i - self.n_cells//2) * a_mag,
                        (j - self.n_cells//2) * a_mag
                    ])
                    for bf in basis_frac:
                        atom_pos = cell_center + bf * a_mag
                        atoms_original.append(atom_pos)
            
            atoms_original = np.array(atoms_original)
            
            # Create 36×36 matrices
            max_atoms = 36
            matrix_initial = np.zeros((36, 36))
            matrix_final = np.zeros((36, 36))
            
            num_atoms = min(len(atoms_original), max_atoms // 2)
            
            for atom_idx in range(num_atoms):
                x_col = atom_idx * 2
                y_col = atom_idx * 2 + 1
                
                if atom_idx < len(atoms_original):
                    matrix_initial[atom_idx, x_col] = atoms_original[atom_idx, 0]
                    matrix_initial[atom_idx, y_col] = atoms_original[atom_idx, 1]
                    
                    matrix_final[atom_idx, x_col] = atoms_base[atom_idx, 0]
                    matrix_final[atom_idx, y_col] = atoms_base[atom_idx, 1]
            
            matrix_transformation = matrix_final - matrix_initial
            
            # Display matrix in text area within the plot
            matrix_text = "TRANSFORMATION MATRIX (36×36):\n"
            matrix_text += "-" * 80 + "\n"
            
            # Show only non-zero rows
            non_zero_rows = []
            for i in range(num_atoms):
                if np.any(matrix_transformation[i] != 0):
                    non_zero_rows.append(i)
            
            if len(non_zero_rows) <= 10:
                # Show full matrix if small
                np.set_printoptions(precision=1, suppress=True, linewidth=150, threshold=1000)
                matrix_str = str(matrix_transformation[:num_atoms, :])
                for line in matrix_str.split('\n'):
                    if len(matrix_text) + len(line) < 3000:  # Limit text length
                        matrix_text += line + "\n"
            else:
                # Show summary for large matrices
                matrix_text += f"Matrix shape: {matrix_transformation.shape}\n"
                matrix_text += f"Non-zero elements: {np.count_nonzero(matrix_transformation)}\n"
                matrix_text += f"Max displacement: {np.max(np.abs(matrix_transformation)):.2f} nm\n"
                matrix_text += f"Mean displacement: {np.mean(np.abs(matrix_transformation[matrix_transformation != 0])):.2f} nm\n"
                matrix_text += "\nFirst 5 atoms:\n"
                for i in range(min(5, num_atoms)):
                    row_str = "[" + " ".join([f"{matrix_transformation[i, j]:7.1f}" for j in range(min(10, 36))]) + "]"
                    matrix_text += f"Row {i}: {row_str}\n"
            
            # Add text box to plot
            self.ax_main.text(0.02, 0.98, matrix_text, transform=self.ax_main.transAxes,
                            fontsize=8, verticalalignment='top', family='monospace',
                            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
        
        # Set reasonable limits
        max_extent = self.n_cells * a_nm * 1.5 * self.global_scale * max(self.petal_scales) + 300
        self.ax_main.set_xlim(-max_extent, max_extent)
        self.ax_main.set_ylim(-max_extent, max_extent)
        
        self.fig.canvas.draw_idle()


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Launch the interactive GUI"""
    print("="*70)
    print("INTERACTIVE GUI - Manual Pentagon Structure Adjustment")
    print("="*70)
    print("\nControls:")
    print("  • Radio buttons: Select decay profile (Exponential/Gaussian/Polynomial/Custom)")
    print("  • Angle text box: Enter target angle (any float value)")
    print("  • Custom Eq: Enter decay equation using 'x' (e.g., exp(-3*x), 1-x**2)")
    print("  • Decay Rate: Control decay strength (0.1-3.0×)")
    print("  • Global Scale: Scale entire structure (0.5-2.0×)")
    print("  • Atom Size: Adjust atom marker diameter (10-200 px)")
    print("  • Atom Site Positions: Enter X,Y coordinates (nm) for each of 4 atoms")
    print("  • Reset Basis: Return atom positions to default")
    print("  • Selection ON/OFF: Toggle visibility of corner markers")
    print("  • Get Transformation Matrix: Export atom positions and transformations")
    print("  • Export: Save matrices to .npy files")
    print("  • Load Initial/Transform/Final: Load saved matrices from files")
    print("  • Save Plot: Save current configuration to .pkl file")
    print("  • Load Plot: Restore previously saved configuration")
    print("  • Matrix Display: Toggle transformation matrix display in GUI")
    print("  • Reset All: Return to defaults")
    print("\n" + "="*70)
    print("SAVE/LOAD PLOT DATA:")
    print("="*70)
    print("  • Save Plot: Saves all parameters (angle, profile, decay, scale, etc.)")
    print("  • Save also includes: custom basis positions, atom transformations, corner offsets")
    print("  • Load Plot: Restores exact previous state including all GUI controls")
    print("  • Useful for: Saving manual adjustments to reopen later")
    print("\n" + "="*70)
    print("TRANSFORMATION MATRIX DISPLAY:")
    print("="*70)
    print("  • Matrix: OFF button toggles display ON/OFF")
    print("  • When enabled: Shows 36×36 transformation matrix in GUI area")
    print("  • Displays displacement field for all atoms")
    print("  • Updates dynamically as you adjust parameters")
    print("\n" + "="*70)
    print("MEEP ELECTROMAGNETIC SIMULATION:")
    print("="*70)
    if MEEP_AVAILABLE:
        print("  • Setup Sim: Convert structure to MEEP geometry (cylinders at atoms)")
        print("  • Run Sim: Execute electromagnetic simulation (Hz, Ex, Ey fields)")
        print("  • Show Hz/Ex/Ey: Visualize field components")
        print("  • Clear Sim: Reset simulation data")
        print("  • Export Fields: Save field data to .npy files")
        print("  • Freq/λ: Set source frequency and wavelength")
        print("  • Res: Simulation resolution (pixels per unit)")
        print("  • R(nm): Cylinder radius for atoms")
        print("  • ε: Dielectric constant for atom material")
        print("  • Time: Simulation runtime (time steps)")
        print("  • Hz/Ex/Ey checkboxes: Select fields to compute and visualize")
        print("  • Workflow: Setup Sim → Run Sim → Show Fields")
        print("\n  BAND STRUCTURE ANALYSIS:")
        print("  • Bands: Number of photonic bands to calculate (1-20)")
        print("  • K-pts: Number of k-points along Γ→X→M→Γ path (5-100)")
        print("  • f_min/f_max: Frequency range for band diagram")
        print("  • Calc Bands: Calculate photonic band structure using eigenmodes")
        print("  • Show Bands: Visualize band diagram with gap analysis")
        print("  • Hz Modes: Detailed Hz field analysis (2D FFT, energy, hotspots)")
        print("  • Export Bands: Save band structure data to .npy files")
        print("  • Band Gap Detection: Automatic identification of photonic band gaps")
        print("  • Workflow: Setup Sim → Calc Bands → Show Bands → Export Bands")
    else:
        print("  ✗ MEEP NOT AVAILABLE - Install: pip install meep")
    print("\n" + "="*70)
    print("INTERACTIVE CORNER MANIPULATION:")
    print("="*70)
    print("  • Click any corner to select it")
    print("  • Drag with mouse OR use arrow keys to move")
    print("  • Arrow keys: move 5nm per step")
    print("  • Shift+Arrow: fine adjustment (1nm per step)")
    print("  • Changes apply RELATIVELY to ALL 5 petals")
    print("  • Lattice deforms like fabric (smooth propagation)")
    print("  • Atoms move with cell deformation")
    print("  • Corners shown as colored dots (always visible)")
    print("  • Selected corner highlighted with yellow star")
    print("="*70)
    
    gui = PentagonGUI(n_cells=3, sq_a1=sq_a1, sq_a2=sq_a2, basis=basis_sites_square)
    plt.show()


if __name__ == '__main__':
    main()
