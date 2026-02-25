import pandas as pd



def detect_sections(data_sheet: pd.DataFrame):
    """
    Detect start indices of key financial sections
    inside Screener 'Data Sheet'.
    """

    col0 = data_sheet.iloc[:, 0].astype(str)

    sections = {}

    for idx, value in col0.items():
        val = value.strip().upper()

        if val == "PROFIT & LOSS":
            sections["pl_start"] = idx

        elif val == "BALANCE SHEET":
            sections["bs_start"] = idx

        elif val == "QUARTERS":
            sections["q_start"] = idx

        elif val == "CASH FLOW:":
            sections["cf_start"] = idx

    return sections










import pandas as pd


def extract_pl(data_sheet: pd.DataFrame, sections: dict) -> pd.DataFrame:
    """
    Extract Profit & Loss section into long format.
    Output columns: metric, year, value
    """

    pl_start = sections["pl_start"]
    pl_end = sections.get("q_start")  # P&L ends where Quarters begins

    if pl_end is None:
        raise ValueError("Could not find where P&L ends (q_start missing).")

    # Slice section (skip the 'PROFIT & LOSS' label row)
    block = data_sheet.iloc[pl_start + 1 : pl_end].copy()

    # First column cleaned
    col0 = block.iloc[:, 0].astype(str).str.strip()

    # 🔥 Robust detection of "Report Date"
    report_date_idx = col0[
        col0.str.contains("REPORT DATE", case=False, na=False)
    ].index

    if len(report_date_idx) == 0:
        raise ValueError("Report Date row not found inside P&L section.")

    report_row = report_date_idx[0]

    # Extract years from Report Date row (columns 1 onward)
    years_raw = block.loc[report_row].iloc[1:]

    years = []
    for x in years_raw:
        if pd.notna(x):
            dt = pd.to_datetime(x)
            years.append(dt.year)

    # Keep only matching value columns
    value_cols = list(range(1, 1 + len(years)))

    # Data rows start AFTER Report Date row
    data = block.loc[
        report_row + 1 :,
        [block.columns[0]] + [block.columns[i] for i in value_cols]
    ].copy()

    data.columns = ["metric"] + years

    # Clean metrics
    data["metric"] = data["metric"].astype(str).str.strip()
    data = data[data["metric"].ne("") & data["metric"].ne("nan")]

    # Wide → Long
    pl_long = data.melt(id_vars="metric", var_name="year", value_name="value")
    pl_long = pl_long.dropna(subset=["value"])

    # Type safety
    pl_long["year"] = pl_long["year"].astype(int)
    pl_long["value"] = pd.to_numeric(pl_long["value"], errors="coerce")
    pl_long = pl_long.dropna(subset=["value"])

    return pl_long



















def extract_quarters(data_sheet: pd.DataFrame, sections: dict) -> pd.DataFrame:
    """
    Extract Quarterly section into long format.
    Output columns: metric, period, value
    """

    q_start = sections.get("q_start")
    bs_start = sections.get("bs_start")

    if q_start is None:
        raise ValueError("QUARTERS section not found.")

    if bs_start is None:
        raise ValueError("Could not determine where QUARTERS ends.")

    # Slice between QUARTERS and BALANCE SHEET
    block = data_sheet.iloc[q_start + 1 : bs_start].copy()

    col0 = block.iloc[:, 0].astype(str).str.strip()

    # Find header row (where first column is 'Report Date')
    header_idx = col0[col0.str.upper() == "REPORT DATE"].index

    if len(header_idx) == 0:
        raise ValueError("REPORT DATE row not found in Quarters section.")

    header_row = header_idx[0]

    # Extract quarter labels
    periods_raw = block.loc[header_row].iloc[1:]
    periods = []

    for p in periods_raw:
        if pd.notna(p):
            dt = pd.to_datetime(p)
            label = dt.strftime("%b-%y")  # Sep-23
            periods.append(label)

    value_cols = list(range(1, 1 + len(periods)))

    # Data rows start after header
    data = block.loc[
        header_row + 1 :,
        [block.columns[0]] + [block.columns[i] for i in value_cols]
    ].copy()

    data.columns = ["metric"] + periods

    # Clean metrics
    data["metric"] = data["metric"].astype(str).str.strip()
    data = data[data["metric"].ne("") & data["metric"].ne("nan")]

    # Wide → long
    q_long = data.melt(id_vars="metric", var_name="period", value_name="value")
    q_long = q_long.dropna(subset=["value"])

    q_long["value"] = pd.to_numeric(q_long["value"], errors="coerce")
    q_long = q_long.dropna(subset=["value"])

    return q_long


















