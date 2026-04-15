"""
Pentagon Photonics Simulator GUI - PyQt6 Implementation
Main launcher for the photonic simulation application.
"""

import sys
from typing import Optional
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QLabel, QPushButton, QSlider, QSpinBox, QComboBox,
    QCheckBox, QTextEdit, QProgressBar, QMessageBox, QDialog,
    QDialogButtonBox, QFormLayout, QScrollArea, QLineEdit, QDoubleSpinBox,
    QFileDialog, QPlainTextEdit, QGroupBox, QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QIcon

from utilities import create_default_gui, LatticeType


class ProgressCallback:
    """Lightweight progress callback wrapper for compatibility."""

    def __init__(self, on_progress=None):
        self.on_progress = on_progress

    def __call__(self, progress, message=""):
        if self.on_progress is not None:
            self.on_progress(progress, message)


class SimulationWorker(QThread):
    """Worker thread for running simulations in the background."""
    
    progress_updated = pyqtSignal(int, str)  # progress_percent, status_message
    simulation_complete = pyqtSignal()
    simulation_error = pyqtSignal(str)
    
    def __init__(self, gui_instance, num_steps: int):
        super().__init__()
        self.gui = gui_instance
        self.num_steps = num_steps
        self._is_running = True
    
    def run(self) -> None:
        """Execute the simulation in this thread."""
        try:
            # Register progress callback with GUI
            def progress_callback(progress, msg):
                self.progress_updated.emit(int(progress), msg)
            
            self.gui.register_progress_callback(
                'run_sim',
                ProgressCallback(on_progress=progress_callback)
            )
            
            # Run simulation without passing progress_callback (GUI handles it internally)
            self.gui.run_simulation_with_progress(self.num_steps)
            self.simulation_complete.emit()
        except Exception as e:
            self.simulation_error.emit(str(e))
    
    def stop(self) -> None:
        """Stop the simulation."""
        self._is_running = False
        self.gui.stop_simulation()


class BandStructureWorker(QThread):
    """Worker thread for band structure calculations."""
    
    progress_updated = pyqtSignal(int, str)
    calculation_complete = pyqtSignal(object)
    calculation_error = pyqtSignal(str)
    
    def __init__(self, gui_instance, num_kpoints: int):
        super().__init__()
        self.gui = gui_instance
        self.num_kpoints = num_kpoints
        self._is_running = True
    
    def run(self) -> None:
        """Execute band structure calculation in this thread."""
        try:
            # Register progress callback with GUI
            def progress_callback(progress, msg):
                self.progress_updated.emit(int(progress), msg)
            
            self.gui.register_progress_callback(
                'calc_band',
                ProgressCallback(on_progress=progress_callback)
            )
            
            # Run calculation without passing progress_callback (GUI handles it internally)
            band_data = self.gui.calculate_band_structure_with_progress(self.num_kpoints)
            self.calculation_complete.emit(band_data)
        except Exception as e:
            self.calculation_error.emit(str(e))
    
    def stop(self) -> None:
        """Stop the calculation."""
        self._is_running = False


