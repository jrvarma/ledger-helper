from annual_settings import year_end

je_list=[]
        
# Income tax of 20000 was deducted from salary of 80000 and the balance was deposited in bank
sal = [(year_end, "Salary Income"),
      ('sbi',60000),
      ('income tax', 20000),
      ('salary', -80000)]
je_list += [sal]

# 10000 was withdrawn from bank and spent. Credit card dues of 15000 paid by cheque
exp = [(year_end, "Expenses for the year"),
       ("cash exp", 10000),
       ("cc exp", 15000),
       ("sbi", -25000)]
je_list += [exp]

# dividend of 5000 credited to bank account
div = [(year_end, "Dividend received "),
       ("sbi", 5000),
       ("dividends", -5000)]
je_list += [div]

## Bought 20 shares of ABC at 78 per share
inv = [("2014-09-08", "Stock Purchase"),
     ('sbi', -7800), ('stock', 10, 'ABC', 7800)]

je_list += [inv]

