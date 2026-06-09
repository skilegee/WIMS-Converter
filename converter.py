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
# MAP LAB ANALYTE NAMES
# TO WIMS ANALYTE NAMES
# -----------------------------
def map_analyte(name):

    name_lower = str(name).lower().strip()

    # Copper PD
    if "copper" in name_lower and "dissolved" in name_lower:
        return "Copper, Dissolved"
    
    # Silver PD
    if "silver" in name_lower and "dissolved" in name_lower:
        return "Silver, Dissolved"
    

    # Cadmium TR
    if "cadmium" in name_lower:
        return "Cadmium, Total Recoverable"
    # Cadmium Dissolved
    if"cadmium" in name_lower and "dissolved" in name_lower:
        return "Cadmium, Dissolved"


    # Chromium Total 
    if "chromium" in name_lower:
        return "Chromium, Total"
    # Chromium  PD
    if "chromium III" in name_lower and "dissolved" in name_lower:
        return "Chromium, Dissolved"


    # Chromium III Total 
    if "chromium III" in name_lower:
        return "Chromium, Total Recoverable"
    # Chromium III PD
    if "chromium III" in name_lower and "dissolved" in name_lower:
        return "Chromium, Dissolved"


   # Chromium-HV Total 
    if "chromium" in name_lower and "hexavalent":
        return "Chromium, Hexavalent"
    # Chromium-HV PD
    if "hexavalent" in name_lower and "dissolved" in name_lower:
        return "Chromium, Dissolved"


    # Lead Total
    if "lead" in name_lower:
        return "Lead, Total"  
    # Lead PD
    if "lead" in name_lower and "dissolved" in name_lower:
        return "Lead, Dissolved"


    # Zinc PD
    if "zinc" in name_lower and "dissolved" in name_lower:
        return "Zinc, Dissolved"

    # Iron TR
    if "iron" in name_lower:
        return "Iron, Total Recoverable"
    # Iron Dissolved
    if "iron" in name_lower and "dissolved" in name_lower:
        return "Iron, Dissolved"


    # Arsenic TR
    if "arsenic" in name_lower:
        return "Arsenic, Total Recoverable"
     # Arsenic Dissolved
    if "arsenic" in name_lower and "dissolved" in name_lower:
        return "Arsenic, Dissolved"

    # Nickel TR 
    if "nickel" in name_lower:
        return "Nickel, Total"
    
    # Nickel PD 
    if "nickel" in name_lower and "dissolved" in name_lower:
        return "Nickel, Dissolved"

    # Selenium PD
    if "selenium" in name_lower and "dissolved" in name_lower:
        return "Selenium, Dissolved"
    
    # Cyanide
    if "cyanide" in name_lower:
        return "Cyanide, Dissolved"
    
    # Molybdenum TR
    if "molybdenum" in name_lower:
        return "Molybdenum, Total"
    
    return name

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

    # DEBUGG
    print("Before mapping:")
    print(sorted(df["ANALYTE"].unique()))

    # -----------------------------
    # APPLY ANALYTE MAPPING
    # -----------------------------
    df["ANALYTE"] = df["ANALYTE"].apply(map_analyte)


    # DEBUG
    print("After mapping:")
    print(sorted(df["ANALYTE"].unique()))

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