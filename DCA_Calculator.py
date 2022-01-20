from sqlite3 import Row
from unicodedata import name, numeric
import requests
import pandas as pd
import alpha_vantage.timeseries as TimeSeries
import time
from pprint import pprint
import matplotlib.pyplot as plt
import datetime


api_key = "PBR5G584UX6Q8AQZ"
api_URL = 'https://www.alphavantage.co/query'
api_call_counter = 0
api_timeout_isEngaged = False

def main_menu ():
    print("Press E to Edit Your Portfolio")
    print("Press V to View Your Portfolio")
    print("Press C to Find Current Price of a Single Stock")
    print("Press P for more information on Prices")
    choice = input()
    if choice == "e":
        edit_portfolio()
    if choice == "v":
        #print(get_portfolio())
        view_portfolio()
    if choice == "c":
        print("Enter the Ticker Symbol You Would Like to Check")
        pprint(get_current_price(input()))
        main_menu()
    if choice == "p":
        print("Press D to view Daily Prices")
        print("Press W to view Weekly Prices")
        print("Press M to view Monthly Prices")
        interval_choice = input()

        print("Would you like to View Adjusted Prices? (adjusted for dividends, splits, etc)")
        print("Y/N")
        adjusted = input()

        print("Enter the Ticker Symbol You Would Like to Check")
        ticker_symbol = input()

        if interval_choice == 'w':
            if adjusted == 'y':
                pprint(get_closing_price(ticker_symbol, "Weekly_Adjusted"))
                graph_closing_price(ticker_symbol, "Weekly_Adjusted")
            else:
                pprint(get_closing_price(ticker_symbol, "Weekly"))
                graph_closing_price(ticker_symbol, "Weekly")

        print("Enter the Ticker Symbol You Would Like to Check")
        ticker_symbol = input()
        pprint(get_closing_price(ticker_symbol, "Weekly"))
        graph_closing_price(ticker_symbol, "Weekly")
        main_menu()


def api_timeout():
    start = 0
    global api_call_counter
    if api_call_counter >= 5 and 60 <= (60 - time.time() - start):
        api_call_counter = 0

    if api_call_counter == 0:
        start = time.time()
        api_call_counter += 1
        calls_left = str(5-api_call_counter)
        print(calls_left + " API CALLS LEFT")

    elif 0 < api_call_counter < 5 and 60 > (60 - time.time() - start):
        api_call_counter += 1
        calls_left = str(5-api_call_counter)
        print(calls_left + " API CALLS LEFT")

    if api_call_counter >= 5 and 60 > (60 - time.time() - start):
        time_left = str(60 - start) + " seconds left"
        print("NO API CALLS LEFT")
        print(time_left)
    
    
def api_call_url(ticker_symbol,function):
    return api_URL + '?function=' + function + '&symbol=' + ticker_symbol + '&apikey=' + api_key 


def determine_time_period(time_period):
    time_period = time_period.strip()
    time_period = time_period.upper()

    if time_period == "DAILY":
        return "TIME_SERIES_DAILY" ,'Daily Time Series'
    elif time_period == "WEEKLY":
        return "TIME_SERIES_WEEKLY" ,'Weekly Time Series'
    elif time_period == "MONTHLY":
        return "TIME_SERIES_MONTHLY" ,'Monthly Time Series' 
    elif time_period == "DAILY_ADJUSTED":
        return "TIME_SERIES_DAILY_ADJUSTED" ,'Daily Adjusted Time Series'
    elif time_period == "WEEKLY_ADJUSTED":
        return "TIME_SERIES_WEEKLY_ADJUSTED" ,'Weekly Adjusted Time Series'
    elif time_period == "MONTHLY_ADJUSTED":
        return "TIME_SERIES_MONTHLY_ADJUSTED" ,'Monthly Adjusted Time Series'


