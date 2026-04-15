#!/home/shaukat/mambaforge/envs/pymeep_env/bin/python
import kivy
kivy.require("2.1.0")

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.image import Image
from kivy.graphics.texture import Texture
from kivy.graphics import Color, RoundedRectangle
from kivy.core.window import Window
from kivy.uix.popup import Popup

import traceback
import numpy as np
import ezdxf
import os
import re

os.environ.setdefault("MPLBACKEND", "Agg")

from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from matplotlib.patches import Circle

class PlotWidget(Image):
    def plot(self, coords, radius=0.1, plot_limits=None, stage_data=None, units="um"):
        if coords is None or len(coords) == 0:
            return

        fig = Figure(figsize=(6.5, 6.5), dpi=100, facecolor='#222222')

        draw_radius = max(float(radius), 1e-9)

        def _resolve_limits(reference_coords):
            if plot_limits is not None:
                x_min, x_max, y_min, y_max = plot_limits
            else:
                x_min = float(np.min(reference_coords[:, 0]) - draw_radius)
                x_max = float(np.max(reference_coords[:, 0]) + draw_radius)
                y_min = float(np.min(reference_coords[:, 1]) - draw_radius)
                y_max = float(np.max(reference_coords[:, 1]) + draw_radius)

            span_x = max(x_max - x_min, 1e-6)
            span_y = max(y_max - y_min, 1e-6)
            pad = 0.05 * max(span_x, span_y)
            return (x_min - pad, x_max + pad, y_min - pad, y_max + pad)

        if stage_data:
            stages = [
                ("1) Initial", np.array(stage_data.get("initial", []), dtype=float), '#4aa8ff'),
                ("2) Grouped", np.array(stage_data.get("grouped", []), dtype=float), '#ffb347'),
                ("3) Transformed", np.array(stage_data.get("transformed", []), dtype=float), '#59d98e'),
                ("4) Final", np.array(stage_data.get("final", coords), dtype=float), '#00d4ff'),
            ]

            ref = np.array(stage_data.get("final", coords), dtype=float)
            if ref.size == 0:
                ref = np.array(coords, dtype=float)
            x0, x1, y0, y1 = _resolve_limits(ref)

            axes = [fig.add_subplot(221), fig.add_subplot(222), fig.add_subplot(223), fig.add_subplot(224)]
            for ax, (title, pts, color) in zip(axes, stages):
                ax.set_facecolor('#111111')
                if pts.size > 0 and pts.ndim == 2 and pts.shape[1] == 2:
                    for x, y in pts:
                        circle = Circle(
                            (float(x), float(y)),
                            draw_radius,
                            facecolor=color,
                            edgecolor='white',
                            linewidth=0.4,
                            alpha=0.9,
                        )
                        ax.add_patch(circle)
                ax.set_xlim(x0, x1)
                ax.set_ylim(y0, y1)
                ax.set_aspect("equal")
                ax.tick_params(colors='white', labelsize=8)
                ax.title.set_color('white')
                ax.set_title(title, fontsize=10)
                ax.set_xlabel(f"x ({units})", color='white', fontsize=8)
                ax.set_ylabel(f"y ({units})", color='white', fontsize=8)
            fig.suptitle(f"Photonic Structure Preview Pipeline [{units}]", color='white', fontsize=11)
            fig.subplots_adjust(wspace=0.16, hspace=0.22, top=0.92)
        else:
            ax = fig.add_subplot(111)
            ax.set_facecolor('#111111')

            for x, y in coords:
                circle = Circle(
                    (float(x), float(y)),
                    draw_radius,
                    facecolor='#00d4ff',
                    edgecolor='white',
                    linewidth=0.5,
                    alpha=0.9,
                )
                ax.add_patch(circle)

            x0, x1, y0, y1 = _resolve_limits(coords)
            ax.set_xlim(x0, x1)
            ax.set_ylim(y0, y1)
            ax.set_aspect("equal")
            ax.tick_params(colors='white')
            ax.title.set_color('white')
            ax.set_title(f"Photonic Structure Preview [{units}]")
            ax.set_xlabel(f"x ({units})", color='white')
            ax.set_ylabel(f"y ({units})", color='white')

        canvas = FigureCanvasAgg(fig)
        canvas.draw()
        w, h = canvas.get_width_height()
        
        # FIX: Convert the buffer to a flat byte string
        buf = canvas.buffer_rgba()
        flat_buf = np.array(buf).tobytes() # Flatten the 3D array into a 1D byte string

        texture = Texture.create(size=(w, h), colorfmt='rgba')
        # Use the flattened buffer here
        texture.blit_buffer(flat_buf, colorfmt='rgba', bufferfmt='ubyte')
        texture.flip_vertical()
        self.texture = texture

