
import camelot
import pandas as pd
import re


# Get the first and only table for all pages except page 1
"""
    The Safaricom MPesa PDF has two tables on page 1. 
    The subsequent pages have one table
    Ideally read the pdf: Page by page
"""


def load_pdf(file_name='mpesa.pdf', password='615856'):
    tables = camelot.read_pdf(file_name, password, pages='4')
    df = tables[0].df
    mpesa_statement_header = df.iloc[0][0].split('\n')

    df.drop(0, inplace=True)

    df.columns = mpesa_statement_header

    df.head()

    df['Details'] = df['Details'].str.replace('\n', ' ')

    to_refactor = df.loc[df['Transaction Status'].str.contains(
        '\n', regex=True)]

    for idx, row in to_refactor.iterrows():
        status, amount = df.loc[idx]['Transaction Status'].split('\n')
        df.loc[idx, 'Transaction Status'] = status
        df.loc[idx, 'Paid In'] = amount

    for row in df['Details']:
        print(row)

# ## Patterns found in details
# ### Keywords
# * to : (Paybill, Merchant)
# * at : (Withdrawal)
# * from : (Incoming)
# * charge


def get_first_element(items):
    try:
        return items[0]
    except IndexError:
        return None

# ## The devil is in the details
#
# Trying to answer:
# * Where am I making most purchases from (till, paybill) - (Where are my expenses)
# * To whom do I send the most money?
# * What are my monthly transactional cost?
#
# Functions
# * handlePaybill()
# * handleTill()
# * handleReceivables()
# * handleWithdrawals()
# * handleCharges()


regx_transaction_dets = r'\d+\s-\s\b\w+.*\b'
regx_paybill = r'\bPay Bill Online\b'
regx_till = r'\bMerchant Payment\b'
regx_charge = r'\bcharge\b'
regx_receivables = r'\bfrom\b'


def handle_paybill(table):
    for row_index, row in table.iterrows():
        completed_at = row["Completion Time"]
        received = row['Paid In']
        paid_out = row['Withdrawn']
        transaction_id = row['Receipt No.']
        payments = re.compile(regx_paybill)
        if payments.search(row['Details']):
            payment_receiver, * \
                rest = re.findall(regx_transaction_dets, row['Details'])
            paybill_number = str.split(payment_receiver, ' - ')[0]
            paybill_name = str.split(payment_receiver, ' - ')[1]
            print(transaction_id, end=" ")
            print(paybill_name, end=" ")
            print(paybill_name, end=" ")
            print(paid_out, end=" ")
            print(completed_at)


def handle_all_charges(table):
    for row_index, row in table.iterrows():
        transaction_date = row["Completion Time"]
        received = row['Paid In']
        paid_out = row['Withdrawn']
        transaction_id = row['Receipt No.']
        payments = re.compile(regx_charge, flags=re.I)
        if payments.search(row['Details']):
            print(transaction_id, end=" ")
            print(paid_out, end=" ")
            print(transaction_date)


def handle_till(table):
    for row_index, row in table.iterrows():
        completed_at = row["Completion Time"]
        paid_out = row['Withdrawn']
        payments = re.compile(regx_till)
        if payments.search(row['Details']):
            print(row['Details'])
            till_merchant, * \
                rest = re.findall(regx_transaction_dets, row['Details'])
            print(str.split(till_merchant, ' - '))


def handle_receivables(table):
    for row_index, row in table.iterrows():
        transaction_date = row['Completion Time']
        received = re.compile(regx_receivables)
        if received.search(row['Details']):
            print(row['Details'])
            print(row['Paid In'])


handle_paybill(df)
handle_all_charges(df)
handle_till(df)
handle_receivables(df)

df.tail()
