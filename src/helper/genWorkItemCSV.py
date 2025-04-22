import pandas as pd
import sys
import os

def extract_tables_to_csv(input_filename):
    # Check if file exists
    if not os.path.isfile(input_filename):
        print(f"Error: File '{input_filename}' does not exist.")
        return

    # Load the HTML content from file
    with open(input_filename, "r", encoding="utf-8") as file:
        html_content = file.read()

    # Parse all tables in the HTML content
    try:
        tables = pd.read_html(html_content)
    except ValueError as e:
        print(f"Error parsing tables: {e}")
        return

    if not tables:
        print("No tables found in the file.")
        return

    # Export each table to a separate CSV file
    base_name = os.path.splitext(os.path.basename(input_filename))[0]
    for i, table in enumerate(tables):
        csv_filename = f"{base_name}_table_{i+1}.csv"
        table.to_csv(csv_filename, index=False)
        print(f"Saved: {csv_filename}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python genWorkItemCSV.py <input_file>")
    else:
        extract_tables_to_csv(sys.argv[1])
