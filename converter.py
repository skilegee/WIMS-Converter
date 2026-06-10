import pandas as pd


# -----------------------------
# Convert mg/L → µg/L safely
# while preserving "<" values
# -----------------------------
def convert_mgL_to_ugL(value):

    value = str(value).strip()

    # Handle non-detects like "<0.0010"
    if value.startswith("<"):
        try:
            num = float(value[1:])
            return f"<{num * 1000:g}"
        except:
            return value

    # Handle normal numeric values
    try:
        return str(float(value) * 1000)
    except:
        return value


# -----------------------------
# MAIN CONVERSION FUNCTION
# -----------------------------
def convert_to_wims(df):

    # IMPORTANT FIX:
    # prevent pandas string dtype crash
    df["RESULT"] = df["RESULT"].astype("object")

    # Clean text fields safely
    df["SAMPLENAME"] = df["SAMPLENAME"].fillna("").astype(str).str.strip()
    df["ANALYTE"] = df["ANALYTE"].fillna("").astype(str).str.strip()
    df["METHOD"] = df["METHOD"].fillna("").astype(str).str.strip()
    df["Units"] = df["Units"].fillna("").astype(str).str.strip().str.lower()

    # -----------------------------
    # Metals to convert ONLY
    # -----------------------------
    metals_to_convert = [
        "Copper",
        "Lead",
        "Iron",
        "Arsenic",
        "Cadmium",
        "Molybdenum",
        "Nickel",
        "Selenium",
        "Silver",
        "Chromium",
        "Hexavalent Chromium",
        "Zinc",
        "Cyanide",
        "Nonylphenol"
    ]

    # -----------------------------
    # Detect matching analytes
    # (handles long names like ICPMS labels)
    # -----------------------------
    metal_mask = df["ANALYTE"].apply(
        lambda x: any(
            metal.lower() in x.lower()
            for metal in metals_to_convert
        )
    )

    # Only convert mg/L rows
    unit_mask = df["Units"].eq("mg/l")

    convert_mask = metal_mask & unit_mask

    # -----------------------------
    # APPLY CONVERSION
    # -----------------------------
    df.loc[convert_mask, "RESULT"] = df.loc[convert_mask, "RESULT"].apply(
        convert_mgL_to_ugL
    )

    # Update units after conversion
    df.loc[convert_mask, "Units"] = "ug/L"

    # -----------------------------
    # BUILD WIMS OUTPUT
    # -----------------------------
    wims_df = pd.DataFrame({
        "StartTime": df["SAMPDATE"],
        "StopTime": df["SAMPDATE"],
        "SampleLocation": df["SAMPLENAME"],
        "Analyte": df["ANALYTE"],
        "Value": df["RESULT"],
        "Notes": df["METHOD"]
    })

    # Remove empty results only
    wims_df = wims_df.dropna(subset=["Value"])

    return wims_df