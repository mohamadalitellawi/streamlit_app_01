import streamlit as st
import forallpeople as si

from app_module import calc_Mr

si.environment("structural")




b_value = st.sidebar.number_input("Section width (mm)")
d_value = st.sidebar.number_input("Section depth (mm)")
fy_value = st.sidebar.number_input("Steel yield strength (MPa)", value=350)

phi = 0.9
b = b_value * si.mm
d = d_value * si.mm
fy = fy_value * si.MPa

mr_latex, mr_value = calc_Mr(b, d, phi, fy)

st.markdown("# Calculating the moment capacity of a steel plate (no LTB)")
st.latex(mr_latex)
