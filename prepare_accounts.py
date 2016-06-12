import numpy as np
import pandas as pd
import sys, io, os, datetime
from ledger_functions import *

if len(sys.argv) < 2 : 
    print("Argument not provided for data_path. Exiting ...\n")
    exit()
data_path = sys.argv[1]
sys.path += [data_path] # annual_settings & other python scripts are in data_path
os.chdir(data_path) # all the data files are in data_path 
from annual_settings import * # this contains file names and other year specific variables
from make_je_list import je_list # je_list contains the journal entries for the year

############          Opending ledger and balance sheet         ############

# Opening ledger
opening_ledger_list = make_opening_ledger_list(
    fnames, prev_yr_end, opg_balance_account)
opening_ledger = ledger_list_to_ledger(opening_ledger_list)
ledger_balance_out, imbalance = ledger_balance(opening_ledger)
assert imbalance == 0
with open(fnames['opening_ledger'], 'w') as out:
    print(opening_ledger, file = out)
save_json(opening_ledger_list, fnames['opening_ledger_json'])

## Opending balance sheet at historical cost
print('Opening Balance Sheet\n' + ledger_balance_out)

## Opending assets at market value
assert 'pre_opening_pricedb' in fnames.keys() or \
    'opening_price_data' in fnames.keys(), \
    'Neither opening pricedb nor opening price data is available'
with open(fnames['opening_pricedb'], 'w') as out:
    if 'pre_opening_pricedb' in fnames.keys():
        print(open(fnames['pre_opening_pricedb']).read(), file = out)
    if 'opening_price_data' in fnames.keys():
        print(make_price_file(fnames['opening_price_data'],
                              opening_datetime), file = out)
ledger_balance_mv_out,imbalance = ledger_balance_MV(
    opening_ledger, fnames['opening_pricedb'], ['assets'])
print('Market Value Opening Assets\n' + ledger_balance_mv_out)


###########   Trial Balance after updating ledger with entries for the year  ##########

ledger_list = opening_ledger_list + je_list # this is imported from make_je_list
ledger = ledger_list_to_ledger(ledger_list)
# print(ledger)
ledger_balance_out, imbalance = ledger_balance(ledger)
assert imbalance == 0
# print('Trial Balance\n' + ledger_balance_out)


########## Income Statement, Balance Sheet, Analysis of Savings ##########

# Split Trial Balance into Income Statement and Balance Sheet with closing entry
surplus = ledger_balance(ledger, regex = income_statement_accounts)[1]
year_end_entry = [(year_end, "Year end transfer of surplus into equity"),
                  ('surplus', -surplus), (annual_savings_account, surplus)]
closing_ledger_list = ledger_list + [year_end_entry]
closing_ledger = ledger_list_to_ledger(closing_ledger_list)
with open(fnames['pre_closing'], 'w') as out:
    print(closing_ledger, file = out)
save_json(closing_ledger_list, fnames['pre_closing_json'])

# Income statement (after closing entry, this has zero balance)
income_statement = ledger_balance(closing_ledger, regex = income_statement_accounts)[0]
print('Income Statement\n' + income_statement)

# Balance Sheet (after closing entry, this balance sheet tallies)
balance_sheet, imbalance = ledger_balance(closing_ledger, regex = balance_sheet_accounts)
assert imbalance == 0
print('Balance Sheet\n' + balance_sheet)

# For full closing, every income statement account is reduced to zero balance
# to start the next year on a clean slate
income_statement_df = ledger_balances_df(closing_ledger, regex = income_statement_accounts)
closingje = [(year_end, 'Year end closure of income statement')] +\
            [(account, -amount) for (_, amount, account)
             in income_statement_df.itertuples()]
post_closing_ledger_list = closing_ledger_list + [closingje]
post_closing_ledger = ledger_list_to_ledger(post_closing_ledger_list)
with open(fnames['post_closing'], 'w') as out:
    print(post_closing_ledger, file = out)
save_json(post_closing_ledger_list, fnames['post_closing_json'])


########## At this stage the accounting is complete ##########
########## Rest is memorandum items and other analysis ##########

# Market Value of Assets
with open(fnames['closing_pricedb'], 'w') as out:
    print(make_price_file(fnames['closing_price_data'], closing_datetime),
          file = out)
balance_sheet_mv,imbalance = ledger_balance_MV(
    closing_ledger, fnames['closing_pricedb'], regex = ['assets'])
print('Market Value Closing Assets\n' + balance_sheet_mv)

# Savings and their deployment
opgBS = ledger_balances_df(opening_ledger, regex = balance_sheet_accounts) 
clsgBS = ledger_balances_df(closing_ledger, regex = balance_sheet_accounts) 
cashflow = pd.merge(opgBS, clsgBS, on = 'Account',
                    suffixes = ['_open', '_close'], how = 'outer').fillna(0)
with io.StringIO() as out:
    print(datetime.date(year, 3, 31), 'Cash flow statement', file =out)
    for _, Amount_open, Account, Amount_close in cashflow.itertuples():
        print(ledger_format().format(Account, Amount_close - Amount_open),
                                     file = out)
    cashflow_ledger = out.getvalue()
ledger_balance_out, imbalance = ledger_balance(cashflow_ledger, strict = False)
assert imbalance == 0
print('Deployment of Savings\n' + ledger_balance_out)

# Write out commodity qty cost and value
qty_cost_value = ledger_qty_basis_df(closing_ledger, fnames['closing_pricedb'])
qty_cost_value.to_csv(fnames['closing_commodity_balances'], index = False)
