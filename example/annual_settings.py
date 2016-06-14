import sys, os
year = 2015
prev_yr_end = str(year - 1) + '-03-31'
year_beg = str(year - 1) + '-04-01'
year_end = str(year) + '-03-31'
opening_datetime = prev_yr_end + ' 23:59:59'
closing_datetime = year_end + ' 23:59:59'
finyr = '{:}-{:}'.format(year-1, year-2000)
fnames = dict(accounts = prev_yr_end + '-account-list.csv',
              money_balances = prev_yr_end + '-opening-money-balances.csv',
              commodity_balances = [prev_yr_end + '-stocks-quantity-cost.csv'],
              commodity_codes = [prev_yr_end + '-stocks-names.csv'],
              opening_ledger = year_beg + '-opening.ledger',
              opening_ledger_json = year_beg + '-opening.json',
              opening_price_data = [prev_yr_end + '-stocks-prices.csv'],
              closing_price_data = [year_end + '-stocks-prices.csv'],
              opening_pricedb = prev_yr_end + '-prices',
              closing_pricedb = year_end + '-prices',
              pre_closing = year_end + '-pre-closing.ledger',
              post_closing = year_end + '-post-closing.ledger',
              pre_closing_json = year_end + '-pre-closing.json',
              post_closing_json = year_end + '-post-closing.json',
              closing_commodity_balances = year_end + '-qty-cost-value.csv'
)

opg_balance_account = 'opening balance'
annual_savings_account = 'savings ' + finyr
