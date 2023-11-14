from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.layout import LAParams, LTTextBox, LTTextLine, LTFigure, LTChar, LTLine, LTTextContainer
from pdfminer.converter import PDFPageAggregator
from pdfminer.utils import bbox2str


def extract_tables_from_pdf(pdf_path, password=None):
    with open(pdf_path, 'rb') as file:
        parser = PDFParser(file)
        document = PDFDocument(parser, password)

        if not document.is_extractable:
            raise Exception("PDF document not extractable.")

        rsrcmgr = PDFResourceManager()
        laparams = LAParams()
        device = PDFPageAggregator(rsrcmgr, laparams=laparams)
        interpreter = PDFPageInterpreter(rsrcmgr, device)

        tables = []

        for page in PDFPage.create_pages(document):
            interpreter.process_page(page)
            layout = device.get_result()

            # Find horizontal and vertical lines
            horizontal_lines = [element for element in layout if isinstance(
                element, LTLine) and element.height < 0.1]
            vertical_lines = [element for element in layout if isinstance(
                element, LTLine) and element.width < 0.1]

            # Group lines to form table cells
            cells = []
            for line in horizontal_lines:
                cells.append([line])
            for line in vertical_lines:
                merged = False
                for cell in cells:
                    if any(cell_line.bbox[0] <= line.bbox[0] <= cell_line.bbox[2] for cell_line in cell):
                        cell.append(line)
                        merged = True
                        break
                if not merged:
                    cells.append([line])

            # Sort cells by position
            cells.sort(key=lambda c: c[0].bbox[3], reverse=True)

            # Extract text from cells
            table = []
            for cell in cells:
                row = []
                for line in cell:
                    text = ""
                    for element in layout:
                        if isinstance(element, (LTTextBox, LTTextLine)):
                            bbox = bbox2str(line.bbox)
                            if bbox2str(element.bbox) == bbox:
                                text += element.get_text().strip() + " "
                    row.append(text.strip())
                table.append(row)

            tables.append(table)

        return tables


pdf_path = r'mpesa.pdf'
password = '615856'

try:
    tables = extract_tables_from_pdf(pdf_path, password)
    for table in tables:
        print('Table:')
        for row in table:
            print(row)
        print('------')
except Exception as e:
    print(e)