def extract_balance_sheet(data_sheet: pd.DataFrame, sections: dict) -> pd.DataFrame:
    """
    Extract Balance Sheet into long format.
    Output columns: metric, year, value
    """

    bs_start = sections.get("bs_start")
    cf_start = sections.get("cf_start")

    if bs_start is None:
        raise ValueError("BALANCE SHEET section not found.")

    # If Cash Flow exists, BS ends there
    if cf_start is not None:
        bs_end = cf_start
    else:
        bs_end = len(data_sheet)

    block = data_sheet.iloc[bs_start + 1 : bs_end].copy()

    col0 = block.iloc[:, 0].astype(str).str.strip()

    header_idx = col0[col0.str.upper() == "REPORT DATE"].index

    if len(header_idx) == 0:
        raise ValueError("REPORT DATE row not found in Balance Sheet section.")

    header_row = header_idx[0]

    years_raw = block.loc[header_row].iloc[1:]
    years = []

    for y in years_raw:
        if pd.notna(y):
            dt = pd.to_datetime(y)
            years.append(dt.year)

    value_cols = list(range(1, 1 + len(years)))

    data = block.loc[
        header_row + 1 :,
        [block.columns[0]] + [block.columns[i] for i in value_cols]
    ].copy()

    data.columns = ["metric"] + years

    data["metric"] = data["metric"].astype(str).str.strip()
    data = data[data["metric"].ne("") & data["metric"].ne("nan")]

    bs_long = data.melt(id_vars="metric", var_name="year", value_name="value")
    bs_long = bs_long.dropna(subset=["value"])

    bs_long["year"] = bs_long["year"].astype(int)
    bs_long["value"] = pd.to_numeric(bs_long["value"], errors="coerce")
    bs_long = bs_long.dropna(subset=["value"])

    return bs_long

















def extract_cash_flow(data_sheet: pd.DataFrame, sections: dict) -> pd.DataFrame:
    """
    Extract Cash Flow section into long format.
    Output columns: metric, year, value
    """

    cf_start = sections["cf_start"]

    # Cash Flow goes till end of sheet
    block = data_sheet.iloc[cf_start + 1 :].copy()

    # First column cleaned
    col0 = block.iloc[:, 0].astype(str).str.strip()

    # Locate "Report Date" row
    report_date_idx = col0[
        col0.str.contains("REPORT DATE", case=False, na=False)
    ].index

    if len(report_date_idx) == 0:
        raise ValueError("Report Date row not found inside Cash Flow section.")

    report_row = report_date_idx[0]

    # Extract years from Report Date row
    years_raw = block.loc[report_row].iloc[1:]

    years = []
    for x in years_raw:
        if pd.notna(x):
            dt = pd.to_datetime(x)
            years.append(dt.year)

    # Determine value columns
    value_cols = list(range(1, 1 + len(years)))

    # Data rows start after Report Date row
    data = block.loc[
        report_row + 1 :,
        [block.columns[0]] + [block.columns[i] for i in value_cols]
    ].copy()

    data.columns = ["metric"] + years

    # Clean metrics
    data["metric"] = data["metric"].astype(str).str.strip()
    data = data[data["metric"].ne("") & data["metric"].ne("nan")]

    # Wide → Long
    cf_long = data.melt(id_vars="metric", var_name="year", value_name="value")
    cf_long = cf_long.dropna(subset=["value"])

    # Type safety
    cf_long["year"] = cf_long["year"].astype(int)
    cf_long["value"] = pd.to_numeric(cf_long["value"], errors="coerce")
    cf_long = cf_long.dropna(subset=["value"])

    return cf_long








































