def get_closing_price (ticker_symbol, time_period):
    ticker_symbol = ticker_symbol.strip()
    ticker_symbol = ticker_symbol.upper()

    function, time_period_price_key = determine_time_period(time_period)
    r = requests.get(api_call_url(ticker_symbol, function))
    if api_timeout_isEngaged:
        api_timeout()
    data = r.json()
    data = data[time_period_price_key]

    weekly_prices_list = []
    date_list = []
    for key in data.keys():
        each_weeks_data = data[key]
        
        weekly_prices_list.append(float(each_weeks_data['4. close']))
        date_list.append(str(key))

    weekly_prices_list.reverse()

    #reverse the list of string of dates
    date_list.reverse()
    date_time_list = []

    #convert each str to datetime objects
    for each_date in date_list:
        each_date = datetime.datetime.strptime(str(each_date), '%Y-%m-%d')
        date_time_list.append(each_date)

    #make dataframe of dates and prices
    data_frame = pd.DataFrame(
        {'Prices': weekly_prices_list,
         'Date': date_time_list})

    return data_frame


def get_current_price (ticker_symbol):
    ticker_symbol = ticker_symbol.strip()
    ticker_symbol = ticker_symbol.upper()
    function = "GLOBAL_QUOTE"
    r = requests.get(api_call_url(ticker_symbol, function))

    if api_timeout_isEngaged:
        api_timeout()

    data = r.json()
    data = data['Global Quote']
    return data['05. price']


def edit_portfolio ():
    #read csv
    portfolio = pd.read_csv('portfolio.csv', header=0)
    #ticker_input_prompt
    print("Please Enter the New Tickear Symbols Separated by Commas")
    ticker_list = input()
    ticker_list = ticker_list.split(",")
    
    #capitalize and trim spaces from entries
    tl_length = len(ticker_list)
    i = 0
    while i < tl_length:
        ticker_list[i].strip()
        ticker_list[i] = ticker_list[i].upper() 
        if len(ticker_list[i]) <= 2:
            ticker_list.remove(ticker_list[i])
            tl_length -= 1
        #adds string to portfolio
        portfolio.loc[len(portfolio)] = ticker_list[i]
        i += 1

    #turn df into strings and remove duplicates
    portfolio = portfolio.astype('str')
    portfolio.drop_duplicates(subset=None, keep='first', inplace=True)

    #saves portfolio to csv
    portfolio.to_csv('portfolio.csv', index=False)

    #return back to main menu
    main_menu()
    

def get_portfolio ():
    portfolio = pd.read_csv('portfolio.csv', header=None)
    portfolio = portfolio.astype('str')
    prices = []
    for line in portfolio[0]:
        prices.append(get_current_price(line))
    portfolio[1] = prices
    return portfolio

def view_portfolio ():
    portfolio = pd.read_csv('portfolio.csv', header=None)
    portfolio = portfolio.astype('str')

    ticker_list = portfolio[0].values.tolist()
    list_of_lists = []
    col_names = []

    for ticker in ticker_list:
        dataframe = get_closing_price(ticker, "Weekly_Adjusted")
        col_names = dataframe['Date'].tolist()
        list_to_add = reversed(dataframe['Prices'].tolist())
 
        list_of_lists.append(list_to_add)

    
    
    df = pd.DataFrame(list_of_lists, columns = reversed(col_names), index=ticker_list)
    df = df.fillna(0)
    df = df.transpose()
    df["Sum"] = df.sum(axis = 1)

    plt.plot(df.index[0:260], df["Sum"])
    plt.ylabel("Prices")
    #plt.title(ticker_symbol.upper() + " " + time_period + " Prices")
    plt.show()

    print(df)

def graph_closing_price (ticker_symbol, time_period):
    data_frame = get_closing_price(ticker_symbol, time_period)
    #plots 260 weeks (5 years) from the last date of the dataframe (most recent) 
    plt.plot(data_frame.loc[len(data_frame)-261:len(data_frame)-1,'Date'], data_frame.loc[len(data_frame)-261:len(data_frame)-1,'Prices'])
    plt.xlabel("Date from " + str(data_frame.loc[len(data_frame)-261,'Date']).split()[0] + ' to ' + str(data_frame.loc[len(data_frame)-1,'Date']).split()[0])
    plt.ylabel("Prices")
    plt.title(ticker_symbol.upper() + " " + time_period + " Prices")
    plt.show()
#---------------------------------------------------------------------

main_menu()


