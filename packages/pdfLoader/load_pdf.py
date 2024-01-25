import camelot
import pandas as pd
from PyPDF2 import PdfReader
from pathlib import Path


class MpesaLoader:
    def __init__(self, filePath: Path = 'mpesa.pdf', secret: str = '615856') -> None:
        self.filePath = filePath
        self.secret = secret
        self.dataFrames = []

    def get_pdf_info(self):
        reader = PdfReader(self.filePath)
        reader.decrypt(self.secret)
        return reader

    def sanitize(self, dataframe: pd.DataFrame):
        #     print(dataframe.columns)
        mpesa_statement_header = dataframe.iloc[0][0].split('\n')
        #     print(mpesa_statement_header)
        dataframe.drop(0, inplace=True)
        dataframe.columns = mpesa_statement_header
        dataframe['Details'] = dataframe.get(
            'Details', default='N/A').str.replace('\n', ' ')
        to_refactor = dataframe.loc[dataframe['Transaction Status'].str.contains(
            '\n', regex=True)]
        withdrawn_refactor = dataframe.loc[dataframe['Withdrawn'].str.contains(
            '\n', regex=True)]
        balance_refactor = dataframe.loc[dataframe['Balance'].str.contains(
            '\n', regex=True)]

        for idx, row in to_refactor.iterrows():
            status, amount = dataframe.loc[idx]['Transaction Status'].split(
                '\n')
            dataframe.loc[idx, 'Transaction Status'] = status
            dataframe.loc[idx, 'Paid In'] = amount

        # This is critical to avoid having errors when converting number to float
        dataframe['Withdrawn'] = dataframe.get(
            'Withdrawn', default='N/A').str.replace(',', '')
        dataframe['Balance'] = dataframe.get(
            'Balance', default='N/A').str.replace(',', '')
        dataframe['Paid In'] = dataframe.get(
            'Paid In', default='N/A').str.replace(',', '')

        for idx, row in withdrawn_refactor.iterrows():
            amounts = dataframe.loc[idx]['Withdrawn'].split('\n')
            # This loop handles the scenarios of multirow values
            for i in range(len(amounts)):
                dataframe.loc[idx + i, 'Withdrawn'] = amounts[i]

        for idx, row in balance_refactor.iterrows():
            amounts = dataframe.loc[idx]['Balance'].split('\n')
            # This loop handles the scenarios of multirow values
            for i in range(len(amounts)):
                dataframe.loc[idx + i, 'Balance'] = amounts[i]

        return dataframe

    def load_data_frame(self, tables, page_number):
        table_number = 0
        if page_number == 1:
            table_number = 1
        print('Page number %d of %d, table number: %d' %
              (page_number, self.get_pdf_info().getNumPages(), table_number))
        df = tables[table_number].df
        sanitized_df = self.sanitize(df.copy())
        return sanitized_df.copy()

    def initDF(self):
        pdfPages = len(self.get_pdf_info().pages)
        for i in range(1, pdfPages+1):
            tables = camelot.read_pdf(
                self.filePath, password=self.secret, pages='%d' % i)
            self.dataFrames.append(self.load_data_frame(tables, page_number=i))

        return pd.concat(self.dataFrames)
