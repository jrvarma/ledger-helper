# Python helper code for [`Ledger`](http://ledger-cli.org/)

 I have long desired a personal accounting software that can be populated with data from downloaded bank statements and other source documents with minimal manual intervention. [`GnuCash`](http://www.gnucash.org/) is a widely used open source software with enough capability to be used by small businesses. However, its ability to import data from other formats is very limited. It can import from [`Quicken`](https://en.wikipedia.org/wiki/Quicken_Interchange_Format), but since `Quicken` is not a proper [double entry](https://en.wikipedia.org/wiki/Double-entry_bookkeeping_system) software, this facility is not particularly useful. So even if I convert a downloaded bank statement into accounting entries, I still have to manually input these into `GnuCash`. That is more work than I am willing to do.

A couple of months back, I discovered [Plain Text Accounting](http://plaintextaccounting.org/) and in particular [`Ledger`](http://ledger-cli.org/). The brilliant idea behind this class of software is that the entire accounting data resides in a plain text file as a series of journal entries. Importing data into `Ledger` is just a question of writing text files. It is hard to imagine anything simpler than this. The only reports that `Ledger` produces are again plain text and parsing them is not difficult to anybody familiar with [regular expressions](https://en.wikipedia.org/wiki/Regular_expression).

Suddenly, personal accounting became something that could be done relatively painlessly. I do not participate in the underground (black money) economy and so all my income flows through my bank account. Most of my large expenses are paid for through credit cards, cheques or online transfers. All of this is visible in my bank statements that I can download from the web sites of my banks or in credit card statements that also come to me by email. If I buy or sell stocks or mutual funds, I get statements by email from the broker, or the mutual fund or  from the depository. The only thing that is left out is the relatively small expenses incurred in cash. Since I am too lazy to manually record and keep track of these, I use the simple accounting policy of treating cash withdrawals as expenses even though they may not yet have been spent. This may appear strange to corporate accountants, but is not unreasonable. If a company gets 5,000 copies of its letterhead printed, it expenses them in the same period even though 4,000 of those may still be in stock. I so no reason to treat pieces of paper printed by the central bank any differently. Accountants who might want to object can be silenced with one magic word &ndash; &ldquo;materiality&rdquo;. In any case, my personal accounting is not subject to any accounting standards.

So I choose to base all my personal accounting only on the statements received from banks and other various financial firms. These statements come in many different formats &ndash; XLS, TXT, HTML and PDF. All these formats other than PDF can be read by a spreadsheet program which can then save them as CSV text files. PDF files are harder, but over a period of time, I have figured out that I can extract the text from these file and then use regular expressions to parse this text into CSV files. (After trying various PDF conversion tools I have found that good old `ghostscript` does the best job: even if the PDF file is ill-formed or slightly damaged, `gs -dBATCH -dNOPAUSE -sDEVICE=txtwrite` will produce usable text.) 

I decided to use Python to manage the whole process from parsing bank statements to creating the journal entries to running ledger and generating balance sheets and other statements. CSV files can be read into a Python `pandas` DataFrame which can be sliced and diced in many ways quite easily. It is quite straightforward to use a series of regular expressions to determine the journal entries for each transaction. For example, the regular expression `ATM WDL` identifies cash withdrawals in one of my bank accounts. To identify online purchases , I use a long  regular expression, a part of which reads as follows:

`(INB Flipkart)|(INB Avenues)|(INB Indigo)|(INB Amazon)||(INB Makemytrip)|(INB EBAY)`

Using such techniques and some manual intervention, each line item in each source document  is turned into a journal entry. I choose to represent journal entry as a Python `list`  whose first element is the date and narration of the entry and the remaining elements are the line items of the entry each of which consists of an account name and amount (a Python `tuple`). The whole journal is simply a list of such journal entries. This internal representation will be turned into a `Ledger` input text file at a later stage. 

Like all modern accounting software, `Ledger` allows multiple currencies and &ldquo;commodities&rdquo;. This becomes relevant for securities transactions. When you buy shares, you can record the company code (&ldquo;commodity&rdquo;), he number of shares and the unit cost in addition to the total purchase price. This line item has four pieces of information. When you sell shares, you can record the number of shares, the cost price, and the selling price so that `Ledger` can calculate the gain or loss and also correctly keep track of the number of shares still in hand. This line item has five pieces of information. 

In addition to transactions, `Ledger` also needs to be told about the account names (and their aliases) as well as all the currencies/commodities that will be used. Account names are typically hierarchical like `Assets:Bank Accounts:State Bank of India` where the `:` separates different levels of the hierarchy. `Assets:Bank Accounts` will represent the total of all the bank accounts, while `Assets` will provide the total of all kinds of assets. It is also possible to create an alias `SBI` for `Assets:Bank Accounts:State Bank of India`. I define these in a CSV file (one time effort) and read them into a Python pandas DataFrame. The account declaration is stored in a list like a journal entry except that in the first element of this list, instead of an entry date, we put the string &ldquo;account&rdquo;. Commodity declarations are handled similarly. This mirrors how the declarations are written in the `Ledger` input text file.

We are now ready to create the input text file for `Ledger`. The Python code for creating the input text file for `Ledger` is very simple:


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


The function `ledger_format` returns a suitable format string. There is also a function  `ledger_command` simply runs `Ledger` (using Python&rsquo;s `subprocess` module). The string returned by  `ledger_list_to_ledger` is fed into `Ledger` as its `stdin` as the input text file and the output from `Ledger` is read from its `stdout` and returned as a string. 

A key step in preparing income statements and balance sheet is the computation of the net balance of a set of accounts. The Python code that I use for this simply runs `Ledger` and parses the last line of its output to obtain this value. The code is as follows:

    money = 'INR' # default currency is Indian Rupee (INR)

    def myfloat(s, commodity = money):
        s = s.replace(',', '') # remove thousand separators (,)
        s = re.sub('\s' + commodity + '\s.*$', '', s) # remove trailing commodity name with spaces
        s = re.sub('\s"' + commodity + '"\s.*$', '', s) # remove trailing quoted commodity name with spaces
        return float(s) # the string s is now numeric and can be converted using float
            
    def ledger_balance(ledger, regex = [], strict = True):
        ledger_out = ledger_command(ledger, ['-B', 'balance'], regex, strict)
        imbalance = myfloat(io.StringIO(ledger_out).readlines()[-1])
        return(ledger_out, imbalance)

With these functions in place, the preparation of a trial balance consists simply of concatenating the opening ledger and the new journal entries for the year and running ledger on this:

    # Trial Balance after updating ledger with entries for the year 
    ledger_list = opening_ledger_list + je_list # this is imported from make_je_list
    ledger = ledger_list_to_ledger(ledger_list)
    ledger_balance_out, imbalance = ledger_balance(ledger)
    assert imbalance == 0

To prepare an income statement and balance sheet, we first find the net balance of all income and expense accounts and transfer this balance to equity. Printing the balance of all income, expense and the surplus account gives us the income statement:

    # Split Trial Balance into Income Statement and Balance Sheet with closing entry
    income_statement_accounts = ['expense', 'income', 'surplus']
    balance_sheet_accounts = ['assets' , 'equity']

    surplus = ledger_balance(ledger, regex = income_statement_accounts)[1]
    year_end_entry = [(year_end, "Year end transfer of surplus into equity"),
                      ('surplus', -surplus), (annual_savings_account, surplus)]
    closing_ledger_list = ledger_list + [year_end_entry]
    closing_ledger = ledger_list_to_ledger(closing_ledger_list)
    
    # Income statement (after closing entry, this has zero balance)
    income_statement = ledger_balance(closing_ledger, regex = income_statement_accounts)[0]
    print('Income Statement\n' + income_statement)

Then printing the balances of all asset, liability and equity accounts gives us the balance sheet.


    # Balance Sheet (after closing entry, this balance sheet tallies)
    balance_sheet, imbalance = ledger_balance(closing_ledger, regex = balance_sheet_accounts)
    assert imbalance == 0
    print('Balance Sheet\n' + balance_sheet)
    
To get a market value balance sheet, I use a `ledger_balance_MV` function which uses the argument list `['--price-db', pricedb, '-V', 'balance']` where `ledger_balance` uses `['-B', 'balance']`.
    
A cash flow statement (what I prefer to call &ldquo;deployment of savings&rdquo;) can be prepared by computing the difference between the closing and opening balance sheets.

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

Thereafter a full closing of the year&rsquo;s accounts is achieved by reducing every income statement account to zero balance to start the next year on a clean slate

    income_statement_df = ledger_balances_df(closing_ledger, regex = income_statement_accounts)
    closingje = [(year_end, 'Year end closure of income statement')] +\
                [(account, -amount) for (_, amount, account)
             in income_statement_df.itertuples()]
    post_closing_ledger_list = closing_ledger_list + [closingje]

What I found hardest to do was to generate a statement of the quantities, cost and market value of each individual stock or mutual fund. The only way that I could find was to run `Ledger` three times for each &ldquo;commodity&rdquo; (stock or mutual fund) which could requires a few hundred `Ledger` runs in all. The code is as follows:

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

That completes the accounting for the year. To preserve a full record of the entire process, and also to facilitate next year&rsquo;s accounting, it is desirable to save the opening and closing ledgers and also all the output produced. It is also a good idea to save the internal (Python list) representation of the journal. The simplest way to do this is to use a [`JSON`](http://www.json.org/) file so that we can avoid parsing the `Ledger` text file if ever a need arises in future to modify the journal in any way. Python can write `JSON` files, but I found it necessary to use a custom encoder:

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

All of this adds up to about 500 lines of Python in addition to another couple of hundred lines of code to parse all the source documents. But all this is a one time effort as practically all the code is reusable from year to year.
