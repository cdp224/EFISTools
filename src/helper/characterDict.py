from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import string

# Register Arial font (Make sure you have 'arial.ttf' in the same directory or installed in your system)
pdfmetrics.registerFont(TTFont('Arial', 'arial.ttf'))

# Define the font name, size, and reference character for normalization
font_name = "Arial"
font_size = 8
reference_char = 'A'

# Get the width of the reference character 'A'
reference_width = pdfmetrics.stringWidth(reference_char, font_name, font_size)

# Characters to measure
characters = string.ascii_letters + string.digits + "-() ."

# Create the dictionary of relative widths
relative_widths = {
    char: pdfmetrics.stringWidth(char, font_name, font_size) / reference_width
    for char in characters
}

# Print the dictionary
print(relative_widths)

# Optionally, save the dictionary to a file
import json
with open("relative_widths.json", "w") as file:
    json.dump(relative_widths, file, indent=4)

print("Relative widths saved to 'relative_widths.json'.")
