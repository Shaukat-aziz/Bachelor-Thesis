from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np

class PlotCanvas(FigureCanvas):

    def __init__(self, parent=None):
        fig = Figure(facecolor="#1E1E2E")
        self.ax = fig.add_subplot(111)
        super().__init__(fig)
        self.setParent(parent)

    def plot_structure(self, points):
        self.ax.clear()
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        self.ax.scatter(xs, ys, s=5, color="#8A2BE2")
        self.ax.set_aspect('equal')
        self.ax.set_facecolor("#1E1E2E")
        self.draw()

    def plot_hz(self, hz):
        self.ax.clear()
        self.ax.imshow(np.abs(hz[:,:,2]), cmap="magma")
        self.ax.set_facecolor("#1E1E2E")
        self.draw()