import numpy as np
import pandas as pd
import io, subprocess, re, json

money = 'INR' # default currency is Indian Rupee (INR)

income_statement_accounts = ['expense', 'income', 'surplus']
balance_sheet_accounts = ['assets' , 'equity']

def ledger_format(type = 'standard'):
    space = ' '
    ledger_indent = space * 4
    dbl_space = space * 2
    width = '15'
    qty_format = '{:' + width + '.6f}'
    money_format = '{:' + width + ',.2f} INR'
    money_hiprec_format = '{:.6f} INR'
    cost_format = '{{' + money_hiprec_format + '}}'
    str_format = '{:' + width + '}'
    code_format = '"{:}"'
    return {'auto' : ledger_indent + '{:}',
            'account_decl' :  'account {:}',
            'sub_directive' : ledger_indent + '{:}' + space + '{:}',
            'standard' :  ledger_indent + str_format + dbl_space + money_format,
            'commodity_decl' : 'commodity' + space + code_format,
            'commodity_buy' : ledger_indent + str_format + dbl_space\
            + qty_format + space + code_format + space + '@@' + space\
            + money_format,
            'commodity_sell' : ledger_indent + str_format + dbl_space\
            + qty_format + space + code_format + space + cost_format\
            + space + '@' +money_format,
            'date_line' : '{:}' + space + '{:}',
            'price' : 'P' + space + '{:}' + space + code_format + space\
            + money_hiprec_format
    }[type]


def myfloat(s, commodity = money):
    s = s.replace(',', '') # remove thousand separators (,)
    s = re.sub('\s' + commodity + '\s.*$', '', s) # remove trailing commodity name with spaces
    s = re.sub('\s"' + commodity + '"\s.*$', '', s) # remove trailing quoted commodity name with spaces
    return float(s) # the string s is now numeric and can be converted using float

def make_opening_ledger_list(fnames, opg_date, opg_balance_account):
    if 'pre_opening_ledger_json' in fnames.keys():
        ledger_list = json.load(open(fnames['pre_opening_ledger_json'], 'r'))
    else:
        ledger_list = []
        first_year_data = ['accounts', 'money_balances', 'commodity_balances',
                           'commodity_codes']
        assert all([x in fnames.keys() for x in first_year_data]), \
            'Some data for creating first year opening ledger is missing'
    if 'accounts' in fnames.keys():
        tree = pd.read_csv(fnames['accounts'], header =0)
    else:
        tree = pd.DataFrame()
    if 'money_balances' in fnames.keys():
        money_balance = pd.read_csv(fnames['money_balances'], header =0)
    else:
        money_balance = pd.DataFrame()
    commodity_bal = pd.DataFrame()
    if 'commodity_balances' in fnames.keys():
        for f in fnames['commodity_balances']:
            commodity_bal = commodity_bal.append(pd.read_csv(f, header =0))
    commodity_codes = pd.DataFrame()
    if 'commodity_codes' in fnames.keys():
        for f in fnames['commodity_codes']:
            commodity_codes = commodity_codes.append(pd.read_csv(f, header =0))
    # account information
    for _, account, alias in tree.itertuples():
        if not pd.isnull(alias):
            ledger_list.append([('account ', account), ('alias', alias.lower())])
    # commodity information
    if 'pre_opening_ledger_json' not in fnames.keys():
        ledger_list.append([('commodity', 'INR'),
                            ('note', 'Indian Rupees'),
                            ('format', '\N{INDIAN RUPEE SIGN} 1,000.00'),
                            ('nomarket', ''),
                            ('default', '')])
    for _, code, name  in commodity_codes.itertuples():
        ledger_list.append([('commodity', code), ('note', name)])
    # opening money balances
    for _, account, amount, *_  in money_balance.itertuples():
        ledger_list.append([(opg_date, ' Opening balance as on ' + opg_date), 
                            (account, amount),
                            (opg_balance_account, )])
    # opening balances commodities
    for _, account, code, qty, cost  in commodity_bal.itertuples():
        ledger_list.append([(opg_date, ' Opening balance as on ' + opg_date), 
                            (account, qty, code, cost),
                            (opg_balance_account, )])
    return(ledger_list)

def ledger_list_to_ledger(ledger_list):
    with io.StringIO() as out:
        for (directive, details), *tail in ledger_list:
            # account information
            if re.match('account', directive):
                print(ledger_format('account_decl').format(details), file = out)
                for sub_directive in tail:
                      print(ledger_format('sub_directive').format(
                          *sub_directive), file = out)
            # commodity information
            elif re.match('commodity', directive):
                print(ledger_format('commodity_decl').format(details),
                      file = out)
                for sub_directive in tail:
                      print(ledger_format('sub_directive').format(
                          *sub_directive), file = out)
            # journal entries
            elif re.search('^[0-9]+', directive):
                print(ledger_format('date_line').format(directive, details),
                      file = out)
                for entry in tail:
                    if len(entry) == 1: # only account (amount is auto)
                        account, = entry
                        print(ledger_format('auto').format(account), file = out)
                    elif len(entry) == 2: # account and amount
                        account, amount = entry
                        print(ledger_format('standard').format(
                            account, amount), file = out)
                    elif len(entry) == 4: # commodity buy (account, qty, code, cost)
                        account, qty, code, cost = entry
                        print(ledger_format('commodity_buy').format(
                            account, qty, code, cost), file = out)
                    elif len(entry) == 5: # commodity sell (account, qty, code, cost, price)
                        account, qty, code, cost, price = entry
                        print(ledger_format('commodity_sell').format(
                            account, qty, code, cost, price), file = out)
                    else:
                        assert False, 'Entry has unknown length:' + str(entry)
            else:
                assert False, 'Unknown directive:' + directive
        return(out.getvalue())
        
