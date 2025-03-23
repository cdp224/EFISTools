import os
import time
import csv
import re
import requests
import argparse


# Function to sanitize the title to create a valid filename
def sanitize_filename(title):
    # Replace '/', '(', and ')' with '_'
    title = ' '.join(title.strip().split())
    #return title.replace('/', '_').replace('(', '_').replace(')', '_').replace('<br>', '_').strip()
    return title.replace('/', '_').replace('<br>', '_').strip()

# Function to create directory if it doesn't exist
def create_directory(path):
    if not os.path.exists(path):
        os.makedirs(path)

# Function to download the file
def download_file(url, file_path):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Check if the request was successful
        with open(file_path, 'wb') as file:
            file.write(response.content)
        print(f"Downloaded: {file_path}")
    except requests.exceptions.RequestException as e:
        print(f"Failed to download {url}. Error: {e}")

# Main function to process the CSV file
def process_csv():

    global file_path, input_csv, output_path, simulate, active_only, get_reports, get_all, get_ec_decisions, get_ecc_decisions, get_recommendations
    with open(file_path, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file, delimiter=';')

        #iterate over all lines in the csv file
        for row in reader:

            doc_type = row['Type']
            print ("Doc_type "+doc_type)
            
            title = row['Title']
            
            status = row['Status']
            print ("Status " + status)
            if active_only:
                if status=="Withdrawn":
                    continue
            if "EC Decision" in doc_type:
                if not get_ec_decisions: 
                    continue
            if "ECC Decision" in doc_type:
                if not get_ecc_decisions: 
                    continue
            if "Report" in doc_type:
                if not get_reports:
                    continue
            if "Recommendation" in doc_type:
                if not get_recommendations:
                    continue
            
            print("Proceed with download...")
            creation_date=row['Publish Date']
            creation_time_struct = time.strptime(creation_date, "%Y-%m-%d")  # Convert to struct_time
            creation_timestamp = time.mktime(creation_time_struct)  # Convert to seconds since epoch
            pdf_url = row['pdf']
            # Only attempt download if url is reasonably long
            if (len(pdf_url)>20):
                pdf_urls = re.findall(r'http[^",]+', pdf_url)
                # pdf_url = re.search(r'"(http[^"]+)"', pdf_url).group(1)
                for i, pdf_url in enumerate(pdf_urls):            
                    # Sanitize title to create filename
                    print("Title: " + title)
                    
                    sanitized_title = sanitize_filename(title)
                    print("SaniTitle: " + sanitized_title)

                    #only add an index in case there are more than one pdf document to be downloaded.
                    if len(pdf_urls) > 1:
                        sanitized_title = sanitized_title + "_" + str(i+1)
                    filename = f"{sanitized_title}.pdf"

                    # Create directory path based on Type and Status
                    directory_path = os.path.join(output_path,doc_type.replace(" ", "_"), status)
                    # Create directory (if not in simulate mode)
                    if (simulate==False):
                        create_directory(directory_path)

                   # Full path to save the PDF
                    file_path = os.path.join(directory_path, filename)
                        
                    if simulate:
                        print("filepath: "+file_path)
                        print(pdf_url)

                    # Download the PDF (if not in simulate mode)
                    if (simulate==False):
                        download_file(pdf_url, file_path)
                        os.utime(file_path, (creation_timestamp, creation_timestamp)) #set the creation time to publication date

# Argument parsing setup
def parse_arguments():
    parser = argparse.ArgumentParser(
                description=("Downloads all active documents from CEPT and stores them in a given directory. "
                             "Example (simulation): python getAllCEPTDocs.py --output-path ..\\..\\TestDownload --input-csv LATEST --simulate"))

    # Argument for the path to the directories where the documents will be stored to
    parser.add_argument('--output-path', type=str, required=True, help="Path to where the documents are downloaded to.")

    # Argument for input CSV file
    parser.add_argument('--input-csv', type=str, required=True, help="File and path to the input CSV file. *LATEST* will download the lates file from CEPT")

    # Optional argument to if we want just to simulate the downloads
    parser.add_argument('--simulate', action='store_true', help="Flag to enable the actual download or not.")
   
    # Optional argument to control if we only need the active documents only.
    parser.add_argument('--active-only', action='store_true', help="Flag to control if only active documents need to be downloaded.")
    
    # Optional argument to control if we want to have the reports
    parser.add_argument('--get-reports', action='store_true', help="Flag to control if reports need to be downloaded.")

    # Optional argument to control if we want to have the reports
    parser.add_argument('--get-ecc-decisions', action='store_true', help="Flag to control if ECC decisions need to be downloaded.")

    # Optional argument to control if we want to have the reports
    parser.add_argument('--get-ec-decisions', action='store_true', help="Flag to control if EC decisions need to be downloaded.")

    # Optional argument to control if we want to have the reports
    parser.add_argument('--get-recommendations', action='store_true', help="Flag to control if recommendations need to be downloaded.")

    # Optional argument to control if we want to override and get all
    parser.add_argument('--get-all', action='store_true', help="Flag to control if all (active) documents need to be downloaded.")

    # Parse the arguments and return them
    return parser.parse_args()

def main():
    # Parse arguments
    args = parse_arguments()

    # Accessing the parsed arguments
    global file_path, input_csv, output_path, simulate, active_only, get_reports, get_all, get_ecc_decisions, get_ec_decisions, get_recommendations
    input_csv = args.input_csv
    output_path = args.output_path
    simulate = args.simulate
    active_only = args.active_only
    get_reports = args.get_reports

    get_recommendations = args.get_recommendations
    get_ecc_decisions = args.get_ecc_decisions
    get_ec_decisions = args.get_ec_decisions
    get_all = args.get_all

    #get_all overrides decisions
    if get_all:
        get_reports = True
        get_ecc_decisions = True
        get_ec_decisions = True
        get_recommendations = True
        
    print("Get_all " + str(get_all))
    print("Get_reports " + str(get_reports))
    print("Get_ecc_decisions " + str(get_ecc_decisions))
    print("Get_recommendations " + str(get_recommendations))
    print("Get_ec_decisions " + str(get_ec_decisions))

    print(simulate)

    if (input_csv=='LATEST'):
        input_csv = os.path.join('.', 'LATEST.csv')
        download_file('https://docdb.cept.org/search/exportall', input_csv)

    file_path=input_csv

    # Process the CSV file
    process_csv()

if __name__ == "__main__":
    main()
