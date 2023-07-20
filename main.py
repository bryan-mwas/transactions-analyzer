from pdfminer.high_level import extract_text

# pdf = Pdf.open(r'mpesa.pdf', password='615856')

# print(pdf.open_metadata())

text = extract_text(r'mpesa.pdf', password='615856')


f = open("pdf_extract.txt", "w")
f.write(text)
f.close()