def ledger_append(ledger, entry_list, entry_date):
    with io.StringIO(ledger) as out:
        out.seek(0, io.SEEK_END)
        for je in entry_list:
            if re.match(r'^\d\d', je[0]): # if the first line has a date, we use it as is
                print(je[0], file = out)
            else: # if the first line does not have a date, we prepend the default entry_date
                print(entry_date, je[0], file = out)
            for item in je[1:]:
                if len(item) == 2: # account and amount
                    account, amount = item
                    print(ledger_format().format(account, amount),
                          file = out)
                elif len(item) == 4:  # commodity buy (account, qty, code, cost)
                    account, units, code, cost = item
                    print(ledger_format('commodity_buy').format(
                        account, units, code, cost), file = out)
                elif len(item) == 5: # commodity sell (account, qty, code, cost, price)
                    account, qty, code, cost, price = item
                    print(ledger_format('commodity_sell').format(
                        account, qty, code, cost, price), file = out)
        return(out.getvalue())

class LedgerError(Exception):
    def __str__(self):
        return "Ledger file is not OK"
    
def ledger_check(ledger):
    # checks ledger for syntax errors using 'source' command
    if subprocess.run(['ledger', '-f', '-', 'source'],
                   input = ledger, stdout=subprocess.PIPE,
                   universal_newlines=True).returncode > 0:
        raise(LedgerError)
    
def ledger_command(ledger, commands, regex = [], strict = True):
    # run specified command on ledger and return output as a string
    ifstrict = ['--strict'] if strict else []
    ledger_check(ledger) # first check ledger for syntax errors
    return(subprocess.run(['ledger', '-f', '-'] + ifstrict + commands + regex,
                          input = ledger, stdout=subprocess.PIPE,
                          universal_newlines=True).stdout)

def ledger_balance(ledger, regex = [], strict = True):
    # run 'balance' command (at cost basis) and return result as a string
    # the imbalance is parsed and returned as a float for diagnostic purposes
    ledger_out = ledger_command(ledger, ['-B', 'balance'], regex, strict)
    imbalance = myfloat(io.StringIO(ledger_out).readlines()[-1])
    return(ledger_out, imbalance)

def ledger_balance_MV(ledger, pricedb, regex = [], strict = True):
    # run 'balance' command (at market value) and return result as a string
    # the imbalance is parsed and returned as a float for diagnostic purposes
    ledger_out = ledger_command(
        ledger, ['--price-db', pricedb, '-V', 'balance'], regex, strict)
    imbalance = myfloat(io.StringIO(ledger_out).readlines()[-1])
    return(ledger_out, imbalance)

def ledger_balances_df(ledger, regex = [], strict = True):
    # run 'balance' command (at cost basis) and parse result into pandas dataframe
    out = ledger_command(ledger, ['-B', '--flat', 'balance'], regex, strict)
    csv = io.StringIO(out.partition('---')[0].replace(',', ''))
    df = pd.read_csv(csv, sep = '\s+INR\s+', header = None, engine = 'python',
                     names = ['Amount', 'Account'])
    return df

def ledger_qty_basis_df(ledger, pricedb = None, regex = [], strict = True):
    # returns quantity balances of all commodities as a pandas dataframe
    # list of all commodities is obtained using the 'commodities' command
    # for each commodity, the 'balance' command is run without prices to get quantity balances
    # this command can take several seconds to run, so it reports progress regularly
    commodities = ledger_command(ledger, ['commodities'], regex, strict).split('\n')
    data = pd.DataFrame()
    nc = len(commodities)
    print('Computing quantities, cost and value of {:} "commodities"'.format(nc))
    n = 0
    for comm in commodities:
        comm = comm.replace('"', '')
        clist = ['-l', 'commodity=~/' + comm + '/', 'bal']
        if not comm in ['', 'INR']:
            d = {'commodity' : comm}
            s = ledger_command(ledger, clist, regex, strict)
            if s != '':
                d['qty'] = myfloat(s, comm)
                s = ledger_command(ledger, ['-B'] + clist, regex, strict)
                d['cost'] = myfloat(s)
                if pricedb is not None:
                    s = ledger_command(
                        ledger, ['-V', '--price-db', pricedb] + clist,
                        regex, strict)
                    d['value'] = myfloat(s)
                data = data.append(d, ignore_index=True)
        n += 1
        if n % 5 == 0: print('{:} of {:} commodities processed'.format(n, nc))
    print('Completed all {:} "commodities"'.format(nc))
    return data

def make_price_file(files, date):
    # read a bunch of price files and return a string with price entries in ledger's format
    # the price file is a csv file with two columns: code and price
    prices = pd.DataFrame()
    for f in files:
        prices = prices.append(pd.read_csv(f, header =0))
    with io.StringIO() as out:
        for _, code, price in prices.itertuples(): # the '_' is for the row name
            print(ledger_format('price').format(date, code, price), file = out)
        return out.getvalue()

class Numpy_int64_Encoder(json.JSONEncoder):
    # if a large number is an integer, numpy uses 64 bit integers instead of float
    # since json handles only 32 bit integers, we convert these into float
    def default(self, obj):
        if isinstance(obj, np.int64):
            return float(obj)
        # Let the base class default method handle the rest
        return json.JSONEncoder.default(self, obj)

def save_json(ledger_list, filename):
    # dump the ledger_list into a json file using the Numpy_int64_Encoder
    with open(filename, 'w') as out:
        json.dump(ledger_list, out, indent = 1, cls=Numpy_int64_Encoder)

