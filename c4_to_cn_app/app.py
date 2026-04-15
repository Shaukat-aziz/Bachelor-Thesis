import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

from geometry import generate_c4_lattice, volterra_transform
from simulation import run_simulation
from analysis import compute_vortex_charge

st.set_page_config(layout="wide")

st.title("C4 → Cn Volterra Disclination Simulator")

# Sidebar parameters
st.sidebar.header("Parameters")

n = st.sidebar.slider("Target symmetry n", 3, 8, 5)
a = st.sidebar.slider("Lattice constant a", 0.5, 2.0, 1.0)
r = st.sidebar.slider("Hole radius r", 0.05, 0.5, 0.2)
R = st.sidebar.slider("Structure radius R", 5, 20, 10)
resolution = st.sidebar.slider("Resolution", 10, 40, 20)

run_button = st.sidebar.button("Run Simulation")

if run_button:

    with st.spinner("Generating lattice..."):
        points = generate_c4_lattice(a, R)
        points = volterra_transform(points, n)

    col1, col2 = st.columns(2)

    # Structure Plot
    with col1:
        fig1, ax1 = plt.subplots()
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        ax1.scatter(xs, ys, s=5)
        ax1.set_aspect('equal')
        ax1.set_title("Structure")
        st.pyplot(fig1)

    with st.spinner("Running Meep simulation..."):
        hz, freq = run_simulation(points, r, R, resolution)

    # Hz intensity
    with col2:
        fig2, ax2 = plt.subplots()
        intensity = np.abs(hz[:,:,2])
        im = ax2.imshow(intensity, cmap="magma")
        ax2.set_title(f"|Hz| (freq = {freq:.4f})")
        st.pyplot(fig2)

    # Phase plot
    fig3, ax3 = plt.subplots()
    phase = np.angle(hz[:,:,2])
    ax3.imshow(phase, cmap="twilight")
    ax3.set_title("Phase of Hz")
    st.pyplot(fig3)

    charge = compute_vortex_charge(hz)

    st.success(f"Vortex charge = {charge}")