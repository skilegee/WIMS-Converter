import pandas as pd


# ==================================================
# CONFIGURATION
# ==================================================

METALS_TO_CONVERT = [
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


# ==================================================
# CLEAN DATA
# ==================================================

def clean_dataframe(df):

    df = df.copy()

    text_columns = [
        "SAMPLENAME",
        "ANALYTE",
        "METHOD",
        "Units",
        "RESULT"
    ]

    for col in text_columns:
        df[col] = (
            df[col]
            .fillna("")
            .astype(str)
            .str.strip()
        )

    df["Units"] = df["Units"].str.lower()

    return df


# ==================================================
# UNIT CONVERSION
# ==================================================

def convert_mgL_to_ugL(value):

    value = str(value).strip()

    if value.startswith("<"):
        try:
            return f"<{float(value[1:]) * 1000:g}"
        except:
            return value

    try:
        return f"{float(value) * 1000:g}"
    except:
        return value


def convert_selected_metals(df):

    pattern = "|".join(METALS_TO_CONVERT)

    mask = (
        df["ANALYTE"].str.contains(
            pattern,
            case=False,
            na=False
        )
        &
        (df["Units"] == "mg/l")
    )

    df.loc[mask, "RESULT"] = (
        df.loc[mask, "RESULT"]
        .apply(convert_mgL_to_ugL)
    )

    df.loc[mask, "Units"] = "ug/L"

    return df


# ==================================================
# SPECIAL LAB RULES
# ==================================================

def split_total_inorganic_nitrogen(df):

    mask = (
        df["ANALYTE"]
        .str.contains(
            "Total and Inorganic Nitrogen",
            case=False,
            na=False
        )
    )

    rows = df[mask].copy()

    if len(rows) != 2:
        return df

    rows["SORT"] = (
        rows["RESULT"]
        .str.replace("<", "", regex=False)
        .astype(float)
    )

    rows = rows.sort_values("SORT")

    inorganic = rows.iloc[0].copy()
    total = rows.iloc[1].copy()

    inorganic["ANALYTE"] = "Inorganic Nitrogen"
    total["ANALYTE"] = "Total Nitrogen"

    df = df[~mask]

    df = pd.concat(
        [
            df,
            pd.DataFrame([inorganic, total])
        ],
        ignore_index=True
    )

    return df


# ==================================================
# BUILD WIMS OUTPUT
# ==================================================

def build_wims_output(df):

    wims_df = pd.DataFrame({

        "StartTime": df["SAMPDATE"],
        "StopTime": df["SAMPDATE"],
        "SampleLocation": df["SAMPLENAME"],
        "Analyte": df["ANALYTE"],
        "Value": df["RESULT"],
        "Notes": df["METHOD"]

    })

    return wims_df.dropna(subset=["Value"])


# ==================================================
# MAIN FUNCTION
# ==================================================

def convert_to_wims(df):

    df = clean_dataframe(df)

    df = convert_selected_metals(df)

    df = split_total_inorganic_nitrogen(df)

    wims_df = build_wims_output(df)

    return wims_df