import gspread
import pandas as pd
import numpy as np

class Gsheet:

    def __init__(self, config_dict):
        self.service_account = gspread.service_account_from_dict(config_dict)

    def get_sheet_data(self, workbook_name, worksheet_name):
        workbook = self.service_account.open(workbook_name)
        worksheet = workbook.worksheet(worksheet_name)
        return pd.DataFrame(worksheet.get_all_records())