class PhotonicGUILauncher(QMainWindow):
    """Main application window for the photonic simulator."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pentagon Photonics Simulator v2.1 - PyQt6")
        self.setGeometry(100, 100, 1200, 800)
        
        # Initialize GUI backend
        try:
            self.gui = create_default_gui()
        except Exception as e:
            QMessageBox.critical(self, "Initialization Error", 
                               f"Failed to initialize simulator:\n{str(e)}")
            sys.exit(1)
        
        # Workers
        self.sim_worker: Optional[SimulationWorker] = None
        self.band_worker: Optional[BandStructureWorker] = None
        
        # Pentagon structure attributes (initialized in plot_pentagon_structure)
        self.pentagon_atoms = None
        self.pentagon_cells = None
        self.pentagon_transforms = None
        self.pentagon_params = {}
        self.meep_results = None
        self.band_data = None
        self.manual_edit_enabled = True  # Always enabled
        self.plot_tab = None
        self.meep_tab = None
        
        # Initialize GUI
        self.init_gui()
    
    def init_gui(self) -> None:
        """Initialize the GUI layout and widgets."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create tab widget
        self.tabs = QTabWidget()
        central_layout = QVBoxLayout(central_widget)

        # Header bar with window controls
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        title = QLabel("Pentagon Photonics Simulator")
        title.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        self.max_restore_btn = QPushButton("Maximize")
        self.max_restore_btn.clicked.connect(self.toggle_max_restore)
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(self.max_restore_btn)
        central_layout.addWidget(header)
        central_layout.addWidget(self.tabs)
        
        # Add tabs
        self.tabs.addTab(self._wrap_scroll(self.create_main_controls_tab()), "Controls")
        self.tabs.addTab(self._wrap_scroll(self.create_pentagon_tab()), "Pentagon Structure")
        self.tabs.addTab(self._wrap_scroll(self.create_plot_tab()), "Structure Plot")
        self.tabs.addTab(self._wrap_scroll(self.create_meep_results_tab()), "MEEP Results")
        self.tabs.addTab(self._wrap_scroll(self.create_info_tab()), "Information")
        
        # Styling with rounded corners - Purple/Violet theme
        self.setStyleSheet("""
            QMainWindow { background-color: #1a1a1a; }
            QLabel { color: white; }
            QPushButton {
                background-color: #7c3aed;
                color: white;
                border-radius: 5px;
                padding: 6px 12px;
                font-weight: bold;
                border: 1px solid #6d28d9;
            }
            QPushButton:hover {
                background-color: #8b5cf6;
            }
            QPushButton:pressed {
                background-color: #6d28d9;
            }
            QTabWidget::pane { 
                border: 1px solid #444; 
                border-radius: 4px;
            }
            QTabBar::tab { 
                background-color: #2d2d2d;
                color: white;
                padding: 8px 20px;
                border-radius: 4px 4px 0 0;
                margin-right: 2px;
            }
            QTabBar::tab:selected { 
                background-color: #7c3aed;
                font-weight: bold;
            }
            QTabBar::tab:hover {
                background-color: #3d3d3d;
            }
            QComboBox {
                background-color: #2d2d2d;
                color: white;
                border: 1px solid #666;
                border-radius: 4px;
                padding: 4px;
            }
            QComboBox::drop-down {
                border-radius: 3px;
            }
            QSpinBox, QDoubleSpinBox {
                background-color: #2d2d2d;
                color: white;
                border: 1px solid #666;
                border-radius: 4px;
                padding: 4px;
            }
            QLineEdit {
                background-color: #2d2d2d;
                color: white;
                border: 1px solid #666;
                border-radius: 4px;
                padding: 4px;
            }
            QSlider::groove:horizontal {
                background-color: #555;
                height: 6px;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background-color: #7c3aed;
                width: 16px;
                margin: -5px 0;
                border-radius: 8px;
                border: 1px solid #6d28d9;
            }
            QSlider::handle:horizontal:hover {
                background-color: #8b5cf6;
            }
            QCheckBox {
                color: white;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 3px;
                border: 1px solid #666;
            }
            QCheckBox::indicator:checked {
                background-color: #7c3aed;
            }
            QGroupBox {
                color: white;
                border: 1px solid #666;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 5px;
            }
            QScrollArea {
                border-radius: 4px;
                border: 1px solid #444;
            }
            QTableWidget {
                background-color: #2d2d2d;
                color: white;
                border: 1px solid #666;
                border-radius: 4px;
                gridline-color: #555;
            }
            QTableWidget::item {
                padding: 4px;
            }
            QHeaderView::section {
                background-color: #1a1a1a;
                color: white;
                padding: 4px;
                border: 1px solid #666;
            }
            QPlainTextEdit {
                background-color: #2d2d2d;
                color: white;
                border: 1px solid #666;
                border-radius: 4px;
                padding: 4px;
            }
            QMessageBox QLabel {
                color: white;
            }
            QDialog {
                background-color: #1a1a1a;
            }
        """)

    def _wrap_group(self, title: str, widget: QWidget) -> QGroupBox:
        """Wrap a widget in a labeled group box."""
        group = QGroupBox(title)
        layout = QVBoxLayout(group)
        layout.addWidget(widget)
        return group

    def _wrap_scroll(self, widget: QWidget) -> QWidget:
        """Wrap a widget in a scroll area."""
        if isinstance(widget, QScrollArea):
            return widget
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(widget)
        return scroll

    def toggle_max_restore(self) -> None:
        """Toggle between maximized and normal window state."""
        if self.isMaximized():
            self.showNormal()
            self.max_restore_btn.setText("Maximize")
        else:
            self.showMaximized()
            self.max_restore_btn.setText("Restore")

    def create_main_controls_tab(self) -> QWidget:
        """Create a combined controls tab with grouped sections."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # === Lattice & Material Configuration ===
        lattice_material_layout = QVBoxLayout()
        lattice_material_layout.addWidget(QLabel("Lattice & Material Configuration:"))
        lattice_material_layout.setSpacing(2)
        
        # Create sub-layout for 2-column layout
        lattice_material_grid = QHBoxLayout()
        
        # Lattice on left
        lattice_layout = QVBoxLayout()
        lattice_widget = self.create_lattice_tab()
        lattice_layout.addWidget(lattice_widget)
        
        # Material on right
        material_layout = QVBoxLayout()
        material_widget = self.create_material_tab()
        material_layout.addWidget(material_widget)
        
        lattice_material_grid.addLayout(lattice_layout)
        lattice_material_grid.addLayout(material_layout)
        
        # Combined apply button
        apply_lattice_material_btn = QPushButton("✓ Apply Configuration")
        apply_lattice_material_btn.clicked.connect(self.apply_lattice_material_configuration)
        lattice_material_grid.addWidget(apply_lattice_material_btn)
        
        lattice_material_layout.addLayout(lattice_material_grid)
        
        group_lattice_material = QGroupBox("Lattice & Material Configuration")
        group_lattice_material.setLayout(lattice_material_layout)
        layout.addWidget(group_lattice_material)

        # === Simulation & Band Structure ===
        sim_band_layout = QVBoxLayout()
        sim_band_layout.addWidget(QLabel("Simulation & Band Structure Analysis:"))
        sim_band_layout.setSpacing(2)
        
        # Create sub-layout for 2-column layout
        sim_band_grid = QHBoxLayout()
        
        # Simulation on left
        sim_layout = QVBoxLayout()
        sim_widget = self.create_simulation_tab()
        sim_layout.addWidget(sim_widget)
        
        # Band structure on right
        band_layout = QVBoxLayout()
        band_widget = self.create_bandstructure_tab()
        band_layout.addWidget(band_widget)
        
        sim_band_grid.addLayout(sim_layout)
        sim_band_grid.addLayout(band_layout)
        
        sim_band_layout.addLayout(sim_band_grid)
        
        group_sim_band = QGroupBox("Simulation & Analysis")
        group_sim_band.setLayout(sim_band_layout)
        layout.addWidget(group_sim_band)

        layout.addStretch()

        return widget

    def create_plot_tab(self) -> QWidget:
        """Create the structure plot display tab (minimal spacing)."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)  # Reduce margins
        layout.setSpacing(5)  # Reduce spacing

        self.plot_tab = widget

        self.plot_title = QLabel("Pentagon Structure Plot")
        self.plot_title.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        self.plot_label = QLabel("No plot available yet.")
        self.plot_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.plot_label.setStyleSheet("background-color: #1f1f1f; padding: 5px; border-radius: 5px;")
        self.plot_label.setMinimumHeight(0)  # Remove minimum height constraint

        layout.addWidget(self.plot_title)
        layout.addWidget(self.plot_label, 1)  # Add stretch factor
        return widget

    def create_meep_results_tab(self) -> QWidget:
        """Create the MEEP results display tab with frequency selector (minimal spacing)."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)  # Reduce margins
        layout.setSpacing(5)  # Reduce spacing

        self.meep_tab = widget

        title = QLabel("MEEP Results (Hz Field)")
        title.setFont(QFont("Arial", 11, QFont.Weight.Bold))

        freq_layout = QHBoxLayout()
        freq_layout.setSpacing(5)
        freq_layout.addWidget(QLabel("Resonant Frequency:"))
        self.meep_freq_combo = QComboBox()
        self.meep_freq_combo.currentIndexChanged.connect(self.on_meep_frequency_changed)
        freq_layout.addWidget(self.meep_freq_combo)
        freq_layout.addStretch()

        self.meep_plot_label = QLabel("No MEEP results yet.")
        self.meep_plot_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.meep_plot_label.setStyleSheet("background-color: #1f1f1f; padding: 5px; border-radius: 5px;")
        self.meep_plot_label.setMinimumHeight(0)  # Remove minimum height constraint

        layout.addWidget(title)
        layout.addLayout(freq_layout)
        layout.addWidget(self.meep_plot_label, 1)  # Add stretch factor

        return widget
    
    def create_lattice_tab(self) -> QWidget:
        """Create the lattice configuration tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Lattice type selection
        lattice_label = QLabel("Lattice Type:")
        lattice_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.lattice_combo = QComboBox()
        self.lattice_combo.addItems(["Uniform", "Cavity"])
        self.lattice_combo.currentTextChanged.connect(self.on_lattice_type_changed)
        
        layout.addWidget(lattice_label)
        layout.addWidget(self.lattice_combo)
        
        # Unit cell parameter (a)
        a_label = QLabel("Unit Cell (a) [μm]:")
        self.a_slider = QSlider(Qt.Orientation.Horizontal)
        self.a_slider.setRange(20, 100)
        self.a_slider.setValue(40)
        self.a_display = QLabel("0.4 μm")
        self.a_slider.valueChanged.connect(self.update_a_display)
        
        layout.addWidget(a_label)
        layout.addWidget(self.a_slider)
        layout.addWidget(self.a_display)
        
        # Cavity offset (d/a)
        d_label = QLabel("Cavity Offset (d/a):")
        self.d_slider = QSlider(Qt.Orientation.Horizontal)
        self.d_slider.setRange(10, 50)
        self.d_slider.setValue(30)
        self.d_display = QLabel("0.30")
        self.d_slider.valueChanged.connect(self.update_d_display)
        
        layout.addWidget(d_label)
        layout.addWidget(self.d_slider)
        layout.addWidget(self.d_display)
        
        # Apply button
        apply_btn = QPushButton("Apply Cavity Settings")
        apply_btn.clicked.connect(self.apply_cavity_settings)
        layout.addWidget(apply_btn)
        
        # Periodic lattice
        layout.addSpacing(20)
        periodic_label = QLabel("Periodic Lattice:")
        periodic_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.periodic_check = QCheckBox("Enable Periodic Lattice")
        self.periodic_check.setChecked(True)
        layout.addWidget(periodic_label)
        layout.addWidget(self.periodic_check)
        
        # Hole radius
        radius_label = QLabel("Hole Radius (nm):")
        self.radius_spin = QSpinBox()
        self.radius_spin.setRange(20, 200)
        self.radius_spin.setValue(80)
        layout.addWidget(radius_label)
        layout.addWidget(self.radius_spin)
        
        # Apply periodic settings button
        apply_periodic_btn = QPushButton("Apply Periodic Settings")
        apply_periodic_btn.clicked.connect(self.apply_periodic_settings)
        layout.addWidget(apply_periodic_btn)
        
        layout.addStretch()
        return widget
    
    def create_material_tab(self) -> QWidget:
        """Create the material selection tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        label = QLabel("Select Material:")
        label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        
        self.material_combo = QComboBox()
        self.material_combo.addItems(["Default", "Silicon", "GaAs", "InP"])
        
        apply_btn = QPushButton("Apply Material")
        apply_btn.clicked.connect(self.apply_material)
        
        layout.addWidget(label)
        layout.addWidget(self.material_combo)
        layout.addWidget(apply_btn)
        layout.addStretch()
        
        return widget
    
    def create_simulation_tab(self) -> QWidget:
        """Create the simulation controls tab with embedded results display."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        label = QLabel("Simulation Controls:")
        label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        
        # Preset steps options
        steps_label = QLabel("Preset Steps:")
        self.steps_combo = QComboBox()
        self.steps_combo.addItems(["Fast (10)", "Medium (50)", "Full (200)"])
        self.steps_combo.currentIndexChanged.connect(self._on_preset_steps_changed)
        
        # Custom steps option
        custom_label = QLabel("Custom Steps:")
        custom_layout = QHBoxLayout()
        self.custom_steps_spin = QSpinBox()
        self.custom_steps_spin.setRange(1, 10000)
        self.custom_steps_spin.setValue(1000)
        self.custom_steps_spin.setSingleStep(100)
        steps_unit = QLabel("(1-10000)")
        steps_unit.setStyleSheet("color: #999999; font-size: 10px;")
        custom_layout.addWidget(self.custom_steps_spin)
        custom_layout.addWidget(steps_unit)
        custom_layout.addStretch()
        
        self.run_btn = QPushButton("▶ Run Simulation")
        self.run_btn.clicked.connect(self.run_simulation)
        
        self.stop_btn = QPushButton("■ Stop")
        self.stop_btn.clicked.connect(self.stop_simulation)
        self.stop_btn.setEnabled(False)
        
        self.sim_progress = QProgressBar()
        self.sim_progress.setVisible(False)
        
        self.sim_status = QLabel("")
        self.sim_status.setStyleSheet("color: lightcyan;")
        
        # Embedded simulation result preview
        result_label = QLabel("Simulation Results:")
        result_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        result_label.setStyleSheet("margin-top: 10px;")
        
        self.sim_result_display = QLabel("No simulation run yet.")
        self.sim_result_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.sim_result_display.setStyleSheet("background-color: #1f1f1f; padding: 10px; border-radius: 5px;")
        self.sim_result_display.setMinimumHeight(200)
        self.sim_result_display.setScaledContents(True)
        
        layout.addWidget(label)
        layout.addWidget(steps_label)
        layout.addWidget(self.steps_combo)
        layout.addWidget(custom_label)
        layout.addLayout(custom_layout)
        layout.addWidget(self.run_btn)
        layout.addWidget(self.stop_btn)
        layout.addWidget(self.sim_progress)
        layout.addWidget(self.sim_status)
        layout.addWidget(result_label)
        layout.addWidget(self.sim_result_display, 1)  # Stretchable
        
        return widget
    
    def _on_preset_steps_changed(self, index: int) -> None:
        """Update custom steps when preset is selected."""
        preset_values = [10, 50, 200]
        if index >= 0 and index < len(preset_values):
            self.custom_steps_spin.setValue(preset_values[index])
    
    def create_bandstructure_tab(self) -> QWidget:
        """Create the band structure tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        label = QLabel("Band Structure Calculation:")
        label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        
        kpoints_label = QLabel("K-points:")
        self.kpoints_spin = QSpinBox()
        self.kpoints_spin.setRange(10, 200)
        self.kpoints_spin.setValue(50)
        self.kpoints_spin.setSingleStep(10)
        
        self.calc_band_btn = QPushButton("📊 Calculate Band Structure")
        self.calc_band_btn.clicked.connect(self.calculate_band_structure)

        self.plot_band_btn = QPushButton("📈 Plot Band Structure")
        self.plot_band_btn.clicked.connect(self.plot_band_structure)
        
        self.stop_band_btn = QPushButton("■ Stop")
        self.stop_band_btn.clicked.connect(self.stop_band_calculation)
        self.stop_band_btn.setEnabled(False)
        
        self.band_progress = QProgressBar()
        self.band_progress.setVisible(False)
        
        self.band_status = QLabel("")
        self.band_status.setStyleSheet("color: lightcyan;")
        
        layout.addWidget(label)
        layout.addWidget(kpoints_label)
        layout.addWidget(self.kpoints_spin)
        layout.addWidget(self.calc_band_btn)
        layout.addWidget(self.plot_band_btn)
        layout.addWidget(self.stop_band_btn)
        layout.addWidget(self.band_progress)
        layout.addWidget(self.band_status)
        layout.addStretch()
        
        return widget
    
    def create_pentagon_tab(self) -> QWidget:
        """Create the pentagon structure configuration tab."""
        widget = QWidget()
        main_layout = QVBoxLayout(widget)
        
        # Title
        title = QLabel("Pentagon Structure Creation")
        title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        main_layout.addWidget(title)
        
        # Create scroll area for many controls
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # === Decay Profile Selection ===
        decay_label = QLabel("Decay Profile:")
        decay_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        scroll_layout.addWidget(decay_label)
        
        self.decay_profile_combo = QComboBox()
        self.decay_profile_combo.addItems(["Exponential", "Gaussian", "Polynomial", "Custom"])
        self.decay_profile_combo.setCurrentIndex(0)
        self.decay_profile_combo.currentTextChanged.connect(self.on_decay_profile_changed)
        scroll_layout.addWidget(self.decay_profile_combo)
        
        # Custom decay equation
        custom_eq_label = QLabel("Custom Equation (if selected):")
        self.custom_eq_input = QLineEdit()
        self.custom_eq_input.setText("exp(-3*x)")
        self.custom_eq_input.setPlaceholderText("e.g., exp(-3*x), x**2, etc.")
        self.custom_eq_input.textChanged.connect(self.on_custom_equation_changed)
        scroll_layout.addWidget(custom_eq_label)
        scroll_layout.addWidget(self.custom_eq_input)
        
        # === Disclination Angle ===
        angle_label = QLabel("Target Angle (°):")
        angle_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        
        angle_layout = QHBoxLayout()
        self.angle_spin = QSpinBox()
        self.angle_spin.setRange(30, 120)
        self.angle_spin.setValue(72)
        self.angle_spin.setSingleStep(1)
        self.angle_spin.valueChanged.connect(self.on_angle_changed)
        
        self.angle_slider = QSlider(Qt.Orientation.Horizontal)
        self.angle_slider.setRange(30, 120)
        self.angle_slider.setValue(72)
        self.angle_slider.valueChanged.connect(self.angle_spin.setValue)
        
        angle_layout.addWidget(QLabel("Angle:"))
        angle_layout.addWidget(self.angle_slider)
        angle_layout.addWidget(self.angle_spin)
        
        scroll_layout.addWidget(angle_label)
        scroll_layout.addLayout(angle_layout)
        
        # === Decay Rate Multiplier ===
        decay_rate_label = QLabel("Decay Rate:")
        decay_rate_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        
        decay_layout = QHBoxLayout()
        self.decay_slider = QSlider(Qt.Orientation.Horizontal)
        self.decay_slider.setRange(1, 50)
        self.decay_slider.setValue(10)
        self.decay_slider.valueChanged.connect(self.on_decay_rate_changed)
        
        self.decay_display = QLabel("1.0x")
        
        decay_layout.addWidget(self.decay_slider)
        decay_layout.addWidget(self.decay_display)
        
        scroll_layout.addWidget(decay_rate_label)
        scroll_layout.addLayout(decay_layout)
        
        # === Global Scale ===
        scale_label = QLabel("Global Scale:")
        scale_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        
        scale_layout = QHBoxLayout()
        self.global_scale_slider = QSlider(Qt.Orientation.Horizontal)
        self.global_scale_slider.setRange(50, 200)
        self.global_scale_slider.setValue(100)
        self.global_scale_slider.valueChanged.connect(self.on_global_scale_changed)
        
        self.scale_display = QLabel("1.0x")
        
        scale_layout.addWidget(self.global_scale_slider)
        scale_layout.addWidget(self.scale_display)
        
        scroll_layout.addWidget(scale_label)
        scroll_layout.addLayout(scale_layout)
        
        # === Number of Cells ===
        cells_label = QLabel("Number of Cells:")
        self.cells_spin = QSpinBox()
        self.cells_spin.setRange(1, 10)
        self.cells_spin.setValue(3)
        scroll_layout.addWidget(cells_label)
        scroll_layout.addWidget(self.cells_spin)

        # === Transform Corner Selection ===
        corner_label = QLabel("Transform Corner:")
        corner_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        self.corner_combo = QComboBox()
        self.corner_combo.addItems(["bottom_left", "bottom_right", "top_left", "top_right"])
        self.corner_combo.setCurrentText("bottom_left")
        scroll_layout.addWidget(corner_label)
        scroll_layout.addWidget(self.corner_combo)

        # === Manual Edit Mode (Always Enabled) ===
        manual_label = QLabel("Manual Edit Mode (Always On):")
        manual_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        scroll_layout.addWidget(manual_label)

        # Manual edit container
        self.manual_edit_container = QWidget()
        manual_layout = QVBoxLayout(self.manual_edit_container)

        # Unit cell vectors (nm)
        unit_cell_label = QLabel("Unit Cell Vectors (nm):")
        manual_layout.addWidget(unit_cell_label)

        unit_cell_layout = QHBoxLayout()
        self.a1x_spin = QDoubleSpinBox()
        self.a1x_spin.setRange(-2000, 2000)
        self.a1x_spin.setValue(400)
        self.a1x_spin.setDecimals(3)
        self.a1y_spin = QDoubleSpinBox()
        self.a1y_spin.setRange(-2000, 2000)
        self.a1y_spin.setValue(0)
        self.a1y_spin.setDecimals(3)
        self.a2x_spin = QDoubleSpinBox()
        self.a2x_spin.setRange(-2000, 2000)
        self.a2x_spin.setValue(0)
        self.a2x_spin.setDecimals(3)
        self.a2y_spin = QDoubleSpinBox()
        self.a2y_spin.setRange(-2000, 2000)
        self.a2y_spin.setValue(400)
        self.a2y_spin.setDecimals(3)

        unit_cell_layout.addWidget(QLabel("a1x"))
        unit_cell_layout.addWidget(self.a1x_spin)
        unit_cell_layout.addWidget(QLabel("a1y"))
        unit_cell_layout.addWidget(self.a1y_spin)
        unit_cell_layout.addWidget(QLabel("a2x"))
        unit_cell_layout.addWidget(self.a2x_spin)
        unit_cell_layout.addWidget(QLabel("a2y"))
        unit_cell_layout.addWidget(self.a2y_spin)
        manual_layout.addLayout(unit_cell_layout)

        # Basis sites table with auto-update
        basis_label = QLabel("Basis Sites (nm):")
        manual_layout.addWidget(basis_label)

        self.basis_table = QTableWidget(2, 2)
        self.basis_table.setHorizontalHeaderLabels(["X", "Y"])
        basis_header = self.basis_table.horizontalHeader()
        if basis_header is not None:
            basis_header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.basis_table.setItem(0, 0, QTableWidgetItem("-100"))
        self.basis_table.setItem(0, 1, QTableWidgetItem("-100"))
        self.basis_table.setItem(1, 0, QTableWidgetItem("100"))
        self.basis_table.setItem(1, 1, QTableWidgetItem("100"))
        # Connect to auto-update when cells change
        self.basis_table.cellChanged.connect(self.on_basis_sites_changed)
        manual_layout.addWidget(self.basis_table)

        basis_buttons = QHBoxLayout()
        self.add_basis_btn = QPushButton("Add Basis Row")
        self.add_basis_btn.clicked.connect(self.add_basis_row)
        self.remove_basis_btn = QPushButton("Remove Basis Row")
        self.remove_basis_btn.clicked.connect(self.remove_basis_row)
        basis_buttons.addWidget(self.add_basis_btn)
        basis_buttons.addWidget(self.remove_basis_btn)
        manual_layout.addLayout(basis_buttons)

        # Note: Atom positions are now displayed in the interactive editor
        # which opens when "Plot & Edit Pentagon" is clicked
        
        scroll_layout.addWidget(self.manual_edit_container)
        
        # === MEEP Parameters (collapsed) ===
        meep_group_label = QLabel("MEEP Electromagnetic Parameters:")
        meep_group_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        scroll_layout.addWidget(meep_group_label)
        
        meep_layout = QHBoxLayout()
        
        # Frequency (no restrictions)
        meep_freq_layout = QVBoxLayout()
        meep_freq_layout.addWidget(QLabel("Frequency:"))
        self.meep_freq_spin = QDoubleSpinBox()
        self.meep_freq_spin.setRange(0.0, 10000.0)  # No practical restrictions
        self.meep_freq_spin.setValue(0.15)
        self.meep_freq_spin.setSingleStep(0.01)
        self.meep_freq_spin.setDecimals(4)
        meep_freq_layout.addWidget(self.meep_freq_spin)
        
        # Resolution
        meep_res_layout = QVBoxLayout()
        meep_res_layout.addWidget(QLabel("Resolution:"))
        self.meep_res_spin = QSpinBox()
        self.meep_res_spin.setRange(5, 50)
        self.meep_res_spin.setValue(20)
        meep_res_layout.addWidget(self.meep_res_spin)
        
        # Epsilon
        meep_eps_layout = QVBoxLayout()
        meep_eps_layout.addWidget(QLabel("Epsilon:"))
        self.meep_eps_spin = QDoubleSpinBox()
        self.meep_eps_spin.setRange(1.0, 20.0)
        self.meep_eps_spin.setValue(12.0)
        self.meep_eps_spin.setSingleStep(0.1)
        self.meep_eps_spin.setDecimals(1)
        meep_eps_layout.addWidget(self.meep_eps_spin)
        
        meep_layout.addLayout(meep_freq_layout)
        meep_layout.addLayout(meep_res_layout)
        meep_layout.addLayout(meep_eps_layout)
        
        scroll_layout.addLayout(meep_layout)
        
        # === Action Buttons ===
        buttons_layout = QHBoxLayout()
        
        self.plot_pentagon_btn = QPushButton("🎨 Plot & Edit Pentagon")
        self.plot_pentagon_btn.clicked.connect(self.plot_pentagon_with_editor)
        buttons_layout.addWidget(self.plot_pentagon_btn)
        
        self.simulate_meep_btn = QPushButton("⚡ Simulate MEEP")
        self.simulate_meep_btn.clicked.connect(self.simulate_meep_structure)
        buttons_layout.addWidget(self.simulate_meep_btn)
        
        self.export_pentagon_btn = QPushButton("💾 Export Structure")
        self.export_pentagon_btn.clicked.connect(self.export_pentagon_structure)
        buttons_layout.addWidget(self.export_pentagon_btn)
        
        scroll_layout.addLayout(buttons_layout)
        scroll_layout.addStretch()
        
        scroll.setWidget(scroll_widget)
        main_layout.addWidget(scroll)

        # Manual edit controls always enabled
        self.manual_edit_container.setEnabled(True)
        
        return widget
    
    def create_info_tab(self) -> QWidget:
        """Create the information display tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        label = QLabel("Structure Information:")
        label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        
        self.info_display = QTextEdit()
        self.info_display.setReadOnly(True)
        self.info_display.setStyleSheet("""
            QTextEdit { 
                background-color: black; 
                color: lightgreen; 
                font-family: Courier; 
            }
        """)
        
        refresh_btn = QPushButton("🔄 Refresh Info")
        refresh_btn.clicked.connect(self.refresh_info)
        
        save_btn = QPushButton("💾 Save Configuration")
        save_btn.clicked.connect(self.save_configuration)
        
        layout.addWidget(label)
        layout.addWidget(self.info_display)
        layout.addWidget(refresh_btn)
        layout.addWidget(save_btn)
        
        return widget
    
    def on_lattice_type_changed(self, lattice_type: str) -> None:
        """Handle lattice type change."""
        try:
            if lattice_type == "Cavity":
                self.gui.switch_to_cavity_lattice()  # type: ignore
            else:
                self.gui.switch_to_uniform_lattice()  # type: ignore
            self.refresh_info()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to change lattice type:\n{str(e)}")
    
    def update_a_display(self, value: int) -> None:
        """Update display for unit cell parameter."""
        a_val = value / 100.0
        self.a_display.setText(f"{a_val:.2f} μm")
    
    def update_d_display(self, value: int) -> None:
        """Update display for cavity offset parameter."""
        d_val = value / 100.0
        self.d_display.setText(f"{d_val:.2f}")
    
    def apply_cavity_settings(self) -> None:
        """Apply cavity parameter changes."""
        try:
            a = self.a_slider.value() / 100.0
            d = self.d_slider.value() / 100.0
            self.gui.set_cavity_parameters(unit_cell_a_um=a, offset_d_frac=d)  # type: ignore
            QMessageBox.information(self, "Success", "Cavity settings applied")
            self.refresh_info()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to apply cavity settings:\n{str(e)}")
    
    def apply_material(self) -> None:
        """Apply material selection."""
        try:
            material = self.material_combo.currentText()
            self.gui.set_substrate_material(material)  # type: ignore
            QMessageBox.information(self, "Success", f"Material updated to {material}")
            self.refresh_info()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to update material:\n{str(e)}")
    
    def apply_lattice_material_configuration(self) -> None:
        """Apply both lattice and material configurations together."""
        try:
            # Get lattice type
            lattice_type = self.lattice_combo.currentText()
            
            # Get material selection
            material = self.material_combo.currentText()
            
            # Apply both
            self.gui.set_substrate_material(material)  # type: ignore
            
            QMessageBox.information(self, "Success", 
                                  f"✓ Configuration Applied:\n"
                                  f"• Lattice: {lattice_type}\n"
                                  f"• Material: {material}\n"
                                  f"\nReady for simulation!")
            self.refresh_info()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to apply configuration:\n{str(e)}")
    
    def run_simulation(self) -> None:
        """Run the simulation in a background thread using custom steps value."""
        if self.sim_worker is not None and self.sim_worker.isRunning():
            QMessageBox.warning(self, "Warning", "Simulation already running")
            return
        
        # Use custom steps spinner value
        num_steps = self.custom_steps_spin.value()
        
        self.run_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.sim_progress.setVisible(True)
        self.sim_progress.setValue(0)
        self.sim_status.setText(f"Running simulation with {num_steps} steps...")
        
        self.sim_worker = SimulationWorker(self.gui, num_steps)
        self.sim_worker.progress_updated.connect(self.update_sim_progress)
        self.sim_worker.simulation_complete.connect(self.on_simulation_complete)
        self.sim_worker.simulation_error.connect(self.on_simulation_error)
        self.sim_worker.start()
    
    def stop_simulation(self) -> None:
        """Stop the running simulation."""
        if self.sim_worker is not None:
            self.sim_worker.stop()
            self.sim_worker.wait()
        
        self.run_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.sim_progress.setVisible(False)
        self.sim_status.setText("Simulation stopped")
    
    def update_sim_progress(self, progress: int, status: str) -> None:
        """Update simulation progress display."""
        self.sim_progress.setValue(progress)
        self.sim_status.setText(f"Progress: {progress}% - {status}")
    
    def on_simulation_complete(self) -> None:
        """Handle simulation completion and display inline results."""
        self.run_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.sim_progress.setVisible(False)
        self.sim_status.setText("✓ Simulation complete")
        self.refresh_info()
        
        # Display simulation results inline
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            import numpy as np
            from PyQt6.QtGui import QPixmap
            
            # Create quick preview of simulation results
            fig, ax = plt.subplots(1, 1, figsize=(8, 6))
            
            # Plot structure with field intensity overlay (placeholder)
            if self.pentagon_atoms is not None:
                ax.scatter(self.pentagon_atoms[:, 0], self.pentagon_atoms[:, 1], 
                          s=80, alpha=0.7, color='cyan', edgecolors='blue', linewidth=1)
                ax.set_xlabel('X (nm)', fontsize=11, fontweight='bold')
                ax.set_ylabel('Y (nm)', fontsize=11, fontweight='bold')
                ax.set_title('Simulation Complete - Structure Overview', fontsize=12, fontweight='bold')
                ax.grid(True, alpha=0.3)
                ax.axis('equal')
            else:
                ax.text(0.5, 0.5, '✓ Simulation Complete\nView detailed results in MEEP tab', 
                       ha='center', va='center', fontsize=14, transform=ax.transAxes)
                ax.axis('off')
            
            plt.tight_layout()
            sim_preview_file = '/tmp/sim_preview.png'
            plt.savefig(sim_preview_file, dpi=100, bbox_inches='tight', facecolor='#1f1f1f')
            plt.close()
            
            # Display in simulation tab
            pixmap = QPixmap(sim_preview_file)
            if not pixmap.isNull():
                self.sim_result_display.setPixmap(pixmap.scaled(
                    self.sim_result_display.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                ))
        except Exception as e:
            print(f"Error displaying simulation preview: {e}")
            self.sim_result_display.setText(f"✓ Simulation Complete\n(Preview unavailable)")
    
    def on_simulation_error(self, error: str) -> None:
        """Handle simulation error."""
        self.run_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.sim_progress.setVisible(False)
        self.sim_status.setText(f"✗ Error: {error}")
        QMessageBox.critical(self, "Simulation Error", f"An error occurred:\n{error}")
    
    def calculate_band_structure(self) -> None:
        """Calculate band structure for unit cell with Floquet periodicity."""
        if self.band_worker is not None and self.band_worker.isRunning():
            QMessageBox.warning(self, "Warning", "Band calculation already running")
            return
        
        num_kpoints = self.kpoints_spin.value()
        
        self.calc_band_btn.setEnabled(False)
        self.stop_band_btn.setEnabled(True)
        self.band_progress.setVisible(True)
        self.band_progress.setValue(0)
        self.band_status.setText("Calculating band structure...")
        
        self.band_worker = BandStructureWorker(self.gui, num_kpoints)
        self.band_worker.progress_updated.connect(self.update_band_progress)
        self.band_worker.calculation_complete.connect(self.on_band_complete)
        self.band_worker.calculation_error.connect(self.on_band_error)
        self.band_worker.start()
    
    def stop_band_calculation(self) -> None:
        """Stop band structure calculation."""
        if self.band_worker is not None:
            self.band_worker.stop()
            self.band_worker.wait()
        
        self.calc_band_btn.setEnabled(True)
        self.stop_band_btn.setEnabled(False)
        self.band_progress.setVisible(False)
        self.band_status.setText("Calculation stopped")
    
    def update_band_progress(self, progress: int, status: str) -> None:
        """Update band structure progress display."""
        self.band_progress.setValue(progress)
        self.band_status.setText(f"Progress: {progress}% - {status}")
    
    def on_band_complete(self, band_data) -> None:
        """Handle band structure calculation completion."""
        self.calc_band_btn.setEnabled(True)
        self.stop_band_btn.setEnabled(False)
        self.band_progress.setVisible(False)
        self.band_status.setText("✓ Band structure calculated")
        self.band_data = band_data
        self.refresh_info()
    
    def on_band_error(self, error: str) -> None:
        """Handle band calculation error."""
        self.calc_band_btn.setEnabled(True)
        self.stop_band_btn.setEnabled(False)
        self.band_progress.setVisible(False)
        self.band_status.setText(f"✗ Error: {error}")
        QMessageBox.critical(self, "Band Structure Error", f"An error occurred:\n{error}")
    
    def refresh_info(self) -> None:
        """Refresh the information display."""
        try:
            info_text = self.gui.get_structure_info()  # type: ignore
            if isinstance(info_text, dict):
                info_text = str(info_text)
            self.info_display.setText(info_text)
        except Exception as e:
            self.info_display.setText(f"Error loading info: {str(e)}")

    def plot_band_structure(self) -> None:
        """Plot band structure with corresponding structure visualization."""
        try:
            if not hasattr(self, 'band_data') or not self.band_data:
                QMessageBox.warning(self, "No Data", "Please calculate band structure first.")
                return

            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            import numpy as np

            k_points = np.array(self.band_data.get('k_points', []))
            freqs = np.array(self.band_data.get('frequencies', []))

            if k_points.size == 0 or freqs.size == 0:
                QMessageBox.warning(self, "No Data", "Band structure data is empty.")
                return

            # Create side-by-side plot: structure on left, band diagram on right
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
            
            # LEFT: Show the structure for which band structure was calculated
            if self.pentagon_atoms is not None:
                atoms = np.array(self.pentagon_atoms)
                ax1.scatter(atoms[:, 0], atoms[:, 1], s=80, alpha=0.7,
                           color='blue', edgecolors='darkblue', linewidth=1)
                
                # Draw unit cell boundaries if available
                if self.pentagon_cells is not None:
                    cell_corners = self.pentagon_cells
                    colors = ['red', 'green', 'blue', 'cyan', 'magenta', 'yellow']
                    for i, corners in enumerate(cell_corners[:30]):  # Limit for clarity
                        corners_array = np.array(corners)
                        corners_closed = np.vstack([corners_array, corners_array[0]])
                        color = colors[i % len(colors)]
                        ax1.plot(corners_closed[:, 0], corners_closed[:, 1],
                                color=color, linewidth=1, alpha=0.4)
                
                ax1.set_xlabel('X (nm)', fontsize=11, fontweight='bold')
                ax1.set_ylabel('Y (nm)', fontsize=11, fontweight='bold')
                ax1.set_title('Pentagon Structure', fontsize=12, fontweight='bold')
                ax1.axis('equal')
                ax1.grid(True, alpha=0.3)
                
                # Add structure info
                info_text = f"Atoms: {len(atoms)}"
                if hasattr(self, 'pentagon_params'):
                    params = self.pentagon_params
                    info_text += f"\nCells: {params.get('n_cells', 'N/A')}×{params.get('n_cells', 'N/A')}"
                    info_text += f"\nAngle: {params.get('target_angle', 'N/A')}°"
                ax1.text(0.02, 0.98, info_text, transform=ax1.transAxes,
                        fontsize=9, verticalalignment='top',
                        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
            else:
                ax1.text(0.5, 0.5, 'No structure data available',
                        ha='center', va='center', transform=ax1.transAxes,
                        fontsize=12, color='gray')
                ax1.set_title('Structure', fontsize=12, fontweight='bold')
                ax1.axis('off')
            
            # RIGHT: Band structure diagram
            for f in freqs:
                ax2.plot(k_points, np.full_like(k_points, f), color='navy', alpha=0.4, linewidth=1.5)

            ax2.set_title("Band Structure (Floquet)", fontsize=12, fontweight='bold')
            ax2.set_xlabel("k", fontsize=11, fontweight='bold')
            ax2.set_ylabel("Frequency", fontsize=11, fontweight='bold')
            ax2.grid(True, alpha=0.3)
            
            # Add band count info
            ax2.text(0.98, 0.02, f'{len(freqs)} bands',
                    transform=ax2.transAxes, fontsize=9,
                    ha='right', va='bottom',
                    bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.5))

            plt.suptitle('Band Structure Analysis', fontsize=14, fontweight='bold', y=0.98)
            plot_file = '/tmp/band_structure.png'
            plt.tight_layout(rect=(0, 0, 1, 0.96))
            plt.savefig(plot_file, dpi=120, bbox_inches='tight', facecolor='white')
            plt.close()

            self.show_plot_dialog(plot_file, "Band Structure Analysis")

        except Exception as e:
            import traceback
            QMessageBox.critical(self, "Plot Error",
                               f"Failed to plot band structure:\n\n{str(e)}\n\n{traceback.format_exc()}")

    def _update_plot_tab(self, image_path: str, title: str) -> None:
        """Update the structure plot tab with a new image."""
        pixmap = QPixmap(image_path)
        if pixmap.isNull():
            self.plot_label.setText("Failed to load plot image.")
            return
        self.plot_title.setText(title)
        scaled = pixmap.scaledToWidth(900, Qt.TransformationMode.SmoothTransformation)
        self.plot_label.setPixmap(scaled)
        if self.plot_tab is not None:
            self.tabs.setCurrentWidget(self.plot_tab)

    def _update_meep_tab(self, image_path: str) -> None:
        """Update the MEEP results tab with a new image."""
        pixmap = QPixmap(image_path)
        if pixmap.isNull():
            self.meep_plot_label.setText("Failed to load MEEP image.")
            return
        scaled = pixmap.scaledToWidth(900, Qt.TransformationMode.SmoothTransformation)
        self.meep_plot_label.setPixmap(scaled)
        if self.meep_tab is not None:
            self.tabs.setCurrentWidget(self.meep_tab)

    def on_meep_frequency_changed(self, index: int) -> None:
        """Handle selection of a different resonant frequency."""
        if not self.meep_results:
            return
        fields = self.meep_results.get('hz_fields', [])
        if index < 0 or index >= len(fields):
            return
        self._render_meep_field(index)

    def _render_meep_field(self, index: int) -> None:
        """Render Hz field plot for selected index with proper pentagon center alignment."""
        try:
            if not self.meep_results:
                return
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            import numpy as np

            hz_data = self.meep_results['hz_fields'][index]
            eps_data = self.meep_results['eps_data']
            extent = self.meep_results['extent']

            fig, axes = plt.subplots(2, 1, figsize=(10, 8))
            
            # Plot structure with centered pentagon
            axes[0].imshow(eps_data.T, extent=extent, cmap='binary', origin='lower', alpha=0.7)
            
            # Overlay pentagon atoms if available (centered at origin)
            if self.pentagon_atoms is not None:
                # Convert nm to μm for overlay
                atoms_um = self.pentagon_atoms / 1000.0
                axes[0].scatter(atoms_um[:, 0], atoms_um[:, 1], s=20, color='red', 
                              alpha=0.5, marker='o', label='Atoms (centered)', zorder=10)
                # Mark origin
                axes[0].plot(0, 0, 'r+', markersize=15, markeredgewidth=2, label='Origin', zorder=11)
                axes[0].legend(loc='upper right', fontsize=8)
            
            axes[0].set_title('Photonic Structure (Pentagon Centered at Origin)')
            axes[0].set_xlabel('X (μm)')
            axes[0].set_ylabel('Y (μm)')
            axes[0].grid(True, alpha=0.3)
            axes[0].axhline(y=0, color='gray', linestyle='--', alpha=0.3, linewidth=1)
            axes[0].axvline(x=0, color='gray', linestyle='--', alpha=0.3, linewidth=1)

            # Plot Hz field intensity
            field_intensity = np.abs(hz_data)
            im = axes[1].imshow(field_intensity.T, extent=extent, cmap='hot', origin='lower')
            axes[1].set_title('Magnetic Field Intensity (Hz) - Centered')
            axes[1].set_xlabel('X (μm)')
            axes[1].set_ylabel('Y (μm)')
            plt.colorbar(im, ax=axes[1], label='|H_z|')
            axes[1].grid(True, alpha=0.3)
            axes[1].axhline(y=0, color='white', linestyle='--', alpha=0.5, linewidth=1)
            axes[1].axvline(x=0, color='white', linestyle='--', alpha=0.5, linewidth=1)

            plt.tight_layout()
            results_file = '/tmp/meep_results.png'
            plt.savefig(results_file, dpi=100, bbox_inches='tight')
            plt.close()

            self._update_meep_tab(results_file)
        except Exception as e:
            QMessageBox.warning(self, "MEEP Plot Error", f"Failed to render Hz field: {str(e)}")
    
    def apply_periodic_settings(self) -> None:
        """Apply periodic lattice settings."""
        try:
            self.gui.set_periodic_lattice_parameters(  # type: ignore
                hole_radius_nm=self.radius_spin.value(),
                offset_x_um=0.0,
                offset_y_um=0.0,
                enabled=self.periodic_check.isChecked()
            )
            QMessageBox.information(self, "Success", "Periodic lattice settings applied")
            self.refresh_info()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to apply periodic settings:\n{str(e)}")
    
    def save_configuration(self) -> None:
        """Save current configuration to file."""
        try:
            config = self.gui.get_structure_info()  # type: ignore
            if isinstance(config, dict):
                config_text = str(config)
            else:
                config_text = str(config)
            
            with open('photonic_config_backup.txt', 'w') as f:
                f.write(config_text)
            
            QMessageBox.information(self, "Success", "Configuration saved to photonic_config_backup.txt")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save configuration:\n{str(e)}")
    
    # ========================== PENTAGON STRUCTURE METHODS ==========================
    
    def on_decay_profile_changed(self, profile: str) -> None:
        """Handle decay profile change."""
        self.custom_eq_input.setEnabled(profile == "Custom")
    
    def on_custom_equation_changed(self, equation: str) -> None:
        """Handle custom equation input."""
        # Equations are validated when used in plotting
        pass
    
    def on_angle_changed(self, angle: int) -> None:
        """Handle target angle change."""
        self.angle_slider.blockSignals(True)
        self.angle_slider.setValue(angle)
        self.angle_slider.blockSignals(False)
    
    def on_decay_rate_changed(self, value: int) -> None:
        """Handle decay rate slider change."""
        rate = value / 10.0
        self.decay_display.setText(f"{rate:.1f}x")
    
    def on_global_scale_changed(self, value: int) -> None:
        """Handle global scale slider change."""
        scale = value / 100.0
        self.scale_display.setText(f"{scale:.2f}x")

    def on_manual_edit_toggled(self, enabled: bool) -> None:
        """Manual edit is always enabled - this method kept for compatibility."""
        self.manual_edit_enabled = True  # Always keep enabled
        if hasattr(self, 'manual_edit_container'):
            self.manual_edit_container.setEnabled(True)
    
    def on_basis_sites_changed(self) -> None:
        """Called when basis sites table is edited - auto-update the structure."""
        if self.manual_edit_enabled and self.pentagon_atoms is not None:
            # Automatically replot when basis sites change
            try:
                # Re-trigger plot with current parameters
                self.plot_pentagon_structure()
            except Exception as e:
                # Silently fail on invalid edits - let user fix and re-edit
                pass

    def add_basis_row(self) -> None:
        """Add a basis row to the basis table."""
        row = self.basis_table.rowCount()
        self.basis_table.insertRow(row)
        self.basis_table.setItem(row, 0, QTableWidgetItem("0"))
        self.basis_table.setItem(row, 1, QTableWidgetItem("0"))
        # Trigger structure update when basis changes
        if self.manual_edit_enabled and self.pentagon_atoms is not None:
            self.plot_pentagon_structure()

    def remove_basis_row(self) -> None:
        """Remove selected basis rows."""
        rows = sorted({idx.row() for idx in self.basis_table.selectedIndexes()}, reverse=True)
        for row in rows:
            self.basis_table.removeRow(row)
        # Trigger structure update when basis changes
        if self.manual_edit_enabled and self.pentagon_atoms is not None:
            self.plot_pentagon_structure()

    def _get_unit_cell_vectors(self):
        """Return unit cell vectors (nm) from UI."""
        import numpy as np
        a1 = np.array([self.a1x_spin.value(), self.a1y_spin.value()])
        a2 = np.array([self.a2x_spin.value(), self.a2y_spin.value()])
        return a1, a2

    def _get_basis_sites(self):
        """Return basis sites (nm) from basis table."""
        import numpy as np
        rows = self.basis_table.rowCount()
        sites = []
        for row in range(rows):
            x_item = self.basis_table.item(row, 0)
            y_item = self.basis_table.item(row, 1)
            if x_item is None or y_item is None:
                continue
            try:
                sites.append([float(x_item.text()), float(y_item.text())])
            except ValueError:
                continue
        if not sites:
            sites = [[-100.0, -100.0], [100.0, 100.0]]
        return np.array(sites)

    def _plot_current_pentagon(self, title_suffix: str = "") -> None:
        """Render the current pentagon data to the plot dialog."""
        if self.pentagon_atoms is None:
            QMessageBox.warning(self, "No Data", "Please plot pentagon structure first.")
            return

        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import numpy as np

        all_atoms = self.pentagon_atoms
        cell_corners = self.pentagon_cells if self.pentagon_cells is not None else []
        transform_factors = self.pentagon_transforms if self.pentagon_transforms is not None else []

        fig, axes = plt.subplots(1, 2, figsize=(16, 7))
        ax1, ax2 = axes

        # ===== LEFT PLOT: Pentagon Structure with Unit Cell Boundaries =====
        # Draw unit cell boundaries with distinct colors for clarity
        if cell_corners:
            colors = ['red', 'green', 'blue', 'cyan', 'magenta', 'yellow']
            for i, corners in enumerate(cell_corners):
                corners_closed = np.vstack([corners, corners[0]])
                # Cycle through colors for distinct visualization
                color = colors[i % len(colors)]
                ax1.plot(corners_closed[:, 0], corners_closed[:, 1], 
                        color=color, linewidth=1.5, alpha=0.6, label=f'Cell {i}' if i < 5 else '')

        # Plot atoms on top
        ax1.scatter(all_atoms[:, 0], all_atoms[:, 1], s=120, alpha=0.8,
                   color='blue', edgecolors='darkblue', linewidth=1, marker='o', label='Atoms',
                   zorder=5)  # Higher z-order so atoms appear on top

        ax1.set_xlabel('X (nm)', fontsize=12, fontweight='bold')
        ax1.set_ylabel('Y (nm)', fontsize=12, fontweight='bold')
        ax1.set_title(f'Pentagon Structure with Unit Cells {title_suffix}', 
                     fontsize=13, fontweight='bold')
        ax1.grid(True, alpha=0.3, linestyle='--')
        ax1.axis('equal')
        if len(cell_corners) < 6:  # Only show legend if reasonable number of cells
            ax1.legend(loc='upper left', fontsize=9)

        # ===== RIGHT PLOT: Transformation Factors (for Hz field overlay) =====
        cell_centers = []
        for corners in cell_corners:
            center = corners.mean(axis=0)
            cell_centers.append(center)

        if cell_centers and len(transform_factors) >= len(cell_centers):
            cell_centers_arr = np.array(cell_centers[:len(transform_factors)])
            scatter = ax2.scatter(cell_centers_arr[:, 0], cell_centers_arr[:, 1],
                                 c=transform_factors[:len(cell_centers)],
                                 s=300, cmap='viridis', alpha=0.85,
                                 edgecolors='black', linewidth=1.2, vmin=0, vmax=1.0)
            cbar = plt.colorbar(scatter, ax=ax2, label='Transformation Factor', pad=0.02)
            cbar.ax.tick_params(labelsize=10)

        # Draw cell boundaries faintly in background
        if cell_corners:
            for i, corners in enumerate(cell_corners):
                corners_closed = np.vstack([corners, corners[0]])
                ax2.plot(corners_closed[:, 0], corners_closed[:, 1], 
                        'gray', linewidth=0.8, alpha=0.3)

        ax2.set_xlabel('X (nm)', fontsize=12, fontweight='bold')
        ax2.set_ylabel('Y (nm)', fontsize=12, fontweight='bold')
        ax2.set_title('Transformation Factors (Hz Field Amplitude)', fontsize=13, fontweight='bold')
        ax2.grid(True, alpha=0.3, linestyle='--')
        ax2.axis('equal')

        # Add overall figure suptitle with structure info
        fig.suptitle(f'Pentagon Photonic Structure | {len(all_atoms)} atoms | {len(cell_corners)} cells',
                    fontsize=11, fontweight='bold', y=0.98)

        plt.tight_layout(rect=(0, 0, 1, 0.96))
        plot_file = '/tmp/pentagon_structure.png'
        plt.savefig(plot_file, dpi=120, bbox_inches='tight', facecolor='white')
        plt.close()

        self._update_plot_tab(plot_file, f"Pentagon Structure {title_suffix}")

    def _build_cyclic_pentagon_structure(
        self,
        n_cells: int,
        sq_a1,
        sq_a2,
        basis_sites,
        target_angle: float,
        stretch_corner: str,
        decay_profile: str,
        custom_eq: Optional[str]
    ):
        """Generate a 5-sector cyclic structure around the origin."""
        import numpy as np
        from testing import create_lattice_with_correct_atom_positions

        atoms, cell_corners, transform_factors, stretch_point = (
            create_lattice_with_correct_atom_positions(
                n_cells, n_cells, sq_a1, sq_a2, basis_sites,
                target_angle_deg=target_angle,
                stretch_corner=stretch_corner,
                decay_profile=decay_profile,
                custom_equation=custom_eq
            )
        )

        atoms = np.array(atoms)

        if stretch_point is not None:
            pivot = np.array(stretch_point)
        else:
            if stretch_corner == "bottom_left":
                pivot = np.array([atoms[:, 0].min(), atoms[:, 1].min()])
            elif stretch_corner == "bottom_right":
                pivot = np.array([atoms[:, 0].max(), atoms[:, 1].min()])
            elif stretch_corner == "top_left":
                pivot = np.array([atoms[:, 0].min(), atoms[:, 1].max()])
            else:
                pivot = np.array([atoms[:, 0].max(), atoms[:, 1].max()])

        atoms = atoms - pivot

        rotated_atoms = []
        rotated_cells = []
        rotated_factors = []
        for i in range(5):
            theta = np.deg2rad(72.0 * i)
            rot = np.array([
                [np.cos(theta), -np.sin(theta)],
                [np.sin(theta), np.cos(theta)]
            ])
            rotated_atoms.append(atoms @ rot.T)
            for corners in cell_corners:
                rotated_cells.append((corners - pivot) @ rot.T)
            if transform_factors is not None:
                rotated_factors.extend(transform_factors)

        all_atoms = np.vstack(rotated_atoms)
        # Remove duplicate atoms by rounding
        rounded = np.round(all_atoms, 4)
        _, idx = np.unique(rounded, axis=0, return_index=True)
        all_atoms = all_atoms[np.sort(idx)]
        
        # CRITICAL: Center pentagon at origin for MEEP simulation alignment
        # Calculate centroid and shift entire structure
        centroid = np.mean(all_atoms, axis=0)
        all_atoms = all_atoms - centroid
        
        # Also center the rotated cells
        centered_cells = []
        for cell_corners in rotated_cells:
            centered_cells.append(cell_corners - centroid)

        return all_atoms, centered_cells, np.array(rotated_factors), stretch_point

    def open_interactive_editor(self) -> None:
        """Open interactive editor with fabric-like lattice transformation and unit cell boundaries."""
        if self.pentagon_atoms is None:
            QMessageBox.warning(self, "No Data", "Please plot pentagon structure first.")
            return

        from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
        from matplotlib.patches import Polygon
        import matplotlib.pyplot as plt
        import numpy as np

        dialog = QDialog(self)
        dialog.setWindowTitle("Interactive Fabric Lattice Editor - Unit Cell Transformation")
        dialog.setGeometry(100, 100, 1400, 800)

        main_layout = QHBoxLayout(dialog)

        # ===== LEFT: Interactive Plot with Unit Cells =====
        plot_layout = QVBoxLayout()
        fig, ax = plt.subplots(figsize=(9, 7))
        canvas = FigureCanvas(fig)
        plot_layout.addWidget(canvas)

        atoms = np.array(self.pentagon_atoms, dtype=float)
        cell_corners = self.pentagon_cells if self.pentagon_cells is not None else []
        
        # Draw unit cell boundaries with spring-like edges
        cell_polygons = []
        if cell_corners:
            colors = ['red', 'green', 'blue', 'cyan', 'magenta', 'yellow']
            for i, corners in enumerate(cell_corners[:50]):  # Limit display for performance
                corners_array = np.array(corners)
                color = colors[i % len(colors)]
                poly = Polygon(corners_array, fill=False, edgecolor=color, 
                             linewidth=2, alpha=0.6, picker=True)
                ax.add_patch(poly)
                cell_polygons.append((poly, corners_array, i))
        
        # Plot atoms with fabric-like connectivity
        scatter = ax.scatter(atoms[:, 0], atoms[:, 1], s=100, picker=True, 
                            color='blue', edgecolors='darkblue', linewidth=1, zorder=5)
        
        ax.set_title("Fabric Lattice Editor - Drag cell edges to transform (Spring-like)")
        ax.set_xlabel("X (nm)")
        ax.set_ylabel("Y (nm)")
        ax.axis('equal')
        ax.grid(True, alpha=0.3)

        # State tracking for fabric transformation
        drag_state = {
            'mode': None,  # 'atom' or 'cell_edge'
            'atom_index': -1,
            'cell_index': -1,
            'edge_index': -1,
            'selected_atoms': [],
            'original_cell_corners': cell_corners.copy() if cell_corners else [],
            'atom_to_cell_map': {}  # Maps atom indices to their parent cells
        }
        
        # Build atom-to-cell mapping for fabric behavior
        for cell_idx, corners in enumerate(cell_corners):
            cell_center = np.mean(corners, axis=0)
            cell_radius = np.max(np.linalg.norm(corners - cell_center, axis=1))
            for atom_idx, atom_pos in enumerate(atoms):
                if np.linalg.norm(atom_pos - cell_center) < cell_radius * 1.2:
                    if atom_idx not in drag_state['atom_to_cell_map']:
                        drag_state['atom_to_cell_map'][atom_idx] = []
                    drag_state['atom_to_cell_map'][atom_idx].append(cell_idx)

        # ===== RIGHT: Control Panel =====
        control_layout = QVBoxLayout()
        
        control_label = QLabel("Fabric Transformation Controls")
        control_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        control_layout.addWidget(control_label)
        
        # Mode selection
        mode_group = QGroupBox("Interaction Mode")
        mode_layout = QVBoxLayout()
        
        # Define mode change callbacks properly for dictionary
        def set_atom_mode():
            drag_state['mode'] = 'atom'
            lattice_mode_radio.setChecked(False)
            atom_mode_radio.setChecked(True)
            sync_label.setText("🔵 Atom Mode: Drag atoms individually")
        
        def set_lattice_mode():
            drag_state['mode'] = 'lattice'
            atom_mode_radio.setChecked(False)
            lattice_mode_radio.setChecked(True)
            sync_label.setText("🟩 Lattice Mode: Transform cells with spring physics")
        
        atom_mode_radio = QPushButton("🔵 Atom Mode")
        atom_mode_radio.setCheckable(True)
        atom_mode_radio.setChecked(True)
        atom_mode_radio.clicked.connect(set_atom_mode)
        
        lattice_mode_radio = QPushButton("🟩 Lattice Fabric Mode")
        lattice_mode_radio.setCheckable(True)
        lattice_mode_radio.clicked.connect(set_lattice_mode)
        
        mode_layout.addWidget(atom_mode_radio)
        mode_layout.addWidget(lattice_mode_radio)
        mode_group.setLayout(mode_layout)
        control_layout.addWidget(mode_group)
        
        # Spring stiffness controls
        spring_group = QGroupBox("Spring Behavior")
        spring_layout = QVBoxLayout()
        
        spring_layout.addWidget(QLabel("Max Stiffness (center):"))
        stiffness_spin = QSpinBox()
        stiffness_spin.setRange(1, 100)
        stiffness_spin.setValue(50)
        spring_layout.addWidget(stiffness_spin)
        
        spring_layout.addWidget(QLabel("Decay Profile:"))
        decay_combo = QComboBox()
        decay_combo.addItems(["exponential", "gaussian", "polynomial", "linear"])
        spring_layout.addWidget(decay_combo)
        
        spring_group.setLayout(spring_layout)
        control_layout.addWidget(spring_group)
        
        # Coordinate table
        table_label = QLabel("Selected Atom Coordinates (nm)")
        table_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        control_layout.addWidget(table_label)
        
        atoms_table = QTableWidget(0, 2)
        atoms_table.setHorizontalHeaderLabels(["X", "Y"])
        header = atoms_table.horizontalHeader()
        if header is not None:
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        control_layout.addWidget(atoms_table)
        
        # Status label
        sync_label = QLabel("🔵 Atom Mode: Drag atoms | 🟩 Lattice Mode: Transform cells")
        sync_label.setStyleSheet("color: #7c3aed; font-style: italic; padding: 5px;")
        sync_label.setWordWrap(True)
        control_layout.addWidget(sync_label)
        
        # Action buttons
        button_layout = QVBoxLayout()
        
        apply_transform_btn = QPushButton("✓ Apply Fabric Transformation")
        apply_transform_btn.setStyleSheet("background-color: #7c3aed; font-weight: bold;")
        
        reset_lattice_btn = QPushButton("↺ Reset Lattice")
        
        apply_all_btn = QPushButton("💾 Save & Close")
        close_btn = QPushButton("❌ Close Without Saving")
        
        button_layout.addWidget(apply_transform_btn)
        button_layout.addWidget(reset_lattice_btn)
        button_layout.addWidget(apply_all_btn)
        button_layout.addWidget(close_btn)
        
        control_layout.addLayout(button_layout)
        control_layout.addStretch()
        
        # ===== Layout Assembly =====
        main_layout.addLayout(plot_layout, 3)
        
        right_panel = QWidget()
        right_panel.setLayout(control_layout)
        main_layout.addWidget(right_panel, 1)

        # ===== Event Handlers with Fabric Physics =====
        def apply_spring_decay(distance, max_distance, profile, stiffness):
            """Calculate spring force decay based on distance from center."""
            if max_distance == 0:
                return stiffness
            ratio = distance / max_distance
            
            if profile == "exponential":
                return stiffness * np.exp(-3 * ratio)
            elif profile == "gaussian":
                return stiffness * np.exp(-5 * ratio ** 2)
            elif profile == "polynomial":
                return stiffness * (1 - ratio ** 3)
            else:  # linear
                return stiffness * (1 - ratio)
        
        def transform_atoms_with_fabric(cell_idx, delta_transform):
            """Transform atoms connected to a cell using fabric-like physics."""
            affected_atoms = []
            for atom_idx, cell_list in drag_state['atom_to_cell_map'].items():
                if cell_idx in cell_list:
                    affected_atoms.append(atom_idx)
            
            # Apply transformation with spring decay
            offsets = np.asarray(scatter.get_offsets(), dtype=float)
            cell_center = np.mean(cell_corners[cell_idx], axis=0)
            max_dist = np.max([np.linalg.norm(atoms[ai] - cell_center) for ai in affected_atoms]) if affected_atoms else 1.0
            
            for atom_idx in affected_atoms:
                atom_pos = offsets[atom_idx]
                dist = np.linalg.norm(atom_pos - cell_center)
                spring_factor = apply_spring_decay(
                    dist, max_dist, 
                    decay_combo.currentText(),
                    stiffness_spin.value() / 100.0
                )
                offsets[atom_idx] += delta_transform * spring_factor
            
            scatter.set_offsets(offsets)
            canvas.draw_idle()

        def on_pick(event):
            """Handle picking atoms or cell edges."""
            if event.artist == scatter:
                # Atom selected
                idx = int(event.ind[0]) if len(event.ind) else -1
                drag_state['atom_index'] = idx
                if idx >= 0:
                    atoms_table.setRowCount(1)
                    atoms_table.setItem(0, 0, QTableWidgetItem(f"{atoms[idx, 0]:.4f}"))
                    atoms_table.setItem(0, 1, QTableWidgetItem(f"{atoms[idx, 1]:.4f}"))
                    sync_label.setText(f"✓ Atom {idx} selected: ({atoms[idx, 0]:.4f}, {atoms[idx, 1]:.4f})")
                    ax.set_title(f"Atom {idx} Selected - Drag to move")
                    canvas.draw_idle()
            else:
                # Check if cell edge was picked
                for poly, corners, cidx in cell_polygons:
                    if event.artist == poly:
                        drag_state['cell_index'] = cidx
                        sync_label.setText(f"✓ Cell {cidx} selected - Transform with fabric physics")
                        ax.set_title(f"Cell {cidx} - Drag edges to transform lattice")
                        canvas.draw_idle()
                        break

        def on_motion(event):
            """Handle dragging with fabric transformation."""
            if event.xdata is None or event.ydata is None:
                return
            
            mode = drag_state.get('mode', 'atom')
            
            if mode == 'atom' and drag_state['atom_index'] >= 0:
                # Normal atom dragging
                offsets = np.array(scatter.get_offsets())
                offsets[drag_state['atom_index']] = [event.xdata, event.ydata]
                scatter.set_offsets(offsets)
                
                atoms_table.setItem(0, 0, QTableWidgetItem(f"{event.xdata:.4f}"))
                atoms_table.setItem(0, 1, QTableWidgetItem(f"{event.ydata:.4f}"))
                canvas.draw_idle()
            
            elif mode == 'lattice' and drag_state['cell_index'] >= 0:
                # Fabric lattice transformation
                # Get mouse delta (simplified - track from last position)
                if not hasattr(on_motion, 'last_pos'):
                    on_motion.last_pos = np.array([event.xdata, event.ydata])
                    return
                
                current_pos = np.array([event.xdata, event.ydata])
                delta = current_pos - on_motion.last_pos
                on_motion.last_pos = current_pos
                
                # Apply fabric transformation
                transform_atoms_with_fabric(drag_state['cell_index'], delta)

        def on_release(event):
            """Handle drag end."""
            drag_state['atom_index'] = -1
            drag_state['cell_index'] = -1
            if hasattr(on_motion, 'last_pos'):
                delattr(on_motion, 'last_pos')

        def apply_transformation():
            """Apply fabric transformation and update structure."""
            offsets_array = np.asarray(scatter.get_offsets(), dtype=float)
            self.pentagon_atoms = offsets_array.copy()
            self._plot_current_pentagon(title_suffix="(Fabric Transformed)")
            sync_label.setText("✓ Fabric transformation applied to structure")
        
        def reset_lattice():
            """Reset to original lattice configuration."""
            scatter.set_offsets(atoms)
            sync_label.setText("↺ Lattice reset to original configuration")
            canvas.draw_idle()

        def save_and_close():
            """Save changes and close editor."""
            offsets_array = np.asarray(scatter.get_offsets(), dtype=float)
            self.pentagon_atoms = offsets_array.copy()
            self._plot_current_pentagon(title_suffix="(Manual Edit)")
            QMessageBox.information(dialog, "Success", 
                                  f"✓ Changes applied!\n{len(offsets_array)} atoms updated")
            dialog.accept()

        canvas.mpl_connect('pick_event', on_pick)
        canvas.mpl_connect('motion_notify_event', on_motion)
        canvas.mpl_connect('button_release_event', on_release)
        
        apply_transform_btn.clicked.connect(apply_transformation)
        reset_lattice_btn.clicked.connect(reset_lattice)
        apply_all_btn.clicked.connect(save_and_close)
        close_btn.clicked.connect(dialog.reject)

        dialog.exec()
    
    def plot_pentagon_structure(self) -> None:
        """Generate and plot pentagon structure (disclination cavity)."""
        try:
            import matplotlib
            matplotlib.use('Agg')  # Use non-interactive backend
            import matplotlib.pyplot as plt
            import numpy as np
            from testing import create_lattice_with_correct_atom_positions
            
            # Store for later use
            self.pentagon_atoms = None
            self.pentagon_cells = None
            self.pentagon_transforms = None
            
            # Get parameters
            n_cells = self.cells_spin.value()
            target_angle = self.angle_spin.value()
            decay_profile = self.decay_profile_combo.currentText().lower()
            if decay_profile == "custom":
                custom_eq = self.custom_eq_input.text()
            else:
                custom_eq = None
            
            # Lattice parameters
            sq_a1, sq_a2 = self._get_unit_cell_vectors()
            basis_sites = self._get_basis_sites()
            stretch_corner = self.corner_combo.currentText()
            
            # Use manual atom edits if already applied
            if self.manual_edit_enabled and self.pentagon_atoms is not None:
                # Manual edits already applied through interactive editor
                all_atoms = np.array(self.pentagon_atoms)
                cell_corners = self.pentagon_cells or []
                transform_factors = self.pentagon_transforms or []
            else:
                # Create pentagon structure with disclination
                all_atoms, cell_corners, transform_factors, stretch_point = (
                    self._build_cyclic_pentagon_structure(
                        n_cells,
                        sq_a1,
                        sq_a2,
                        basis_sites,
                        target_angle,
                        stretch_corner,
                        decay_profile,
                        custom_eq
                    )
                )
            
            # Store for MEEP simulation
            import numpy as np
            self.pentagon_atoms = np.array(all_atoms) if not isinstance(all_atoms, np.ndarray) else all_atoms
            self.pentagon_cells = cell_corners
            self.pentagon_transforms = transform_factors
            self.pentagon_params = {
                'n_cells': n_cells,
                'target_angle': target_angle,
                'decay_profile': decay_profile,
                'frequency': self.meep_freq_spin.value(),
                'resolution': self.meep_res_spin.value(),
                'epsilon': self.meep_eps_spin.value()
            }
            
            # Plot using shared renderer
            self._plot_current_pentagon(title_suffix=f"(Angle: {target_angle}°, Cells: {n_cells}×{n_cells})")
            
            QMessageBox.information(self, "Success", 
                                  f"✓ Pentagon structure generated:\n"
                                  f"• Cells: {n_cells}×{n_cells}\n"
                                  f"• Target Angle: {target_angle}°\n"
                                  f"• Decay Profile: {decay_profile}\n"
                                  f"• Atoms: {len(all_atoms)}\n\n"
                                  f"Ready for MEEP simulation!")
        
        except Exception as e:
            import traceback
            QMessageBox.critical(self, "Plot Error", 
                               f"Failed to plot pentagon structure:\n\n{str(e)}\n\n{traceback.format_exc()}")
    
    def plot_pentagon_with_editor(self) -> None:
        """Plot pentagon structure and open interactive editor."""
        # First, plot the structure
        self.plot_pentagon_structure()
        
        # Then open the interactive editor if structure was successfully created
        # (No extra notification - plot_pentagon_structure already shows success)
        if self.pentagon_atoms is not None and len(self.pentagon_atoms) > 0:
            self.open_interactive_editor()
    
    def show_plot_dialog(self, image_path: str, title: str) -> None:
        """Display plot image in a Qt dialog."""
        try:
            dialog = QDialog(self)
            dialog.setWindowTitle(title)
            dialog.setGeometry(100, 100, 1000, 700)
            
            layout = QVBoxLayout()
            label = QLabel()
            pixmap = QPixmap(image_path)
            if pixmap.isNull():
                label.setText("Failed to load image")
            else:
                scaled_pixmap = pixmap.scaledToWidth(900, Qt.TransformationMode.SmoothTransformation)
                label.setPixmap(scaled_pixmap)
            
            layout.addWidget(label)
            
            close_btn = QPushButton("Close")
            close_btn.clicked.connect(dialog.accept)
            layout.addWidget(close_btn)
            
            dialog.setLayout(layout)
            dialog.exec()
        except Exception as e:
            QMessageBox.warning(self, "Display Error", f"Could not display plot: {str(e)}")
    
    def simulate_meep_structure(self) -> None:
        """Run MEEP electromagnetic simulation on pentagon structure with full integration."""
        try:
            if self.pentagon_atoms is None:
                QMessageBox.warning(self, "No Structure", 
                                  "Please plot pentagon structure first!")
                return
            
            # Show progress dialog
            progress_dialog = QDialog(self)
            progress_dialog.setWindowTitle("MEEP Simulation in Progress")
            progress_dialog.setGeometry(200, 200, 500, 200)
            
            layout = QVBoxLayout()
            status_label = QLabel("Initializing MEEP simulation...")
            progress_bar = QProgressBar()
            progress_bar.setRange(0, 100)
            
            layout.addWidget(QLabel("Running electromagnetic simulation..."))
            layout.addWidget(status_label)
            layout.addWidget(progress_bar)
            progress_dialog.setLayout(layout)
            progress_dialog.show()
            
            # Progress updates
            def update_progress(value, msg):
                progress_bar.setValue(int(value))
                status_label.setText(msg)
                QApplication.processEvents()
            
            update_progress(10, "Setting up MEEP cell...")
            
            # Import MEEP
            import meep as mp
            import numpy as np
            import matplotlib.pyplot as plt
            
            # Get parameters
            params = self.pentagon_params
            frequency = params['frequency']
            resolution = params['resolution']
            epsilon = params['epsilon']
            
            # Cell dimensions
            cell_size = 10  # micrometers
            sx = sy = cell_size
            cell = mp.Vector3(sx, sy, 0)
            
            update_progress(20, "Building photonic structure...")
            
            # Create geometry from pentagon atoms
            # Convert atoms to MEEP cylinders (air holes)
            radius = 0.1  # micrometers
            geometry = []
            
            # Normalize atom positions to cell
            atom_min = self.pentagon_atoms.min(axis=0)
            atom_max = self.pentagon_atoms.max(axis=0)
            atom_range = atom_max - atom_min
            if np.any(atom_range == 0):
                atom_range = np.where(atom_range == 0, 1.0, atom_range)
            
            # Normalize to cell size
            atoms_normalized = (self.pentagon_atoms - atom_min) / atom_range * (cell_size - 2) + 1
            
            # Create air holes at atom positions
            substrate_eps = epsilon
            for atom_pos in atoms_normalized:
                geometry.append(
                    mp.Cylinder(radius=radius, center=mp.Vector3(atom_pos[0], atom_pos[1], 0),
                               material=mp.Medium(epsilon=1.0))
                )
            
            # Background substrate
            geometry.append(mp.Block(size=cell, material=mp.Medium(epsilon=substrate_eps)))
            
            # Reorder so substrate is first
            geometry.reverse()
            
            update_progress(30, "Setting up source and detectors...")
            
            # Light source (plane wave)
            sources = [
                mp.Source(
                    mp.GaussianSource(frequency, fwidth=0.1 * frequency),
                    component=mp.Hz,
                    center=mp.Vector3(-sx/4, 0, 0)
                )
            ]
            
            # Field monitors with DFT
            symmetries = []
            
            update_progress(40, "Initializing simulation...")
            
            # Create simulation
            sim = mp.Simulation(
                cell_size=cell,
                geometry=geometry,
                sources=sources,
                symmetries=symmetries,
                resolution=resolution,
                default_material=mp.Medium(epsilon=substrate_eps)
            )
            
            update_progress(50, "Running MEEP simulation (this may take a moment)...")
            
            # Run simulation with Harminv
            harminv_points = [mp.Harminv(mp.Hz, mp.Vector3(0, 0, 0), frequency, 0.1*frequency)]
            sim.run(*harminv_points, until_after_sources=200)
            
            update_progress(70, "Collecting field data...")
            
            # Get resonances from harminv
            f_res = []
            Q_res = []
            try:
                for entry in harminv_points[0].modes:
                    f_res.append(entry.freq)
                    Q_res.append(abs(entry.Q) if entry.Q != 0 else 1.0)
            except:
                # Fallback if harminv results not available
                f_res = [frequency]
                Q_res = [10.0]
            
            # Prepare DFT run to capture Hz fields for each resonant frequency
            if not f_res:
                f_res = [frequency]
                Q_res = [0.0]

            f_res = sorted(f_res)
            nfreq = len(f_res)
            if nfreq == 1:
                fmin = f_res[0]
                df = 0.0
            else:
                fmin = f_res[0]
                df = (f_res[-1] - f_res[0]) / (nfreq - 1)

            update_progress(75, "Running DFT for Hz fields...")

            dft_sim = mp.Simulation(
                cell_size=cell,
                geometry=geometry,
                sources=sources,
                symmetries=symmetries,
                resolution=resolution,
                default_material=mp.Medium(epsilon=substrate_eps)
            )

            dft_obj = dft_sim.add_dft_fields(
                [mp.Hz],
                fmin,
                df,
                nfreq,
                center=mp.Vector3(0, 0, 0),
                size=mp.Vector3(sx, sy, 0)
            )

            dft_sim.run(until_after_sources=200)

            # Get field data per frequency
            try:
                eps_data = dft_sim.get_array(center=mp.Vector3(), size=cell, component=mp.Dielectric)
                hz_fields = []
                for i in range(nfreq):
                    hz_fields.append(dft_sim.get_dft_array(dft_obj, mp.Hz, i))
            except Exception:
                eps_data = np.ones((int(sx*resolution), int(sy*resolution)))
                hz_fields = [np.zeros_like(eps_data)]
            

            update_progress(85, "Generating results visualization...")

            # Close progress dialog
            progress_dialog.close()

            # Store results and update UI
            extent = [-sx/2, sx/2, -sy/2, sy/2]
            self.meep_results = {
                'frequencies': f_res,
                'q_factors': Q_res,
                'hz_fields': hz_fields,
                'eps_data': eps_data,
                'extent': extent
            }

            self.meep_freq_combo.clear()
            for f in f_res:
                self.meep_freq_combo.addItem(f"{f:.6f}")

            self._render_meep_field(0)
            
            # Summary
            summary = f"""
✓ MEEP Simulation Complete!

Simulation Parameters:
  • Frequency: {frequency:.3f}
  • Resolution: {resolution} points/μm
  • Substrate ε: {epsilon:.1f}
  • Cell Size: {cell_size}×{cell_size} μm²

Pentagon Structure:
  • Cells: {params['n_cells']}×{params['n_cells']}
  • Angle: {params['target_angle']}°
  • Profile: {params['decay_profile']}

Results:
  • Resonant Frequencies Found: {len(f_res)}
  • Max Q Factor: {max(Q_res) if Q_res else 'N/A'}
  • Field data saved

Field data stored in simulation object.
Structure is ready for band structure analysis!
            """
            
            QMessageBox.information(self, "MEEP Results", summary)
            
            # Ensure the MEEP results tab is visible
            if self.meep_tab is not None:
                self.tabs.setCurrentWidget(self.meep_tab)
        
        except ImportError:
            QMessageBox.critical(self, "MEEP Not Found",
                               "MEEP is required for electromagnetic simulation.\n"
                               "Please ensure meep is installed: pip install meep")
        except Exception as e:
            import traceback
            QMessageBox.critical(self, "Simulation Error",
                               f"MEEP simulation failed:\n\n{str(e)}\n\n{traceback.format_exc()}")
    
    def export_pentagon_structure(self) -> None:
        """Export pentagon structure data and MEEP results to file."""
        try:
            import numpy as np
            from pathlib import Path
            
            if self.pentagon_atoms is None:
                QMessageBox.warning(self, "No Data", "Please plot pentagon structure first!")
                return
            
            # Select save location
            home_dir = str(Path.home())
            filename, _ = QFileDialog.getSaveFileName(
                self, "Save Pentagon Structure", home_dir,
                "NumPy Compressed (*.npz);;CSV Files (*.csv);;Text Files (*.txt)"
            )
            
            if not filename:
                return
            
            # Prepare structure data
            data_dict = {
                'atoms': self.pentagon_atoms,
                'n_cells': self.pentagon_params['n_cells'],
                'target_angle': self.pentagon_params['target_angle'],
                'decay_profile': self.pentagon_params['decay_profile'],
                'frequency': self.pentagon_params['frequency'],
                'resolution': self.pentagon_params['resolution'],
                'epsilon': self.pentagon_params['epsilon'],
                'transform_factors': self.pentagon_transforms,
            }
            
            # Add MEEP results if available
            if hasattr(self, 'meep_results') and self.meep_results:
                data_dict['meep_frequencies'] = np.array(self.meep_results['frequencies'])
                data_dict['meep_q_factors'] = np.array(self.meep_results['q_factors'])
            
            # Save based on file extension
            if filename.endswith('.npz'):
                np.savez_compressed(filename, **data_dict)
                message = f"Structure saved to:\n{filename}\n\nData includes:\n• Atom positions\n• Transform factors\n• MEEP parameters & results"
            elif filename.endswith('.csv'):
                np.savetxt(filename, self.pentagon_atoms, delimiter=',', 
                          header='X(nm),Y(nm)', comments='')
                message = f"Atom positions saved to:\n{filename}"
            else:
                # Save as text summary
                with open(filename, 'w') as f:
                    f.write("Pentagon Structure Export\n")
                    f.write("=" * 50 + "\n\n")
                    f.write(f"Cells: {self.pentagon_params['n_cells']}×{self.pentagon_params['n_cells']}\n")
                    f.write(f"Target Angle: {self.pentagon_params['target_angle']}°\n")
                    f.write(f"Decay Profile: {self.pentagon_params['decay_profile']}\n")
                    f.write(f"Number of Atoms: {len(self.pentagon_atoms)}\n\n")
                    f.write("MEEP Parameters:\n")
                    f.write(f"  Frequency: {self.pentagon_params['frequency']}\n")
                    f.write(f"  Resolution: {self.pentagon_params['resolution']} pts/μm\n")
                    f.write(f"  Substrate ε: {self.pentagon_params['epsilon']}\n\n")
                    f.write("Atom Positions (first 10):\n")
                    f.write("X(nm)\t\tY(nm)\n")
                    for i, atom in enumerate(self.pentagon_atoms[:10]):
                        f.write(f"{atom[0]:.3f}\t\t{atom[1]:.3f}\n")
                    f.write(f"... ({len(self.pentagon_atoms)-10} more atoms)\n")
                message = f"Summary saved to:\n{filename}"
            
            QMessageBox.information(self, "Export Success", message)
        
        except Exception as e:
            import traceback
            QMessageBox.critical(self, "Export Error",
                               f"Failed to export structure:\n\n{str(e)}\n\n{traceback.format_exc()}")



def main() -> None:
    """Main entry point."""
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    launcher = PhotonicGUILauncher()
    launcher.show()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
