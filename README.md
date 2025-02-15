# EFISTools HOWTO

These scripts currently serve the following purposes:

1. *transformECATableDatacsv2pdf.py*: generating a pdf file based on the EFIS data (csv file)
2. *getAllCEPTDocs.py*: downloading and storing all pdf files from the ECO data base.

## get python

Download and install python from https://www.python.org/

## Setup environment:

Open a command window and navigate into the repo top directory.

`C:\Temp>C:\Users\david\AppData\Local\Programs\Python\Python312\python -m venv venv`
`C:\Temp>cd venv`
`C:\Temp\venc>Scripts\activate`
`(venv) C:\Temp\venv>pip install -r ..\requirements.txt `

## transformECATableDatacsv2pdf.py

### Provide Script and data:

Download and store the csv file
    https://efis.cept.org/reports/ReportDownloader?reportid=3
into the ECATable folder and rename the file to
    ECA_Table.csv

### Run the script

(venv) C:\Temp\ECATable>python ECATable_EFIS59.py

### NOTES:

- Missing:
  - Appendix with (linked) footnotes RR and ECA
  - Clickable Links to the CEPT Deliverables online
  - …