class ThesisDXFApp(App):
    def _apply_rounded_background(self, widget, radius=14, color=(0.12, 0.12, 0.12, 1)):
        with widget.canvas.before:
            widget._rounded_bg_color = Color(*color)
            widget._rounded_bg_rect = RoundedRectangle(
                pos=widget.pos,
                size=widget.size,
                radius=[radius, radius, radius, radius],
            )

        def _update_rect(instance, value):
            instance._rounded_bg_rect.pos = instance.pos
            instance._rounded_bg_rect.size = instance.size

        widget.bind(pos=_update_rect, size=_update_rect)

    def _style_button(self, button, color, radius=12):
        button.background_normal = ""
        button.background_down = ""
        button.background_color = (0, 0, 0, 0)
        self._apply_rounded_background(button, radius=radius, color=color)

    def build(self):
        self.title = "Structure Designer: Unit-Center Volterra to DXF"
        self.coords = None
        self.radius = 0.1
        self.units = "um"
        self.preview_limits = None

        # Root Layout
        root = BoxLayout(orientation="vertical", padding=10, spacing=10)

        # Top Section: Editor and Preview
        main_area = BoxLayout(orientation="horizontal", spacing=15)

        # Left Side: Code Editor
        editor_layout = BoxLayout(orientation="vertical", size_hint_x=0.45, spacing=5)
        editor_label = Label(text="Python Structure Script", size_hint_y=None, height=30, bold=True)
        
        # Default starter code for your thesis
        starter_code = (
            "# =================================================================\n"
            "# CELL 1: 2x2-Cell Shared-Corner Grouping -> Volterra on Centers\n"
            "# =================================================================\n\n"
            "import meep as mp\n"
            "import numpy as np\n"
            "import matplotlib.pyplot as plt\n\n"
            "# -----------------------------\n"
            "# PARAMETERS (edit freely)\n"
            "# -----------------------------\n"
            "a = 1.0\n"
            "r_hole = 0.1 * a\n"
            "offset = 0.35 * a\n"
            "Rmax = 3\n"
            "cavity_radius = 3.35\n"
            "cell_size = 7\n"
            "units = 'um'  # default length unit (micrometer)\n"
            "n = 6\n"
            "c = 0.4\n"
            "d = 0.6   # angular displacement strength (0.0 to 1.0)\n"
            "s = 1     # parity selector (0 or 1)\n\n"
            "# Transformation origin mode: 'center', 'edge', 'corner'\n"
            "origin_mode = 'center'\n"
            "origin_map = {\n"
            "    'center': np.array([0.0, 0.0]),\n"
            "    'edge': np.array([0.5 * a, 0.0]),\n"
            "    'corner': np.array([0.5 * a, 0.5 * a]),\n"
            "}\n"
            "origin = origin_map.get(origin_mode, origin_map['center'])\n\n"
            "# Original C4 hole motif inside one unit cell\n"
            "c4_basis = np.array([\n"
            "    [+offset, +offset],\n"
            "    [+offset, -offset],\n"
            "    [-offset, +offset],\n"
            "    [-offset, -offset],\n"
            "], dtype=float)\n\n"
            "# Stage-1 plot data: initial full hole structure (before grouping)\n"
            "initial_coords = []\n"
            "for i0 in range(-Rmax, Rmax + 1):\n"
            "    for j0 in range(-Rmax, Rmax + 1):\n"
            "        uc0 = np.array([i0 * a, j0 * a])\n"
            "        for hole_offset in c4_basis:\n"
            "            p = uc0 + hole_offset\n"
            "            if np.linalg.norm(p - origin) < cavity_radius:\n"
            "                initial_coords.append((p[0], p[1]))\n"
            "initial_coords = np.array(initial_coords, dtype=float)\n"
            "initial_coords = np.unique(np.round(initial_coords, 6), axis=0)\n\n"
            "# ----------------------------------------------------------------------\n"
            "# 1) Build groups from shared corners of 2x2 neighboring unit cells\n"
            "#    Group = 4 holes from 4 different cells around one grid vertex\n"
            "# ----------------------------------------------------------------------\n"
            "group_centers = []\n"
            "\n"
            "# Distance from the 2x2 block center to each grouped hole\n"
            "delta_corner = 0.5 * a - offset\n"
            "corner_basis = np.array([\n"
            "    [-delta_corner, -delta_corner],\n"
            "    [+delta_corner, -delta_corner],\n"
            "    [-delta_corner, +delta_corner],\n"
            "    [+delta_corner, +delta_corner],\n"
            "], dtype=float)\n\n"
            "for i in range(-Rmax, Rmax):\n"
            "    for j in range(-Rmax, Rmax):\n"
            "        # 2x2 block cells: (i,j), (i+1,j), (i,j+1), (i+1,j+1)\n"
            "        # Shared-corner quartet (one hole from each different cell):\n"
            "        h1 = np.array([i * a + offset,     j * a + offset    ])      # cell (i, j)\n"
            "        h2 = np.array([(i + 1) * a - offset, j * a + offset  ])      # cell (i+1, j)\n"
            "        h3 = np.array([i * a + offset,     (j + 1) * a - offset])    # cell (i, j+1)\n"
            "        h4 = np.array([(i + 1) * a - offset, (j + 1) * a - offset])  # cell (i+1, j+1)\n"
            "\n"
            "        holes = np.vstack([h1, h2, h3, h4])\n"
            "        center = np.mean(holes, axis=0)\n"
            "\n"
            "        # Keep groups whose 4 corners stay within cavity\n"
            "        hole_r = np.linalg.norm(holes - origin, axis=1)\n"
            "        if np.all(hole_r < cavity_radius):\n"
            "            group_centers.append(center)\n"
            "\n"
            "group_centers = np.array(group_centers, dtype=float)\n"
            "if group_centers.size == 0:\n"
            "    raise ValueError('No valid shared-corner 4-hole groups found.')\n\n"
            "# ----------------------------------------------------------------------\n"
            "# 2) Apply Volterra angular process on these group centers\n"
            "# ----------------------------------------------------------------------\n"
            "extended_points = []\n"
            "theta_extension_factor = n / 4.0\n"
            "for gc in group_centers:\n"
            "    local = gc - origin\n"
            "    r = np.linalg.norm(local)\n"
            "    theta = np.arctan2(local[1], local[0])\n"
            "    for k in range(int(np.ceil(theta_extension_factor))):\n"
            "        theta_ext = theta + 2.0 * np.pi * k\n"
            "        if theta_ext < 2.0 * np.pi * theta_extension_factor:\n"
            "            extended_points.append((r, theta_ext))\n\n"
            "transformed_centers = []\n"
            "transformed_rotations = []\n"
            "alpha = 4.0 / n\n"
            "for r, theta in extended_points:\n"
            "    theta_new = alpha * theta\n"
            "    x_new = r * np.cos(theta_new) + origin[0]\n"
            "    y_new = r * np.sin(theta_new) + origin[1]\n"
            "    if r < cavity_radius - np.sqrt(2.0) * abs(delta_corner):\n"
            "        transformed_centers.append((x_new, y_new))\n\n"
            "        transformed_rotations.append(theta_new - theta)\n\n"
            "transformed_centers = np.array(transformed_centers, dtype=float).reshape(-1, 2)\n"
            "transformed_rotations = np.array(transformed_rotations, dtype=float).reshape(-1)\n"
            "rounded_centers = np.round(transformed_centers, 6)\n"
            "_, unique_indices = np.unique(rounded_centers, axis=0, return_index=True)\n"
            "unique_indices = np.sort(unique_indices)\n"
            "transformed_centers = transformed_centers[unique_indices]\n"
            "transformed_rotations = transformed_rotations[unique_indices]\n\n"
            "# Nearest n centers: radial contraction\n"
            "if transformed_centers.shape[0] >= n:\n"
            "    local_tc = transformed_centers - origin\n"
            "    distances = np.linalg.norm(local_tc, axis=1)\n"
            "    nearest_indices = np.argsort(distances)[:n]\n"
            "    for idx in nearest_indices:\n"
            "        r = distances[idx]\n"
            "        theta = np.arctan2(local_tc[idx, 1], local_tc[idx, 0])\n"
            "        r_new = (1.0 - c) * r\n"
            "        transformed_centers[idx, 0] = r_new * np.cos(theta) + origin[0]\n"
            "        transformed_centers[idx, 1] = r_new * np.sin(theta) + origin[1]\n\n"
            "# Next 2*n centers: angular displacement\n"
            "if transformed_centers.shape[0] >= 3 * n:\n"
            "    local_tc = transformed_centers - origin\n"
            "    distances = np.linalg.norm(local_tc, axis=1)\n"
            "    sorted_idx = np.argsort(distances)\n"
            "    second_group_indices = sorted_idx[n:3 * n]\n"
            "    ring_points = local_tc[second_group_indices]\n"
            "    ring_theta = np.arctan2(ring_points[:, 1], ring_points[:, 0])\n"
            "    ring_r = np.linalg.norm(ring_points, axis=1)\n"
            "    theta_order = np.argsort(ring_theta)\n"
            "    delta_theta = d * (np.pi / (2.0 * n))\n"
            "    s = int(s) % 2\n\n"
            "    for i, local_idx in enumerate(theta_order):\n"
            "        global_idx = second_group_indices[local_idx]\n"
            "        theta = ring_theta[local_idx]\n"
            "        r = ring_r[local_idx]\n"
            "        theta_new = theta + ((-1) ** (i + s)) * delta_theta\n"
            "        transformed_centers[global_idx, 0] = r * np.cos(theta_new) + origin[0]\n"
            "        transformed_centers[global_idx, 1] = r * np.sin(theta_new) + origin[1]\n\n"
            "        transformed_rotations[global_idx] += theta_new - theta\n\n"
            "# ----------------------------------------------------------------------\n"
            "# 3) Reconstruct 4 shared-corner holes around each transformed center\n"
            "#    using the stored relative rotation of each transformed group\n"
            "# ----------------------------------------------------------------------\n"
            "def rotate_offsets(points, angle):\n"
            "    c = np.cos(angle)\n"
            "    s = np.sin(angle)\n"
            "    rot = np.array([[c, -s], [s, c]], dtype=float)\n"
            "    return points @ rot.T\n\n"
            "coords = []\n"
            "for center, rotation in zip(transformed_centers, transformed_rotations):\n"
            "    holes = center + rotate_offsets(corner_basis, rotation)\n"
            "    for x, y in holes:\n"
            "        r = np.linalg.norm(np.array([x, y]) - origin)\n"
            "        if r < cavity_radius:\n"
            "            coords.append((x, y))\n\n"
            "coords = np.array(coords, dtype=float).reshape(-1, 2)\n"
            "coords = np.unique(np.round(coords, 6), axis=0)\n\n"
            "geometry_cN = [\n"
            "    mp.Cylinder(\n"
            "        r_hole,\n"
            "        height=mp.inf,\n"
            "        center=mp.Vector3(x, y),\n"
            "        material=mp.Medium(epsilon=1),\n"
            "    )\n"
            "    for (x, y) in coords\n"
            "]\n\n"
            "# ----------------------------------------------------------------------\n"
            "# Stage plots\n"
            "# 1) Initial structure\n"
            "# 2) Grouped representation (centers only)\n"
            "# 3) After transformation before ungrouping (transformed centers)\n"
            "# 4) Final after ungrouping (reconstructed holes)\n"
            "# ----------------------------------------------------------------------\n"
            "fig, axes = plt.subplots(2, 2, figsize=(12, 10))\n"
            "ax1, ax2, ax3, ax4 = axes.flatten()\n"
            "\n"
            "if initial_coords.size > 0:\n"
            "    ax1.scatter(initial_coords[:, 0], initial_coords[:, 1], s=18, c='tab:blue')\n"
            "ax1.set_title('1) Initial structure (all holes)')\n"
            "\n"
            "if group_centers.size > 0:\n"
            "    ax2.scatter(group_centers[:, 0], group_centers[:, 1], s=24, c='tab:orange')\n"
            "ax2.set_title('2) After grouping (centers only)')\n"
            "\n"
            "if transformed_centers.size > 0:\n"
            "    ax3.scatter(transformed_centers[:, 0], transformed_centers[:, 1], s=24, c='tab:green')\n"
            "ax3.set_title('3) After transform (before ungrouping)')\n"
            "\n"
            "if coords.size > 0:\n"
            "    ax4.scatter(coords[:, 0], coords[:, 1], s=18, c='tab:red')\n"
            "ax4.set_title('4) Final after ungrouping')\n"
            "\n"
            "for ax in [ax1, ax2, ax3, ax4]:\n"
            "    ax.set_aspect('equal')\n"
            "    ax.set_xlim(-cell_size / 2, cell_size / 2)\n"
            "    ax.set_ylim(-cell_size / 2, cell_size / 2)\n"
            "    ax.set_xlabel(f'x ({units})')\n"
            "    ax.set_ylabel(f'y ({units})')\n"
            "    ax.grid(alpha=0.2)\n"
            "\n"
            "fig.suptitle(f'Shared-corner 4-cell C{n} pipeline [{units}] ({origin_mode}-origin, c={c}, d={d})')\n"
            "plt.tight_layout()\n"
            "plt.show()\n"
            "# GUI accepts either 'coords' or 'geometry_cN'\n"
        )
        
        self.code_input = TextInput(
            text=starter_code,
            multiline=True,
            readonly=False,
            background_color=(0.08, 0.08, 0.08, 1),
            foreground_color=(1, 1, 1, 1),
            cursor_color=(1, 1, 1, 1),
            font_size=14,
            tab_width=4,
            write_tab=True,
            use_bubble=False,
            use_handles=False,
            padding=(10, 10, 10, 10),
        )

        self._apply_rounded_background(editor_layout, radius=16, color=(0.14, 0.14, 0.14, 1))
        editor_layout.add_widget(editor_label)
        editor_layout.add_widget(self.code_input)

        # Right Side: Preview
        preview_layout = BoxLayout(orientation="vertical", size_hint_x=0.55, spacing=5)
        preview_label = Label(text="Live Preview", size_hint_y=None, height=30, bold=True)
        self.plot_widget = PlotWidget()
        self._apply_rounded_background(self.plot_widget, radius=12, color=(0.08, 0.08, 0.08, 1))
        self._apply_rounded_background(preview_layout, radius=16, color=(0.14, 0.14, 0.14, 1))
        preview_layout.add_widget(preview_label)
        preview_layout.add_widget(self.plot_widget)

        main_area.add_widget(editor_layout)
        main_area.add_widget(preview_layout)

        # Bottom Section: Buttons
        controls = BoxLayout(size_hint_y=None, height=60, spacing=15)
        self._apply_rounded_background(controls, radius=14, color=(0.14, 0.14, 0.14, 1))
        
        edit_btn = Button(text="Edit", background_color=(0.35, 0.35, 0.35, 1))
        origin_toggle_btn = Button(text="Origin: Center", background_color=(0.35, 0.35, 0.35, 1))
        run_btn = Button(text="Run Script & Preview", background_color=(0.1, 0.7, 0.9, 1))
        export_btn = Button(text="Export as DXF", background_color=(1, 0.5, 0, 1))

        self._style_button(edit_btn, color=(0.35, 0.35, 0.35, 1), radius=12)
        self._style_button(origin_toggle_btn, color=(0.35, 0.35, 0.35, 1), radius=12)
        self._style_button(run_btn, color=(0.1, 0.7, 0.9, 1), radius=12)
        self._style_button(export_btn, color=(1.0, 0.5, 0.0, 1), radius=12)

        self.origin_mode = "center"
        self.origin_toggle_btn = origin_toggle_btn
        
        edit_btn.bind(on_press=self.enable_edit_mode)
        origin_toggle_btn.bind(on_press=self.toggle_origin_mode)
        run_btn.bind(on_press=self.execute_script)
        export_btn.bind(on_press=self.export_dxf)

        controls.add_widget(edit_btn)
        controls.add_widget(origin_toggle_btn)
        controls.add_widget(run_btn)
        controls.add_widget(export_btn)

        root.add_widget(main_area)
        root.add_widget(controls)
        self._apply_rounded_background(root, radius=18, color=(0.10, 0.10, 0.10, 1))
        self._apply_rounded_background(main_area, radius=16, color=(0.12, 0.12, 0.12, 1))

        return root

    def enable_edit_mode(self, instance):
        self.code_input.readonly = False
        self.code_input.focus = True

    def _set_origin_mode_in_editor(self, mode):
        code = self.code_input.text
        pattern = r"origin_mode\s*=\s*['\"](?:center|corner|edge)['\"]"
        replacement = f"origin_mode = '{mode}'"

        if re.search(pattern, code):
            self.code_input.text = re.sub(pattern, replacement, code, count=1)
            return

        marker = "s = 1      # parity selector (0 or 1)"
        insertion = "\norigin_mode = '" + mode + "'\n"
        if marker in code:
            self.code_input.text = code.replace(marker, marker + insertion, 1)
        else:
            self.code_input.text = replacement + "\n" + code

    def toggle_origin_mode(self, instance):
        self.origin_mode = "corner" if self.origin_mode == "center" else "center"
        self.origin_toggle_btn.text = f"Origin: {self.origin_mode.capitalize()}"
        self._set_origin_mode_in_editor(self.origin_mode)

    def _extract_coords_from_geometry(self, geometry_list):
        return np.array([[obj.center.x, obj.center.y] for obj in geometry_list], dtype=float)

    def _resolve_preview_limits(self, namespace):
        if "cell_size" in namespace:
            half = float(namespace["cell_size"]) / 2.0
            return (-half, half, -half, half)
        if "cavity_radius" in namespace:
            r = float(namespace["cavity_radius"])
            return (-r, r, -r, r)
        return None

    def _normalize_units(self, units_value):
        text = str(units_value or "um").strip().lower()
        aliases = {
            "micron": "um",
            "microns": "um",
            "micrometer": "um",
            "micrometers": "um",
            "μm": "um",
        }
        return aliases.get(text, text)

    def _dxf_insunits_code(self, units_value):
        units_key = self._normalize_units(units_value)
        code_map = {
            "unitless": 0,
            "in": 1,
            "inch": 1,
            "ft": 2,
            "foot": 2,
            "feet": 2,
            "mi": 3,
            "mile": 3,
            "mm": 4,
            "cm": 5,
            "m": 6,
            "km": 7,
            "um": 13,
            "nm": 14,
        }
        return code_map.get(units_key, 13)

    def execute_script(self, instance):
        try:
            # Prepare namespace
            namespace = {"np": np, "numpy": np}
            
            # Get code directly from the text box
            code = self.code_input.text
            exec(code, namespace)

            if "coords" in namespace:
                self.coords = np.array(namespace["coords"], dtype=float)
            elif "geometry_cN" in namespace:
                geom = namespace["geometry_cN"]
                self.coords = self._extract_coords_from_geometry(geom)
            else:
                raise ValueError("Script must define 'coords' or 'geometry_cN'")

            if self.coords.ndim != 2 or self.coords.shape[1] != 2:
                raise ValueError("'coords' must be a 2D array/list with shape (N, 2)")

            if "r_hole" in namespace:
                self.radius = float(namespace["r_hole"])
            elif "geometry_cN" in namespace and len(namespace["geometry_cN"]) > 0 and hasattr(namespace["geometry_cN"][0], "radius"):
                self.radius = float(namespace["geometry_cN"][0].radius)

            self.units = self._normalize_units(namespace.get("units", self.units))

            self.preview_limits = self._resolve_preview_limits(namespace)

            stage_data = None
            if any(k in namespace for k in ("initial_coords", "group_centers", "transformed_centers")):
                stage_data = {
                    "initial": namespace.get("initial_coords", []),
                    "grouped": namespace.get("group_centers", []),
                    "transformed": namespace.get("transformed_centers", []),
                    "final": namespace.get("coords", self.coords),
                }

            self.plot_widget.plot(
                self.coords,
                radius=self.radius,
                plot_limits=self.preview_limits,
                stage_data=stage_data,
                units=self.units,
            )
        except Exception:
            self.show_error(traceback.format_exc())

    def export_dxf(self, instance):
        if self.coords is None:
            self.show_error("No coordinates found. Click 'Run Script' first.")
            return

        content = BoxLayout(orientation="vertical", spacing=10, padding=10)
        prompt = Label(text="Enter DXF file name:", size_hint_y=None, height=30, color=(1, 1, 1, 1))
        file_input = TextInput(
            text="structure_output.dxf",
            multiline=False,
            size_hint_y=None,
            height=45,
            background_normal="",
            background_active="",
            background_color=(0.15, 0.15, 0.15, 1),
            foreground_color=(1, 1, 1, 1),
            cursor_color=(1, 1, 1, 1),
            padding=(10, 10, 10, 10),
        )

        btn_row = BoxLayout(size_hint_y=None, height=45, spacing=10)
        save_btn = Button(text="Save")
        cancel_btn = Button(text="Cancel")
        self._style_button(save_btn, color=(0.15, 0.65, 0.25, 1), radius=10)
        self._style_button(cancel_btn, color=(0.45, 0.45, 0.45, 1), radius=10)

        btn_row.add_widget(save_btn)
        btn_row.add_widget(cancel_btn)

        content.add_widget(prompt)
        content.add_widget(file_input)
        content.add_widget(btn_row)

        popup = Popup(title="Save DXF As", content=content, size_hint=(0.55, 0.35), auto_dismiss=False)

        def do_save(_):
            self._save_dxf_with_name(file_input.text, popup)

        save_btn.bind(on_press=do_save)
        cancel_btn.bind(on_press=lambda _: popup.dismiss())

        popup.open()

    def _save_dxf_with_name(self, file_name, popup):
        name = (file_name or "").strip()
        if not name:
            self.show_error("Please enter a file name.")
            return

        if not name.lower().endswith(".dxf"):
            name = f"{name}.dxf"

        try:
            doc = ezdxf.new('R2010')
            doc.header["$INSUNITS"] = self._dxf_insunits_code(self.units)
            msp = doc.modelspace()
            for pt in self.coords:
                msp.add_circle((float(pt[0]), float(pt[1])), radius=self.radius)
            doc.saveas(name)
            popup.dismiss()
            self.show_error(
                f"SUCCESS!\nSaved to: {os.path.abspath(name)}\nUnits: {self.units}"
            )
        except Exception as e:
            self.show_error(str(e))

    def show_error(self, msg):
        popup = Popup(title="Status/Error Log", content=Label(text=msg), size_hint=(0.8, 0.6))
        popup.open()

if __name__ == "__main__":
    Window.size = (1200, 800)
    ThesisDXFApp().run()