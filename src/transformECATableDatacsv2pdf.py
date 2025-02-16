import pandas as pd
import os
import requests
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import SimpleDocTemplate, Flowable, Table, TableStyle, PageTemplate, Paragraph, Frame, Spacer, PageBreak
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfgen.canvas import Canvas
import argparse

# Register Arial font
pdfmetrics.registerFont(TTFont('Arial', 'Arial.ttf'))

class MyDocTemplate(SimpleDocTemplate):
    """Custom SimpleDocTemplate to manage bookmarks and table of contents."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bookmarks = []

    def afterFlowable(self, flowable):
        """Capture the location of flowable for bookmarks."""
        if isinstance(flowable, Paragraph) and hasattr(flowable, '_bookmark'):
            self.canv.bookmarkPage(flowable._bookmark)  # Mark the page for the bookmark
            self.canv.addOutlineEntry(flowable.text, flowable._bookmark, level=0)  # Add to outline

def estimate_string_length(s):
    capital_letters=sum(1 for char in s if char.isupper())
    return ((len(s)-capital_letters)*0.7+capital_letters)

def find_space_or_hyphen(s):
    # Find the position of the first space after the given start position
    pos_space = s.find(' ')
    if pos_space == -1:
        pos_space=1000
    
    # Find the position of the first hyphen after the given start position
    pos_hyphen = s.find('-')
    if pos_hyphen==-1:
        pos_hyphen = 1000

    pos_comma = s.find(',')
    if pos_comma == -1:
        pos_comma = 1000
    
    # Now, we need to return the first occurrence of either space or hyphen
    if pos_space == 1000 and pos_hyphen == 1000 and pos_comma == 1000:
        # Neither space nor hyphen is found: just give the remaining length
        return estimate_string_length(s)
    else:
        # Both are found, return the one with the lower index (earliest in the string)
        return estimate_string_length(s[:min(pos_space, pos_hyphen, pos_comma)])

#this routine takes the string from the csv and formats it according to the
#Radio Regulations. This needs to be extended to support reordering of the services 
#according to the french ordering. Proposal: make a lookup table that stores the
#services and the position in ordering according to the french way. Extract these numbers
#according to the services at hand and to the reordering accordingly.
def wrap_service_data_info(in_string):
    in_bracket = False
    test_str = in_string
    remaining_str = test_str
    servicedata_info = ""
    line_char_count = 0
    kill_next_char = False
    for i in test_str:
        remaining_str = remaining_str[1:]
        if kill_next_char == False:
            nc = i #default: next charactrer is the current character...
            if nc.isupper():
                line_char_count = line_char_count + 1
            else:
                line_char_count = line_char_count + 0.7
            if i == '(':
                in_bracket = True
            if i == ')':
                in_bracket = False
            if in_bracket == True:
                if i == ',':  #in a bracket replace the comma with void, i.e., just remove it
                    nc=""
            if in_bracket == False:
                if i == ',':  #outside a bracket replace a comma with a break; remove next (space)
                    nc="<br/>"
                    line_char_count = 0
                    kill_next_char = True
            if i == "-": #check if a break is needed
                if find_space_or_hyphen(remaining_str) + line_char_count > 25: 
                    nc="-<br/>&nbsp;&nbsp;&nbsp;"
                    line_char_count = 2
            if i == " ": #check if a break is needed
                if find_space_or_hyphen(remaining_str) + line_char_count > 25: 
                    nc="<br/>&nbsp;&nbsp;&nbsp;"
                    line_char_count = 2
            servicedata_info=servicedata_info + nc
        else:
            kill_next_char = False
    return servicedata_info

def wrap_deliverables_info(in_string):
    test_str = in_string
    remaining_str = test_str
    servicedata_info = ""
    line_char_count = 0
    kill_next_char = False
    for i in test_str:
        remaining_str = remaining_str[1:]
        if kill_next_char == False:
            nc = i #default: next charactrer is the current character...
            if nc.isupper():
                line_char_count = line_char_count + 1
            else:
                line_char_count = line_char_count + 0.7
            if i == ',':  #outside a bracket replace a comma with a break; remove next (space)
                nc=",<br/>"
                line_char_count = 0
                kill_next_char = True
            servicedata_info=servicedata_info + nc
        else:
            kill_next_char = False
    return servicedata_info

def generate_pdf(data, output_filename):

    def draw_footer(canvas, doc):
        canvas.saveState()
    
        # Set font for the footer text
        canvas.setFont("Arial", 9)
    
        # Footer text (you can customize this)
        footer_text = f"Page {doc.page}"
    
        # Draw the footer text at the bottom right of the page
        canvas.drawRightString(doc.width + doc.leftMargin, 1 * cm, footer_text)
    
        canvas.restoreState()


    # Function to define the layout of each page, including the footer
    def my_on_page(canvas, doc):
        draw_footer(canvas, doc)

    doc = MyDocTemplate(output_filename, pagesize=landscape(A4),
                            leftMargin=1 * cm,
                            rightMargin=1 * cm,
                            topMargin=1 * cm,
                            bottomMargin=1 * cm)

    elements = []

    # Define a common style for all cells
    common_style = ParagraphStyle(
        name="CommonStyle",
        fontName="Arial",
        fontSize=8,
        leading=9,
        alignment=TA_LEFT,
        spaceAfter=-6
    )

    # Define the style for the frequency band range cell
    band_style = ParagraphStyle(
        name="BandStyle",
        fontName="Arial",
        fontSize=12,
        leading=14,
        alignment=TA_LEFT,
        spaceAfter=-6,
        textColor=colors.black,
        fontWeight='bold',
    )

    # Define the style for the frequency band range cell
    title_style = ParagraphStyle(
        name="TitleStyle",
        fontName="Arial",
        fontSize=16,
        leading=18,
        alignment=TA_LEFT,
        spaceAfter=6,
        textColor=colors.black,
        fontWeight='bold',
    )

    ECATableHeaderStyle = TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),  # Align text to the top
        ('LINEBELOW', (0, 0), (-1, 0), 1, colors.black),  # Line under header
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),  # Add grid to the entire table
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),  # Header background
        ('LINEBEFORE', (2, 0), (2, -1), 2, colors.black),  # Double line between service and application columns
        ('LINEBEFORE', (2, 0), (2, -1), 1, colors.white),  # Double line between service and application columns
    ])

    InfoTableHeaderStyle=TableStyle([
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),  # Align text to the top
                    ('LINEBELOW', (0, 0), (-1, 0), 1, colors.black),  # Line under header
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.black),  # Add grid to the entire table
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),  # Header background
                    #('LINEBEFORE', (2, 0), (2, -1), 2, colors.black),  # Double line between service and application columns
                    #('LINEBEFORE', (2, 0), (2, -1), 1, colors.white),  # Double line between service and application columns
                ])
    InfoTableStyle=TableStyle([
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),  # Align text to the top
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),  # Add grid to the entire table
                    ])
    # Table headings
    table_headers = ["RR Region 1", "European Common Allocations", "Application", "CEPT Deliverables", "Standard", "Note"]
    col_widths = [150, 150, 152, 92, 58, 180]  # Adjust based on content

    FN_table_headers = ["Footnote Number", "Footnote Content"]
    FN_col_widths = [100, 50+150+152+92+58+180]  # Adjust based on content

    current_band = None
    table_data = []  # Initialize the table_data list before the loop
    lines_used = 0  # Track the number of lines used on the current page
    max_lines_per_page = 44  # Adjust based on the content and font size
    
    # draw the initial first table header
    table_data = [table_headers]
    elements.append(Table(table_data, colWidths=col_widths, style=ECATableHeaderStyle))
    elements.append(Spacer(1, 12))  # Add space after each frequency band table
    lines_used = 2  # Track the number of lines used on the current page

    table_data = []  # Initialize the table_data list before the loop
    first_line = True
    comas_for_table = 0
    service_hight = 0
    
    inECAtable = True
    inECAFootnoteTable = False
    docType = "ECATable"

    for index, row in data.iterrows():
        
        #Footnote Part of csv reached
        if (row['Upper Frequency']=="footnotetext"):
            inECAtable = False
            docType = "ECANotes"
            print("footnotes start")

        if inECAtable:
            freq_band = f"{row['Lower Frequency']} - {row['Upper Frequency']}"

            # Start a new frequency band table when the frequency range changes
            if freq_band != current_band:
                first_line = True
                # If table_data is not empty, create and add the table to elements
                if table_data:
                    # Estimate the number of lines the current table will use
                    tt_len = len(table_data)                
                    lines_for_table = max(service_hight, comas_for_table * 1 + tt_len) + 3.7  # Adding 2 for the band title and spacer
                    comas_for_table = 0
                    # Check if adding this table will exceed the max lines per page
                    if lines_used + lines_for_table > max_lines_per_page:
                        elements.append(PageBreak())
                        table_head_data = [table_headers]
                        elements.append(Table(table_head_data, colWidths=col_widths, style=ECATableHeaderStyle))

                        elements.append(Spacer(1, 12))  # Add space after each frequency band table
                        lines_used = 2  # Track the number of lines used on the current page
        
                    # Add the table and update lines used
                    # Add a bookmark for the current frequency band
                    bookmark_name = f"band_{current_band.replace(' ', '_').replace('-', '_')}"
                    paragraph = Paragraph(current_band, band_style)
                    paragraph._bookmark = bookmark_name  # Assign a bookmark name to the Paragraph
                    elements.append(paragraph)

                    elements.append(Table(table_data, colWidths=col_widths, style=TableStyle([
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),  # Align text to the top
                        ('SPAN', (0, 0), (0, len(table_data) - 1)),  # Merge RR Region 1 cells
                        ('SPAN', (1, 0), (1, len(table_data) - 1)),  # Merge CEPT Allocation cells
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),  # Add grid to the entire table
                        ('LINEBEFORE', (2, 0), (2, -1), 2, colors.black),  # Double line between service and application columns
                        ('LINEBEFORE', (2, 0), (2, -1), 1, colors.white),  # Double line between service and application columns
                    ])))

                    lines_used += lines_for_table
                    
                    if lines_used < 0.9*max_lines_per_page:
                        elements.append(Spacer(1, 12))  # Add space after each frequency band table


                # Start a new table for the new frequency band
                current_band = freq_band
                #table_data = [table_headers]  # Reset the table data with the headers

            # Prepare row data for the table
            footnote_info = row['RR Region 1 Footnotes'].replace(",", "")
            servicedata_info = row['RR Region 1 Allocation'].replace("(", " (") #add spaces before the '('
            servicedata_info = wrap_service_data_info(servicedata_info) #wrap the service data
            service_info = Paragraph(f"{servicedata_info}<br/><br/>{footnote_info}", common_style) #attach the footnotes

            footnote_info = row['ECA Footnotes'].replace(",", "")
            servicedata_info = row['European Common Allocation'].replace("(", " (")
            servicedata_info = wrap_service_data_info(servicedata_info) #wrap the service data
            cept_info = Paragraph(f"{servicedata_info}<br/><br/>{footnote_info}", common_style)

            app_info = Paragraph(row['Applications'], common_style)
            cept_doc = Paragraph(wrap_deliverables_info(row['ECC/ERC Harmonisation Measure']), common_style)
            standard = Paragraph(row['Standard'], common_style)  # Wrap text in the "Standard" column
            notes = Paragraph(row['Notes'], common_style)  # Wrap text in the "Notes" column

            # Append the current row data
            if first_line:
                table_first_line = [service_info, cept_info, app_info, cept_doc, standard, notes]
                table_data = [table_first_line]  # Reset the table data with the headers
                #table_data.append([service_info, cept_info, app_info, cept_doc, standard, notes])
                service_hight = 0.85*max(len(service_info.text) // 30, len(cept_info.text) // 30, service_info.text.count('<br/>'), cept_info.text.count('<br/>'))
                first_line = False
            else:
                table_data.append([service_info, cept_info, app_info, cept_doc, standard, notes])
            commas_for_row = max(standard.text.count(','), cept_doc.text.count(','), len(notes.text) // 40) # estimate the hight of the line. Check the number of comas, cehck the length of the note.
            comas_for_table = comas_for_table+commas_for_row
        elif (inECAtable == False and inECAFootnoteTable == False):
            inECAFootnoteTable = True
            # Add the last table for the remaining data
            if table_data:
                # Estimate the number of lines the last table will use
                tt_len = len(table_data)                
                lines_for_table = max(service_hight, comas_for_table * 1.0 + tt_len) + 3  # Adding 2 for the band title and spacer
                comas_for_table = 0
                # Check if adding this table will exceed the max lines per page
                if lines_used + lines_for_table > max_lines_per_page:
                    elements.append(PageBreak())
                    table_head_data = [table_headers]
                    elements.append(Table(table_head_data, colWidths=col_widths, style=ECATableHeaderStyle))
                    elements.append(Spacer(1, 12))  # Add space after each frequency band table
                    lines_used = 2  # Track the number of lines used on the current page
            
                # Add the table and update lines used
                bookmark_name = f"band_{current_band.replace(' ', '_').replace('-', '_')}"
                paragraph = Paragraph(current_band, band_style)
                paragraph._bookmark = bookmark_name  # Assign a bookmark name to the Paragraph
                elements.append(paragraph)
                #elements.append(Paragraph(current_band, band_style))
                elements.append(Table(table_data, colWidths=col_widths, style=TableStyle([
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),  # Align text to the top
                        ('SPAN', (0, 0), (0, len(table_data) - 1)),  # Merge RR Region 1 cells
                        ('SPAN', (1, 0), (1, len(table_data) - 1)),  # Merge CEPT Allocation cells
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),  # Add grid to the entire table
                        ('LINEBEFORE', (2, 0), (2, -1), 2, colors.black),  # Double line between service and application columns
                        ('LINEBEFORE', (2, 0), (2, -1), 1, colors.white),  # Double line between service and application columns
                    ])))

                #new page: now the footnotes start:
                elements.append(PageBreak())
                # draw the initial first table header
                bookmark_name = f"ECA Footnotes"
                paragraph = Paragraph("ECA Footnotes", title_style)
                paragraph._bookmark = bookmark_name  # Assign a bookmark name to the Paragraph
                elements.append(paragraph)
                table_data = [FN_table_headers]
                elements.append(Table(table_data, colWidths=FN_col_widths, style=InfoTableHeaderStyle))
                elements.append(Spacer(1, 12))  # Add space after each frequency band table
                lines_used = 4  # Track the number of lines used on the current page
                #elements.append(paragraph)
                first_line = True
                #elements.append(Spacer(1, 12))  # Add space after each frequency band table
                #table_data=[]
        elif (inECAFootnoteTable):
                if (row['Upper Frequency']=="title" and docType=="ETSI"):
                    print("ETSI what start")
                    docType = "ETSIwhat"
                    FN_table_headers = ["Document", "Description"]
                    lines_used = 100 #trigger a new page. 
                if (row['Upper Frequency']=="title" and docType=="CEPT"):
                    print("ETSI start")
                    docType = "ETSI"
                    FN_table_headers = ["Document", "Description"]
                    lines_used = 100 #trigger a new page. 
                if (row['Upper Frequency']=="title" and docType=="RR"):
                    print("CEPT start")
                    docType = "CEPT"
                    FN_table_headers = ["Document", "Description"]
                    lines_used = 100 #trigger a new page.
                if (row['Upper Frequency']=="footnotetext"):
                    inECAtable = False
                    print("RR footnotes start")
                    docType = "RR"
                    lines_used = 100 #trigger a new page.
                if (row['Upper Frequency']=="description"):
                    print("abbreviation start")
                    FN_table_headers = ["Abbreviation", "Description"]
                    docType = "Abbreviations"
                    lines_used = 100 #trigger a new page.

                foot_note_number = row['Lower Frequency'] 
                foot_note_content = row['Upper Frequency']
                #print(foot_note_content)
                foot_note_number_par = Paragraph(f"{foot_note_number}", common_style) #attach the footnotes
                foot_note_content_par = Paragraph(f"{foot_note_content}", common_style) #attach the footnotes
                
                if lines_used < 100: #ignore line.
                    if first_line:
                        table_first_line = [foot_note_number_par, foot_note_content_par]
                        table_data = [table_first_line]  # Reset the table data with the headers
                        #table_data.append([service_info, cept_info, app_info, cept_doc, standard, notes])
                        first_line = False
                    else:
                        table_data.append([foot_note_number_par, foot_note_content_par])
                
                    footnote_height = max(len(foot_note_content_par.text) // 190,  foot_note_content_par.text.count('<br/>'))
                    lines_used = lines_used + footnote_height + 1.4
                    print(lines_used)

                if (lines_used  > max_lines_per_page):

                    elements.append(Table(table_data, colWidths=FN_col_widths, style=InfoTableStyle))
                    #add the table and make a new page.
                    elements.append(PageBreak())

                    if lines_used == 100: #insert new title
                        lines_used = 2
                        if docType=="RR":
                            bookmark_name = f"Radio Regulations Footnotes"
                            paragraph = Paragraph("Radio Regulations Footnotes", title_style)
                        elif docType=="CEPT":
                            bookmark_name = f"CEPT Deliverables"
                            paragraph = Paragraph("CEPT Deliverables", title_style)
                        elif docType=="ETSI":
                            bookmark_name = f"European Standards"
                            paragraph = Paragraph("European Standards", title_style)
                        elif docType=="ETSIwhat":
                            bookmark_name = f"Receive only European Standards"
                            paragraph = Paragraph("Receive only European Standards", title_style)
                        elif docType=="Abbreviations":
                            bookmark_name = f"Abbreviations"
                            paragraph = Paragraph("Abbreviations", title_style)
                        paragraph._bookmark = bookmark_name  # Assign a bookmark name to the Paragraph
                        elements.append(paragraph) # add title
                    else:
                        lines_used = 0

                    table_data = [FN_table_headers]
                    elements.append(Table(table_data, colWidths=FN_col_widths, style=InfoTableHeaderStyle))
                    elements.append(Spacer(1, 12))  # Add space after each frequency band table
                    lines_used = lines_used + 2  # Track the number of lines used on the current page
                    first_line = True
    elements.append(Table(table_data, colWidths=FN_col_widths, style=InfoTableStyle))
            


    # Build PDF

    doc.build(elements, onFirstPage=my_on_page, onLaterPages=my_on_page)

def process_csv(csv_filename):
    # Read the CSV file without any changes to the row order
    df = pd.read_csv(csv_filename, sep=';', quotechar='"')

    # Replace NaN with empty strings
    df.fillna("  ", inplace=True)

    # Renaming columns for easier access
    # TODO: This needs to be adapted in case the csv format is changed (swap Standard and Applications)
    df.columns = [
        'Lower Frequency', 'Upper Frequency', 
        'RR Region 1 Allocation', 'RR Region 1 Footnotes', 
        'European Common Allocation', 'ECA Footnotes', 
        'ECC/ERC Harmonisation Measure', 'Applications', 
        'Standard', 'Notes'
    ]

    return df
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

# Argument parsing setup
def parse_arguments():
    parser = argparse.ArgumentParser(description="Generate a frequency allocation PDF from CSV data.")

    # Optional argument to control data manipulations
    parser.add_argument('--manipulate-data', action='store_true', help="Flag to control data manipulations. Default is False.")

    # Argument for input CSV file
    parser.add_argument('--input-csv', type=str, required=True, help="Path to the input CSV file. LATEST to get the latest from ECO")

    # Argument for output PDF file
    parser.add_argument('--output-pdf', type=str, default='../output/output.pdf', help="Path to the output PDF file. Default is 'output.pdf'.")

    # Parse the arguments and return them
    return parser.parse_args()

def main():
    # Parse arguments
    args = parse_arguments()

    # Accessing the parsed arguments
    input_csv = args.input_csv
    output_pdf = args.output_pdf
    manipulate_data = args.manipulate_data

    # Process input data
    print(f"Processing input file: {input_csv}")
    if (input_csv=='LATEST'):
        input_csv = os.path.join('.', 'LATEST.csv')
        download_file('https://efis.cept.org/reports/ReportDownloader?reportid=3', input_csv)

    data = process_csv(input_csv)  # Replace with your CSV processing function

    # Optionally manipulate data
    if manipulate_data:
        print("Applying data manipulations...")
        # Add your data manipulation code here
    
    # Generate the PDF
    print(f"Generating PDF: {output_pdf}")
    generate_pdf(data, output_pdf)

    #input_csv = 'ECA_Table.csv'  # Replace with your CSV file path
    #output_pdf = 'ECA_Table.pdf'
    
    # Process the CSV and generate the PDF
    #data = process_csv(input_csv)
    #generate_pdf(data, output_pdf)


if __name__ == "__main__":
    main()
