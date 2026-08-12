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

    # Preserve "<" for non-detects
    if value.startswith("<"):
        try:
            return f"<{float(value[1:]) * 1000:g}"
        except:
            return value

    # Convert normal numeric values
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

    # Find all rows containing
    # "Total and Inorganic Nitrogen"
    mask = (
        df["ANALYTE"]
        .str.contains(
            "Total and Inorganic Nitrogen",
            case=False,
            na=False
        )
    )

    # Get only the nitrogen rows
    tin_rows = df[mask].copy()

    # If there are no nitrogen rows,
    # return the original dataframe
    if tin_rows.empty:
        return df

    # --------------------------------------------------
    # Create a temporary numeric value for comparison
    # --------------------------------------------------

    tin_rows["RESULT_NUMERIC"] = (
        tin_rows["RESULT"]
        .astype(str)
        .str.replace("<", "", regex=False)
        .str.strip()
    )

    tin_rows["RESULT_NUMERIC"] = pd.to_numeric(
        tin_rows["RESULT_NUMERIC"],
        errors="coerce"
    )

    # --------------------------------------------------
    # Check for invalid nitrogen results
    # --------------------------------------------------

    if tin_rows["RESULT_NUMERIC"].isna().any():

        bad_rows = tin_rows[
            tin_rows["RESULT_NUMERIC"].isna()
        ]

        raise ValueError(
            "One or more Total and Inorganic Nitrogen "
            "results could not be interpreted as numbers."
        )

    # --------------------------------------------------
    # Group nitrogen results by sample
    # --------------------------------------------------
    #
    # This allows the program to handle:
    #
    # Sample 1 → 2 nitrogen rows
    # Sample 2 → 2 nitrogen rows
    # Sample 3 → 2 nitrogen rows
    #
    # etc.
    # --------------------------------------------------

    grouped = tin_rows.groupby(
        ["SAMPLENAME", "SAMPDATE"],
        sort=False
    )

    replacement_rows = []

    # --------------------------------------------------
    # Process each sample individually
    # --------------------------------------------------

    for _, group in grouped:

        # Each sample should have exactly
        # two Total and Inorganic Nitrogen results

        if len(group) != 2:

            sample_name = group.iloc[0]["SAMPLENAME"]
            sample_date = group.iloc[0]["SAMPDATE"]

            raise ValueError(
                f"Expected exactly 2 Total and Inorganic "
                f"Nitrogen results for sample "
                f"'{sample_name}' on '{sample_date}', "
                f"but found {len(group)}."
            )

        # --------------------------------------------------
        # Smallest = Inorganic Nitrogen
        # Largest = Total Nitrogen
        # --------------------------------------------------

        group = group.sort_values(
            "RESULT_NUMERIC"
        )

        inorganic_n = group.iloc[0].copy()
        total_n = group.iloc[1].copy()

        # --------------------------------------------------
        # Safety check
        # --------------------------------------------------

        if (
            total_n["RESULT_NUMERIC"]
            < inorganic_n["RESULT_NUMERIC"]
        ):

            raise ValueError(
                f"Total Nitrogen ({total_n['RESULT']}) "
                f"is less than Inorganic Nitrogen "
                f"({inorganic_n['RESULT']}) for sample "
                f"'{total_n['SAMPLENAME']}'."
            )

        # --------------------------------------------------
        # Rename analytes
        # --------------------------------------------------

        inorganic_n["ANALYTE"] = "Inorganic Nitrogen"
        total_n["ANALYTE"] = "Total Nitrogen"

        # --------------------------------------------------
        # Remove temporary comparison column
        # --------------------------------------------------

        inorganic_n = inorganic_n.drop(
            "RESULT_NUMERIC"
        )

        total_n = total_n.drop(
            "RESULT_NUMERIC"
        )

        # Add converted rows to list

        replacement_rows.append(inorganic_n)
        replacement_rows.append(total_n)

    # --------------------------------------------------
    # Remove original combined nitrogen rows
    # --------------------------------------------------

    df = df[~mask].copy()

    # --------------------------------------------------
    # Add the newly labeled nitrogen rows
    # --------------------------------------------------

    if replacement_rows:

        nitrogen_df = pd.DataFrame(
            replacement_rows
        )

        df = pd.concat(
            [
                df,
                nitrogen_df
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

    return wims_df.dropna(
        subset=["Value"]
    )


# ==================================================
# MAIN FUNCTION
# ==================================================

def convert_to_wims(df):

    #Clean incoming laboratory data
    df = clean_dataframe(df)

    #Convert selected metals
    # mg/L → µg/L
    df = convert_selected_metals(df)

    #Differentiate Btwn Total and Inorganic Nitrogen
    df = split_total_inorganic_nitrogen(df)

    #Build WIMS-compatible dataframe
    wims_df = build_wims_output(df)

    return wims_df