from dataclasses import dataclass
import re
import pandas as pd

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


@dataclass
class Transaction:
    """ Class to keep track of an MPesa transaction """
    category: str = ''
    completion_time: str = ''
    amount: float = 0.00
    recipient_id: str = 'n/a'
    recipient_name: str = ''
    receipt_id: str = ''


regx_transaction_dets = r'\d+\s-\s\b\w+.*\b'
regx_transaction_dets = r'\S+\s-\s+\S+.*'
regx_paybill = r'\bPay Bill Online\b'
regx_till = r'\bMerchant Payment\b'
regx_charge = r'(.)+(?=charge)'
regx_receivables = r'\bfrom\b'
regx_send_money = r'^Customer Transfer to.+\d{3}\s([A-Za-z]+\s[A-Za-z]+)$'


class TransactionFactory:
    def __init__(self, dataFrame: pd.DataFrame) -> None:
        self.transactions: list[Transaction] = []
        self.dataFrame: pd.DataFrame = dataFrame

    def extract_values(self, row):
        completed_at = row["Completion Time"]
        received = row['Paid In']
        paid_out = row['Withdrawn']
        receipt_no = row['Receipt No.']
        return (completed_at, received, paid_out, receipt_no)

    def handle_paybill(self):
        for row_index, row in self.dataFrame.iterrows():
            (completed_at, received, paid_out,
             receipt_no) = self.extract_values(row)
            payments = re.compile(regx_paybill)

            if payments.search(row['Details']):
                match = re.findall(regx_transaction_dets, row['Details'])
                payment_receiver = "0000 - Error"
                if len(match) > 0:
                    payment_receiver = match[0]
                paybill_number = str.split(payment_receiver, ' - ')[0]
                paybill_name = str.split(payment_receiver, ' - ')[1]

                transaction = Transaction()
                transaction.category = 'Paybill'
                transaction.receipt_id = receipt_no
                try:
                    amt = float(paid_out)
                    transaction.amount = abs(amt)
                except ValueError:
                    transaction.amount = float(0)
                transaction.completion_time = completed_at
                transaction.recipient_name = str.strip(
                    paybill_name).upper()
                transaction.recipient_id = str.strip(
                    paybill_number).upper()

                self.transactions.append(transaction)

    def handle_all_charges(self):
        for row_index, row in self.dataFrame.iterrows():
            (completed_at, received, paid_out,
             receipt_no) = self.extract_values(row)
            payments = re.compile(regx_charge, flags=re.I)
            result = payments.search(row['Details'])
            if result:
                transaction = Transaction()
                transaction.category = 'Charge'
                transaction.receipt_id = receipt_no
                try:
                    amt = float(paid_out)
                    transaction.amount = abs(amt)
                except ValueError:
                    transaction.amount = float(0)
                transaction.completion_time = completed_at
                transaction.recipient_name = str.strip(
                    result.group(0)).upper()

                self.transactions.append(transaction)

    def handle_till(self):
        for row_index, row in self.dataFrame.iterrows():
            (completed_at, received, paid_out,
             receipt_no) = self.extract_values(row)

            payments = re.compile(regx_till)

            if payments.search(row['Details']):
                match = re.findall(regx_transaction_dets, row['Details'])
                if len(match) > 0:
                    till_number = str.split(match[0], ' - ')[0]
                    till_name = str.split(match[0], ' - ')[1]

                    transaction = Transaction()
                    transaction.category = 'Merchant Payment'
                    transaction.receipt_id = receipt_no
                    try:
                        amt = float(paid_out)
                        transaction.amount = abs(amt)
                    except ValueError:
                        transaction.amount = float(0)
                    transaction.completion_time = completed_at
                    transaction.recipient_name = str.strip(till_name)
                    transaction.recipient_id = str.strip(till_number)

                    self.transactions.append(transaction)

    def handle_send_money(self):
        for row_index, row in self.dataFrame.iterrows():
            (completed_at, received, paid_out,
             receipt_no) = self.extract_values(row)

            send_money = re.compile(regx_send_money)
            res = send_money.search(row['Details'])
            if res:
                transaction = Transaction()
                transaction.category = 'Send Money'
                transaction.receipt_id = receipt_no
                try:
                    amt = float(paid_out)
                    transaction.amount = abs(amt)
                except ValueError:
                    transaction.amount = float(0)
                transaction.completion_time = completed_at
                transaction.recipient_name = str.strip(
                    res.group(1)).upper()

                self.transactions.append(transaction)
