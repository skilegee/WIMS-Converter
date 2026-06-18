import pandas as pd


# -----------------------------
# Convert mg/L → µg/L 
# keep "<" values
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
    # Metals to convert 
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
        "Nonylphenol",
        "Mercury",
        "Magnesium",
        "Manganese",
        "Nonylphenols",
        "Phenols"
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


    # --------------------------------------------------
    # DIFFERENTIATE BTWN TOTAL AND INORGANIC NITROGEN
    # --------------------------------------------------

    extra_rows = []

    tin_rows = df[df["ANALYTE"] == "Total and Inorganic Nitrogen"]

    if len(tin_rows) == 2:

     # Convert to numeric just in case
        tin_rows = tin_rows.copy()
        tin_rows["RESULT"] = pd.to_numeric(tin_rows["RESULT"], errors="coerce")

        # Smallest = Inorganic, Largest = Total
        tin_rows = tin_rows.sort_values("RESULT")

        inorganic_n = tin_rows.iloc[0]
        total_n = tin_rows.iloc[1]

        # Safety check - Total > Inorganic 
        if total_n["RESULT"] < inorganic_n["RESULT"]:
            raise ValueError(
                f"Total Nitrogen ({total_n['RESULT']}) is less than "
                f"Inorganic Nitrogen ({inorganic_n['RESULT']})"
            )

         # Create replacement rows
        extra_rows.append({
            "StartTime": total_n["SAMPDATE"],
            "StopTime": total_n["SAMPDATE"],
            "SampleLocation": total_n["SAMPLENAME"],
            "Analyte": "Total Nitrogen",
            "Value": total_n["RESULT"],
            "Notes": total_n["METHOD"]
        })

        extra_rows.append({
            "StartTime": inorganic_n["SAMPDATE"],
            "StopTime": inorganic_n["SAMPDATE"],
            "SampleLocation": inorganic_n["SAMPLENAME"],
            "Analyte": "Inorganic Nitrogen",
            "Value": inorganic_n["RESULT"],
            "Notes": inorganic_n["METHOD"]
        })

        # Remove original combined rows
        df = df[df["ANALYTE"] != "Total and Inorganic Nitrogen"]


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

    if extra_rows:
        wims_df = pd.concat(
            [wims_df, pd.DataFrame(extra_rows)],
            ignore_index=True
        )
    
    # Remove empty results only
    wims_df = wims_df.dropna(subset=["Value"])

    return wims_df