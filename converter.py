import pandas as pd

def convert_to_wims(df):
    """
    Convert lab CSV format to WIMS RIO import format.
    """

    # Clean text fields
    df["SAMPLENAME"] = df["SAMPLENAME"].astype(str).str.strip()
    df["ANALYTE"] = df["ANALYTE"].astype(str).str.strip()
    df["METHOD"] = df["METHOD"].astype(str).str.strip()

    # Create WIMS output
    wims_df = pd.DataFrame({
        "StartTime": df["SAMPDATE"],
        "StopTime": df["SAMPDATE"],
        "SampleLocation": df["SAMPLENAME"],
        "Analyte": df["ANALYTE"],
        "Value": df["RESULT"],
        "Notes": df["METHOD"]
    })

    # Remove rows with missing results
    wims_df = wims_df.dropna(subset=["Value"])

    return wims_df