# Python helper code for [`Ledger`](http://ledger-cli.org/)

This repository contains some Python helper code to make more effective use of the [Plain Text Accounting](http://plaintextaccounting.org/) command line tool called [`Ledger`](http://ledger-cli.org/) for personal accounting. The motivation for this project is described in my blog post.

The typical use case for this helper code is that of generating the personal accounting largely from  bank statements, credit card statements, portfolio transaction statements from stock brokers, mutual funds and other financial firms. Assuming that the user has written code to analyse these statements semi-automatically and generate accounting entries, the helper code in this project will help prepare a complete set of accounting statements from these entries. 

The helper code in this project assumes the existence of a program `make_je_list.py` that does the hard work of conversion and analysis of bank and other statements. It is assumed that `make_je_list.py` represents a journal entry as a Python data structure, more specifically, a `list`  whose first element is the date and narration of the entry and the remaining elements are the line items of the entry each of which consists of an account name and amount (a Python `tuple`). The whole journal is simply a list of such journal entries. The helper code takes this list as its input and feeds it to `Ledger` to prepare the accounts. 

# `ledger_functions.py`

This module contains the following key functions:

* `ledger_list_to_ledger` converts  the  internal representation of the journal into a string suitable to be fed as an input into `Ledger`.

* `ledger_command` runs `Ledger` (using Python&rsquo;s `subprocess` module). The string returned by  `ledger_list_to_ledger` is fed into `Ledger` as its `stdin` as the input text file and the output from `Ledger` is read from its `stdout` and returned as a string. `Ledger` accepts a variety of commands  and options. `ledger_command` accepts a list of such arguments and passes them on to `Ledger`. In almost all cases, the `balance` command of `Ledger` is the one that is used. `Ledger` also accepts a regex to limit the processing only to account names that match the regex. We use this quite frequently.

* `ledger_balance` runs `ledger_command` with the `balance` command on a set of accounts (specified as a regex)  and returns its output as a string. It also parses the last line of its output to obtain the net balance of these accounts as a numeric value. If no regex is given (all accounts are processed), the net balance must be zero as a fundamental principle of double entry accounting, and we often test for this as a sanity check. All balances are computed on the historical cost basis (the `-B` option to `Ledger`)

* `ledger_balance_MV` is similar to `ledger_balance` except that all items are valued at market prices specified in a price data base that is provided to this function. This function uses the `-V` option while invoking `Ledger`.

* `ledger_balances_df` is similar to `ledger_balance` except that the output is parsed into a `pandas` `DataFrame`.

* `ledger_qty_basis_df` generates a statement of the quantities, cost and market value of each individual stock or mutual fund. The only way that I could find to accomplish this was to run `Ledger` three times for each &ldquo;commodity&rdquo; (stock or mutual fund) which could requires a few hundred `Ledger` runs in all. The function reports its progress regularly (`k of n commodities processed`) so that the user does not think that the program is hanging.

* `save_json` saves the internal (Python list) representation of the journal as  a [`JSON`](http://www.json.org/) file so that we can avoid parsing the `Ledger` text file if ever a need arises in future to modify the journal in any way. The function uses a custom encoder because if a large number is an integer, `numpy` uses 64 bit integers instead of `float` but `JSON` handles only 32 bit integers. The custom encoder turns 64 bit integers into float.

# `prepare_accounts.py`

The module `prepare_accounts.py` uses the ledger functions discusses above to go through the whole process of preparing the accounts including income statement, balance sheet and the annual closing entries. The key steps in this process are:

* Read the opening ledger, call `make_je_list.py` to obtain the journal entries for the year, append these entries to get the closing ledger and prepare Trial Balance

* To prepare an income statement and balance sheet, we first find the net balance of all income and expense accounts and transfer this balance to equity. Printing the balance of all income, expense and the surplus account gives us the income statement:

* Then printing the balances of all asset, liability and equity accounts gives us the balance sheet. This can be done on cost basis and on market value basis.
 
* A cash flow statement (what I prefer to call &ldquo;deployment of savings&rdquo;) is prepared by computing the difference between the closing and opening balance sheets.

* Thereafter a full closing of the year&rsquo;s accounts is achieved by reducing every income statement account to zero balance to start the next year on a clean slate.

# Data path

The module `prepare_accounts.py`  takes one command line argument &ndash; the data path where all the data files (for example, the opening ledger and the market price data) reside. The output files (for example, the closing ledger in `Ledger` and `JSON` format) are also created in this folder. So it is possible to have a separate folder for each year without any conflict. The opening ledger file in each year can be a symlink to the closing ledger of the previous year. The module `prepare_accounts.py` searches for Python modules both in its own folder and in the data folder. So the module `make_je_list.py` (see below) can be either in the same folder as `prepare_accounts.py` or it can be in the data folder. In the former case, it can import Python modules from the data folder so that the generic code is in the main folder and the year specific data in the data folder.

# `make_je_list.py`

Both `ledger_functions.py` and `prepare_accounts.py` are generic and can be used with minimal modifications by different users, but `make_je_list.py` must be specific to each user. It is the code that creates the journal entries for the year and would depend on the format in which the user&rsquo;s bank (and other financial firms) provides their statements as well as the specific heads of income and expenses of each user. My own `make_je_list.py` contains too much personal information for me to post it as an example file but a few details about how it works is given below.  My banks and other financial services firms provide statements in many different formats &ndash; XLS, TXT, HTML and PDF. All these formats other than PDF can be read by a spreadsheet program which can then save them as CSV text files. PDF files can also be converted to text using good old `ghostscript` (`gs -dBATCH -dNOPAUSE -sDEVICE=txtwrite`). My `make_je_list.py` reads these various CSV files, and uses regular expressions  to analyse these statements semi-automatically and generate accounting entries. I say semi-automatically because it has some interactive parts which require the user to choose the account name for entries where the regular expressions are not sufficient.

# example

The example folder contains some data files and a `make_je_list.py` which contains only a few journal entries (these are all hard coded). To run this example, `cd` to the folder containing  prepare_accounts.py and run the following command to get the opening and closing balance sheets, income statements, cash flow statements and also generate the opening and closing ledger files.

`python prepare_accounts.py example`


