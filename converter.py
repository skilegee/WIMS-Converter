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

    # --------------------------------------------------
    # Make a copy so we don't accidentally modify the
    # original dataframe while processing nitrogen.
    # --------------------------------------------------

    df = df.copy()

    # --------------------------------------------------
    # Find all rows containing:
    #
    # Total and Inorganic Nitrogen
    #
    # Case-insensitive and allows extra spaces.
    # --------------------------------------------------

    nitrogen_mask = (
        df["ANALYTE"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.contains(
            "total and inorganic nitrogen",
            case=False,
            na=False
        )
    )

    nitrogen_rows = df[nitrogen_mask].copy()

    # --------------------------------------------------
    # Nothing to process
    # --------------------------------------------------

    if nitrogen_rows.empty:
        return df

    # --------------------------------------------------
    # Make sure LABSAMPID exists.
    #
    # LABSAMPID is preferable to SAMPLENAME because it
    # uniquely identifies the laboratory sample.
    # --------------------------------------------------

    if "LABSAMPID" not in nitrogen_rows.columns:

        raise ValueError(
            "LABSAMPID column was not found in the laboratory "
            "file. The nitrogen conversion requires LABSAMPID "
            "to identify individual samples."
        )

    # --------------------------------------------------
    # Clean LABSAMPID
    # --------------------------------------------------

    nitrogen_rows["LABSAMPID"] = (
        nitrogen_rows["LABSAMPID"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    # --------------------------------------------------
    # Create a temporary numeric version of RESULT.
    #
    # IMPORTANT:
    # This does NOT change the original RESULT.
    #
    # Example:
    #
    # "<0.50" → 0.50
    # "8.5"   → 8.5
    #
    # This is ONLY used to determine which result is
    # smaller/larger.
    # --------------------------------------------------

    nitrogen_rows["RESULT_NUMERIC"] = (
        nitrogen_rows["RESULT"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.replace("<", "", regex=False)
        .str.replace(">", "", regex=False)
        .str.strip()
    )

    nitrogen_rows["RESULT_NUMERIC"] = pd.to_numeric(
        nitrogen_rows["RESULT_NUMERIC"],
        errors="coerce"
    )

    # --------------------------------------------------
    # Check for results that could not be interpreted.
    # --------------------------------------------------

    invalid_results = nitrogen_rows[
        nitrogen_rows["RESULT_NUMERIC"].isna()
    ]

    if not invalid_results.empty:

        bad_values = (
            invalid_results["RESULT"]
            .astype(str)
            .unique()
            .tolist()
        )

        raise ValueError(
            "The following Total and Inorganic Nitrogen "
            f"results could not be interpreted: {bad_values}"
        )

    # --------------------------------------------------
    # Group by LABSAMPID.
    #
    # This allows the program to process:
    #
    # Sample 1 → two nitrogen results
    # Sample 2 → two nitrogen results
    # Sample 3 → two nitrogen results
    #
    # ...and so on.
    # --------------------------------------------------

    grouped = nitrogen_rows.groupby(
        "LABSAMPID",
        sort=False
    )

    replacement_rows = []

    # --------------------------------------------------
    # Process every laboratory sample separately.
    # --------------------------------------------------

    for sample_id, group in grouped:

        # --------------------------------------------------
        # Each sample MUST contain exactly two results.
        # --------------------------------------------------

        if len(group) != 2:

            raise ValueError(
                f"Sample {sample_id} has {len(group)} "
                "rows labeled 'Total and Inorganic Nitrogen'. "
                "Exactly 2 results are required."
            )

        # --------------------------------------------------
        # Sort from smallest → largest.
        #
        # Smallest = Inorganic Nitrogen
        # Largest   = Total Nitrogen
        # --------------------------------------------------

        group = group.sort_values(
            "RESULT_NUMERIC"
        )

        inorganic_row = group.iloc[0].copy()
        total_row = group.iloc[1].copy()

        inorganic_value = inorganic_row["RESULT_NUMERIC"]
        total_value = total_row["RESULT_NUMERIC"]

        # --------------------------------------------------
        # Make sure the values are actually different.
        #
        # If both values are identical, we cannot determine
        # which one is Total and which one is Inorganic
        # using the requested "smallest/largest" rule.
        # --------------------------------------------------

        if inorganic_value == total_value:

            raise ValueError(
                f"Sample {sample_id} has two identical "
                f"Total and Inorganic Nitrogen results "
                f"({inorganic_row['RESULT']}). "
                "The converter cannot determine which is "
                "Total Nitrogen and which is Inorganic Nitrogen."
            )

        # --------------------------------------------------
        # Assign the analyte names.
        # --------------------------------------------------

        inorganic_row["ANALYTE"] = "Inorganic Nitrogen"

        total_row["ANALYTE"] = "Total Nitrogen"

        # --------------------------------------------------
        # Remove temporary comparison column.
        #
        # The original RESULT remains untouched, meaning:
        #
        # "<0.50" stays "<0.50"
        # --------------------------------------------------

        inorganic_row = inorganic_row.drop(
            "RESULT_NUMERIC"
        )

        total_row = total_row.drop(
            "RESULT_NUMERIC"
        )

        # --------------------------------------------------
        # Save the two converted rows.
        # --------------------------------------------------

        replacement_rows.append(inorganic_row)
        replacement_rows.append(total_row)

    # --------------------------------------------------
    # Remove the original:
    #
    # Total and Inorganic Nitrogen
    #
    # rows from the dataframe.
    # --------------------------------------------------

    df = df[
        ~nitrogen_mask
    ].copy()

    # --------------------------------------------------
    # Add the newly labeled rows.
    # --------------------------------------------------

    if replacement_rows:

        nitrogen_output = pd.DataFrame(
            replacement_rows
        )

        df = pd.concat(
            [
                df,
                nitrogen_output
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