import pandas as pd
from sqlalchemy import create_engine


def load_excel_to_sql(
    file_path: str,
    table_name: str = "financial_metrics",
    db_path: str = "bank_financials.db"
):
    """
    Loads Excel data into SQLite database.

    Parameters:
    -----------
    file_path : str
        Full path to Excel file
    table_name : str
        Name of SQL table
    db_path : str
        SQLite database file name
    """

    try:
        print("Reading Excel file...")
        df = pd.read_excel(file_path)

        print("Creating database connection...")
        engine = create_engine(f"sqlite:///{db_path}")

        print("Uploading data to SQL...")
        df.to_sql(
            name=table_name,
            con=engine,
            if_exists="replace",   # replace existing table
            index=False
        )

        print("======================================")
        print(f"SUCCESS: Table '{table_name}' created.")
        print(f"Database file: {db_path}")
        print("======================================")

    except FileNotFoundError:
        print("ERROR: Excel file not found. Check the file path.")

    except Exception as e:
        print("Unexpected error occurred:")
        print(e)


if __name__ == "__main__":
    load_excel_to_sql(
        file_path=r"C:\Users\rithw\Downloads\financial_data.xlsx"
    )