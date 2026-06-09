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
# MAP LAB ANALYTE → WIMS PARAMETER NAME
# -----------------------------
def map_analyte(name):

    name_lower = str(name).lower().strip()

    # =============================
    # CHROMIUM (SPECIFIC FIRST)
    # =============================
    if "hexavalent" in name_lower:
        return "Chromium Hexavalent"

    if "chromium iii" in name_lower and "dissolved" in name_lower:
        return "Chromium, Dissolved"

    if "chromium iii" in name_lower:
        return "Chromium, Total Recoverable"

    if "chromium" in name_lower and "dissolved" in name_lower:
        return "Chromium, Dissolved"

    if "chromium" in name_lower:
        return "Chromium, Total Recoverable"

    # =============================
    # COPPER
    # =============================
    if "copper" in name_lower and "dissolved" in name_lower:
        return "Copper, Dissolved"

    if "copper" in name_lower:
        return "Copper, Total Recoverable"

    # =============================
    # LEAD
    # =============================
    if "lead" in name_lower and "dissolved" in name_lower:
        return "Lead, Dissolved"

    if "lead" in name_lower:
        return "Lead, Total Recoverable"

    # =============================
    # CADMIUM
    # =============================
    if "cadmium" in name_lower and "dissolved" in name_lower:
        return "Cadmium, Dissolved"

    if "cadmium" in name_lower:
        return "Cadmium, Total Recoverable"

    # =============================
    # ZINC
    # =============================
    if "zinc" in name_lower and "dissolved" in name_lower:
        return "Zinc, Dissolved"

    if "zinc" in name_lower:
        return "Zinc, Total Recoverable"

    # =============================
    # IRON
    # =============================
    if "iron" in name_lower and "dissolved" in name_lower:
        return "Iron, Dissolved"

    if "iron" in name_lower:
        return "Iron, Total Recoverable"

    # =============================
    # ARSENIC
    # =============================
    if "arsenic" in name_lower and "dissolved" in name_lower:
        return "Arsenic, Dissolved"

    if "arsenic" in name_lower:
        return "Arsenic, Total Recoverable"

    # =============================
    # NICKEL
    # =============================
    if "nickel" in name_lower and "dissolved" in name_lower:
        return "Nickel, Dissolved"

    if "nickel" in name_lower:
        return "Nickel, Total Recoverable"

    # =============================
    # SELENIUM
    # =============================
    if "selenium" in name_lower and "dissolved" in name_lower:
        return "Selenium, Dissolved"

    if "selenium" in name_lower:
        return "Selenium, Total Recoverable"

    # =============================
    # OTHER METALS
    # =============================
    if "silver" in name_lower and "dissolved" in name_lower:
        return "Silver, Dissolved"

    if "silver" in name_lower:
        return "Silver, Total Recoverable"

    if "molybdenum" in name_lower:
        return "Molybdenum, Total Recoverable"

    if "cyanide" in name_lower:
        return "Cyanide, Total"

    # fallback
    return name


# -----------------------------
# MAIN CONVERSION FUNCTION
# -----------------------------
def convert_to_wims(df):

    # Fix pandas dtype issues
    df["RESULT"] = df["RESULT"].astype("object")

    # Clean fields
    df["SAMPLENAME"] = df["SAMPLENAME"].fillna("").astype(str).str.strip()
    df["ANALYTE"] = df["ANALYTE"].fillna("").astype(str).str.strip()
    df["METHOD"] = df["METHOD"].fillna("").astype(str).str.strip()
    df["Units"] = df["Units"].fillna("").astype(str).str.strip().str.lower()

    # DEBUG (optional)
    print("Before mapping:")
    print(sorted(df["ANALYTE"].unique()))

    # Apply mapping
    df["ANALYTE"] = df["ANALYTE"].apply(map_analyte)

    # DEBUG (optional)
    print("After mapping:")
    print(sorted(df["ANALYTE"].unique()))

    # -----------------------------
    # METAL DETECTION (SAFE VERSION)
    # -----------------------------
    valid_metals = [
        "Copper", "Lead", "Iron", "Arsenic", "Cadmium",
        "Molybdenum", "Nickel", "Selenium", "Silver",
        "Chromium", "Zinc", "Cyanide"
    ]

    metal_mask = df["ANALYTE"].apply(
        lambda x: any(m.lower() in str(x).lower() for m in valid_metals)
    )

    # Only mg/L rows
    unit_mask = df["Units"].eq("mg/l")

    convert_mask = metal_mask & unit_mask

    # Convert values
    df.loc[convert_mask, "RESULT"] = df.loc[
        convert_mask, "RESULT"
    ].apply(convert_mgL_to_ugL)

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

    wims_df = wims_df.dropna(subset=["Value"])

    return wims_dfs