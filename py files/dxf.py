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
    def plot(self, coords, radius=0.1, plot_limits=None):
        if coords is None or len(coords) == 0:
            return

        fig = Figure(figsize=(5, 5), dpi=100, facecolor='#222222')
        ax = fig.add_subplot(111)
        ax.set_facecolor('#111111')

        draw_radius = max(float(radius), 1e-9)
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

        if plot_limits is not None:
            x_min, x_max, y_min, y_max = plot_limits
        else:
            x_min = float(np.min(coords[:, 0]) - draw_radius)
            x_max = float(np.max(coords[:, 0]) + draw_radius)
            y_min = float(np.min(coords[:, 1]) - draw_radius)
            y_max = float(np.max(coords[:, 1]) + draw_radius)

        span_x = max(x_max - x_min, 1e-6)
        span_y = max(y_max - y_min, 1e-6)
        pad = 0.05 * max(span_x, span_y)
        ax.set_xlim(x_min - pad, x_max + pad)
        ax.set_ylim(y_min - pad, y_max + pad)

        ax.set_aspect("equal")
        ax.tick_params(colors='white')
        ax.title.set_color('white')
        ax.set_title("Photonic Structure Preview")

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
        self.title = "Structure Designer: Script-to-DXF"
        self.coords = None
        self.radius = 0.1
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
            "# ==========================================\n"
            "# CELL 1: Proper Volterra C4 → Cn (No Gap)\n"
            "# ==========================================\n\n"
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
            "n = 6\n"
            "c = 0.4\n\n"
            "d = 0.6   # angular displacement strength (0.0 to 1.0)\n"
            "s = 1      # parity selector (0 or 1)\n\n"
            "# Transformation origin mode: 'center', 'edge', 'corner'\n"
            "origin_mode = 'center'\n"
            "origin_map = {\n"
            "    'center': np.array([0.0, 0.0]),\n"
            "    'edge': np.array([0.5 * a, 0.0]),\n"
            "    'corner': np.array([0.5 * a, 0.5 * a]),\n"
            "}\n"
            "origin = origin_map.get(origin_mode, origin_map['center'])\n\n"
            "# -----------------------------\n"
            "# C4 basis\n"
            "# -----------------------------\n"
            "c4_basis = [\n"
            "    (+offset, +offset),\n"
            "    (+offset, -offset),\n"
            "    (-offset, +offset),\n"
            "    (-offset, -offset),\n"
            "]\n\n"
            "# -----------------------------\n"
            "# Build base C4 lattice\n"
            "# -----------------------------\n"
            "base_points = []\n"
            "for i in range(-Rmax, Rmax+1):\n"
            "    for j in range(-Rmax, Rmax+1):\n"
            "        for dx, dy in c4_basis:\n"
            "            x = i*a + dx\n"
            "            y = j*a + dy\n"
            "            x_local = x - origin[0]\n"
            "            y_local = y - origin[1]\n"
            "            r = np.sqrt(x_local**2 + y_local**2)\n"
            "            if r < cavity_radius:\n"
            "                base_points.append((x, y))\n\n"
            "base_points = np.array(base_points)\n"
            "extended_points = []\n"
            "theta_extension_factor = n / 4\n\n"
            "for x, y in base_points:\n"
            "    x_local = x - origin[0]\n"
            "    y_local = y - origin[1]\n"
            "    r = np.sqrt(x_local**2 + y_local**2)\n"
            "    theta = np.arctan2(y_local, x_local)\n"
            "    for k in range(int(np.ceil(theta_extension_factor))):\n"
            "        theta_ext = theta + 2*np.pi*k\n"
            "        if theta_ext < 2*np.pi * theta_extension_factor:\n"
            "            extended_points.append((r, theta_ext))\n\n"
            "coords = []\n"
            "alpha = 4 / n\n"
            "for r, theta in extended_points:\n"
            "    theta_new = alpha * theta\n"
            "    x_new = r*np.cos(theta_new) + origin[0]\n"
            "    y_new = r*np.sin(theta_new) + origin[1]\n"
            "    if r < cavity_radius:\n"
            "        coords.append((x_new, y_new))\n\n"
            "coords = np.array(coords)\n"
            "coords = np.unique(np.round(coords, 6), axis=0)\n\n"
            "if coords.shape[0] >= n:\n"
            "    local_coords = coords - origin\n"
            "    distances = np.linalg.norm(local_coords, axis=1)\n"
            "    nearest_indices = np.argsort(distances)[:n]\n"
            "    for idx in nearest_indices:\n"
            "        r = distances[idx]\n"
            "        theta = np.arctan2(local_coords[idx,1], local_coords[idx,0])\n"
            "        r_new = (1 - c) * r\n"
            "        coords[idx,0] = r_new*np.cos(theta) + origin[0]\n"
            "        coords[idx,1] = r_new*np.sin(theta) + origin[1]\n\n"
            "# -----------------------------\n"
            "# Second-nearest group angular displacement\n"
            "# Take 2*n holes after excluding nearest n\n"
            "# -----------------------------\n"
            "if coords.shape[0] >= 3*n:\n"
            "    local_coords = coords - origin\n"
            "    distances = np.linalg.norm(local_coords, axis=1)\n"
            "    sorted_idx = np.argsort(distances)\n"
            "    second_group_indices = sorted_idx[n:3*n]\n\n"
            "    ring_points = local_coords[second_group_indices]\n"
            "    ring_theta = np.arctan2(ring_points[:,1], ring_points[:,0])\n"
            "    ring_r = np.linalg.norm(ring_points, axis=1)\n\n"
            "    theta_order = np.argsort(ring_theta)\n"
            "    delta_theta = d * (np.pi / (2*n))\n"
            "    s = int(s) % 2\n\n"
            "    for i, local_idx in enumerate(theta_order):\n"
            "        global_idx = second_group_indices[local_idx]\n"
            "        theta = ring_theta[local_idx]\n"
            "        r = ring_r[local_idx]\n"
            "        theta_new = theta + ((-1)**(i + s)) * delta_theta\n"
            "        coords[global_idx,0] = r*np.cos(theta_new) + origin[0]\n"
            "        coords[global_idx,1] = r*np.sin(theta_new) + origin[1]\n\n"
            "# Optional: also expose Meep geometry\n"
            "geometry_cN = [\n"
            "    mp.Cylinder(\n"
            "        r_hole,\n"
            "        height=mp.inf,\n"
            "        center=mp.Vector3(x, y),\n"
            "        material=mp.Medium(epsilon=1),\n"
            "    )\n"
            "    for (x, y) in coords\n"
            "]\n\n"
            "plt.figure(figsize=(6,6))\n"
            "plt.scatter(coords[:,0], coords[:,1], s=30)\n"
            "plt.gca().set_aspect('equal')\n"
            "plt.title(f'C{n} Disclination ({origin_mode}-origin, c={c}, d={d})')\n"
            "plt.xlim(-cell_size/2, cell_size/2)\n"
            "plt.ylim(-cell_size/2, cell_size/2)\n"
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

            self.preview_limits = self._resolve_preview_limits(namespace)

            self.plot_widget.plot(self.coords, radius=self.radius, plot_limits=self.preview_limits)
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
            msp = doc.modelspace()
            for pt in self.coords:
                msp.add_circle((float(pt[0]), float(pt[1])), radius=self.radius)
            doc.saveas(name)
            popup.dismiss()
            self.show_error(f"SUCCESS!\nSaved to: {os.path.abspath(name)}")
        except Exception as e:
            self.show_error(str(e))

    def show_error(self, msg):x
        popup = Popup(title="Status/Error Log", content=Label(text=msg), size_hint=(0.8, 0.6))
        popup.open()

if __name__ == "__main__":
    Window.size = (1200, 800)
    ThesisDXFApp().run()