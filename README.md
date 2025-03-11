# EFISTools HOWTO

These scripts currently serve the following purposes:

1. *transformECATableDatacsv2pdf.py*: generating a pdf file based on the EFIS data (csv file)
2. *getAllCEPTDocs.py*: downloading and storing all pdf files from the ECO data base.

## get python

Download and install python from https://www.python.org/

## Setup environment:

Open a command window and navigate into the repo top directory.

```shell
C:\Temp>C:\Users\david\AppData\Local\Programs\Python\Python312\python -m venv venv
C:\Temp>cd venv
C:\Temp\venv>Scripts\activate
(venv) C:\Temp\venv>pip install -r ..\requirements.txt 
```

Now, all required libraries should have been installed.

## Generate ECA Table PDF

The script `transformECATableDatacsv2pdf.py` allows to generate a pdf file from the raw csv files from ECO.

There are several paramters:

### options

- -h, --help            show this help message and exit
- --input-ECA-csv INPUT_ECA_CSV
                        Path to the input CSV ECA table data file. LATEST to get the latest from ECO
                        Currently use the ´fixed_LATEST_ECA.csv´ file.
- --input-HarmStand-csv INPUT_HARMSTAND_CSV
                        Path to the input CSV harmonized standards data file. LATEST to get the latest from ECO
- --input-CEPTDocs-csv INPUT_CEPTDOCS_CSV
                        Path to the input CSV CEPT documents data file. LATEST to get the latest from ECO
- --output-pdf OUTPUT_PDF
                        Path to the output PDF file. Default is '_output.pdf'.

### Provide Script and data:

Download and store the csv file
    https://efis.cept.org/reports/ReportDownloader?reportid=3
into the ECATable folder and rename the file to
    ECA_Table.csv

### Run the script

(venv) C:\Temp\EISTools>python ECATable_EFIS59.py

### NOTES and TODOs

- TODO:
  - [x] Appendix with footnotes RR and ECA
  - [x] Appendix with abbreviations
  - [x] Clickable Links to the CEPT Deliverables online
  - [x] Include parameters for all input files
  - [x] Linking footnotes
  - [ ] Make the script immune against inconsistencies (report only).
  - [ ] Linking abbreviations
