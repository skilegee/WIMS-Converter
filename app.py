import streamlit as st
import pandas as pd
from converter import convert_to_wims

st.title("WIMS CSV Converter")

file = st.file_uploader("Upload CSV")

if file:
    df = pd.read_csv(file)
    st.dataframe(df)

    converted = convert_to_wims(df)

    st.write("Converted Data")
    st.dataframe(converted)

 # Create downloadable CSV
    csv = converted.to_csv(index=False)

    st.download_button(
        label="Download WIMS CSV",
        data=csv,
        file_name="WIMS_Import.csv",
        mime="text/csv"
    )
    