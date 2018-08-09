#!/usr/bin/env python3

import json
import sqlite3
import time
import requests
import os


def registration(firstname, lastname, email, password, balance):
    connection = sqlite3.connect('master.db', check_same_thread=False)
    cursor = connection.cursor()
    print(firstname, lastname, email, password, balance)

    if True:
        cursor.execute("""INSERT INTO users(
                            firstname,
                            lastname,
                            email,
                            password,
                            balance
                        ) VALUES(
                        "{firstname}",
                        "{lastname}",
                        "{email}",
                        "{password}",
                        {balance});""".format(firstname=firstname, lastname=lastname, email=email, password=password, balance=float(balance)))
        connection.commit()
        cursor.close()
        connection.close()
        return 'You have successfully registered'

    else:
        return 'This email has already registered or is already being used, Please choose another one or go back to login screen'


def buy(ticker_symbol, trade_volume, guid):

    deep_link = 'http://dev.markitondemand.com/MODApis/Api/v2/Quote/json?symbol={ticker_symbol}'.format(ticker_symbol=ticker_symbol)
    response = json.loads(requests.get(deep_link).text)

    connection = sqlite3.connect('master.db', check_same_thread=False)
    cursor = connection.cursor()

    last_price = response['LastPrice']

    cursor.execute('SELECT balance FROM users WHERE pk=?;', (guid,))
    balance = cursor.fetchall()[0][0]

    friction = 12.00  # Amount of money it costs to make a trade per trade

    transaction_cost = (int(trade_volume) * float(last_price)) + friction
    unix_time = time.time()
    transaction_type = 1

    if transaction_cost > balance:
        return 'You have insufficient funds'
    else:
        new_balance = balance - transaction_cost
        cursor.execute('UPDATE users SET balance = {new_balance};'.format(new_balance=new_balance))
        connection.commit()

        cursor.execute('INSERT INTO transactions(unix_time, ticker_symbol, transaction_type, last_price, trade_volume, fk) VALUES({0}, "{1}", {2}, {3}, {4}, {5});'.format(unix_time, ticker_symbol, transaction_type, last_price, int(trade_volume), guid))
        connection.commit()

        cursor.execute('SELECT ticker_symbol FROM positions WHERE ticker_symbol = "{ticker_symbol}";'.format(ticker_symbol=ticker_symbol))
        position_exists = cursor.fetchone()

        if position_exists is None:
            cursor.execute('INSERT INTO positions(ticker_symbol, number_of_shares, vwap) VALUES("{ticker_symbol}", {number_of_shares}, {vwap});'.format(ticker_symbol=ticker_symbol, number_of_shares=int(trade_volume), vwap=last_price))
            connection.commit()

        else:
            cursor.execute('SELECT number_of_shares FROM positions WHERE ticker_symbol = "{ticker_symbol}";'.format(ticker_symbol=ticker_symbol))
            current_holdings = cursor.fetchall()[0][0]
            new_holdings = int(current_holdings) + int(trade_volume)

            cursor.execute('UPDATE positions SET number_of_shares = {number_of_shares} WHERE ticker_symbol = "{ticker_symbol}";'.format(number_of_shares=new_holdings, ticker_symbol=ticker_symbol))
            connection.commit()

            cursor.execute('SELECT vwap FROM positions WHERE ticker_symbol = "{ticker_symbol}";'.format(ticker_symbol=ticker_symbol))
            old_vwap = cursor.fetchall()[0][0]

            new_vwap = ((int(trade_volume) * last_price) + (current_holdings * old_vwap)) / new_holdings

            cursor.execute('UPDATE positions SET vwap = {vwap} WHERE ticker_symbol = "{ticker_symbol}";'.format(vwap=new_vwap, ticker_symbol=ticker_symbol))
            connection.commit()

            cursor.close()
            connection.close()
        return 'Trade is complete. You paid {last_price} on {trade_volume} shares of {ticker_symbol}'.format(last_price=last_price, trade_volume=trade_volume, ticker_symbol=ticker_symbol.upper())


def sell(ticker_symbol, trade_volume, guid):

    deep_link = 'http://dev.markitondemand.com/MODApis/Api/v2/Quote/json?symbol={ticker_symbol}'.format(ticker_symbol=ticker_symbol)
    response = json.loads(requests.get(deep_link).text)

    connection = sqlite3.connect('master.db', check_same_thread=False)
    cursor = connection.cursor()

    last_price = response['LastPrice']

    cursor.execute('SELECT balance FROM users WHERE pk=?;', (guid,))
    balance = cursor.fetchall()[0][0]

    friction = 12.00  # Amount of money it costs to make a trade per trade

    transaction_cost = friction
    new_balance = balance + (last_price * int(trade_volume)) - transaction_cost

    unix_time = time.time()
    transaction_type = 0

    if transaction_cost > balance:
        return 'You have insufficient funds'
    else:
        cursor.execute('SELECT number_of_shares FROM positions WHERE ticker_symbol = "{ticker_symbol}";'.format(ticker_symbol=ticker_symbol))
        current_holdings = cursor.fetchall()

        if len(current_holdings) < 1:
            return 'You don\'t have any shares to sell'
        else:
            current_holdings = current_holdings[0][0]

        new_holdings = current_holdings - int(trade_volume)
        # new_holdings and current_holdings are correct

        cursor.execute('INSERT INTO transactions(unix_time, ticker_symbol, transaction_type, last_price, trade_volume, fk) VALUES({0}, "{1}", {2}, {3}, {4}, {5});'.format(unix_time, ticker_symbol, transaction_type, last_price, int(trade_volume), guid))
        connection.commit()

        cursor.execute('SELECT ticker_symbol FROM positions WHERE ticker_symbol = "{ticker_symbol}";'.format(ticker_symbol=ticker_symbol))
        position_exists = cursor.fetchone()

        if position_exists is None or int(trade_volume) > current_holdings:
            return 'You don\'t have any shares to sell'

        else:

            cursor.execute('UPDATE positions SET number_of_shares = {number_of_shares} WHERE ticker_symbol = "{ticker_symbol}";'.format(number_of_shares=new_holdings, ticker_symbol=ticker_symbol))
            connection.commit()

            cursor.execute('SELECT vwap FROM positions WHERE ticker_symbol = "{ticker_symbol}";'.format(ticker_symbol=ticker_symbol))

            old_vwap = cursor.fetchall()[0][0]

            if new_holdings == 0:
                new_vwap = 0.0
            else:
                new_vwap = (old_vwap)
                print(new_vwap)

            cursor.execute('UPDATE positions SET vwap = {vwap} WHERE ticker_symbol = "{ticker_symbol}";'.format(vwap=new_vwap, ticker_symbol=ticker_symbol))
            connection.commit()

            cursor.execute('UPDATE users SET balance = {new_balance};'.format(new_balance=new_balance))
            connection.commit()

            cursor.close()
            connection.close()

        return 'Trade is complete. You sold {trade_volume} shares of {ticker_symbol} at {last_price}'.format(trade_volume=trade_volume, ticker_symbol=ticker_symbol.upper(), last_price=last_price)


def lookup(company_name):
    deep_link = 'http://dev.markitondemand.com/MODApis/Api/v2/Lookup/json?input={company_name}'.format(company_name=company_name)
    response = json.loads(requests.get(deep_link).text)
    ticker_symbol = response[0]['Symbol']
    return 'The ticker symbol for {company_name} is: '.format(company_name=company_name) + ticker_symbol


def quote(ticker_symbol):
    deep_link = 'http://dev.markitondemand.com/MODApis/Api/v2/Quote/json?symbol={ticker_symbol}'.format(ticker_symbol=ticker_symbol)
    response = json.loads(requests.get(deep_link).text)
    last_price = response['LastPrice']

    return 'The last trade price for {ticker_symbol} is {last_price}'.format(ticker_symbol=ticker_symbol.upper(), last_price=last_price)


def portfolio(guid):
    connection = sqlite3.connect('master.db', check_same_thread=False)
    cursor = connection.cursor()

    cursor.execute('SELECT balance FROM users WHERE pk=?;', (guid,))
    balance = cursor.fetchall()[0][0]

    cursor.execute('SELECT ticker_symbol,number_of_shares,vwap FROM positions WHERE pk=?;', (guid,))
    trades = cursor.fetchall()

    if trades == []:
        return 'You have no positions on.'
    else:
        # return 'Your current balance is ${balance} and your current positions are: {trades}'.format(balance=round(balance, 2), trades=trades)
        return 'Your current balance is ${balance}.'.format(balance=round(balance, 2))

    cursor.close()
    connection.close()


def pl(guid):

    connection = sqlite3.connect('master.db', check_same_thread=False)
    cursor = connection.cursor()

    start = 100000

    cursor.execute('SELECT SUM(vwap) FROM positions WHERE pk=?;', (guid,))
    svwap = ''
    xa = cursor.fetchall()
    if xa[0][0] != None:
        svwap = xa[0][0]
    else:
        return 'Your p/l is flat'
    # print(svwap)
        # print(xa)

    cursor.execute('SELECT SUM(number_of_shares) FROM positions WHERE pk=?;', (guid,))
    sshar = ''
    xa = cursor.fetchall()
    if xa[0][0] != None:
        sshar = xa[0][0]
    else:
        return 'Your p/l is flat'
    # sshar = cursor.fetchall()[0][0]
        # print(sshar)
        # print(svwap, sshar)

    cursor.execute('SELECT balance FROM users WHERE pk=?;', (guid,))
    balance = cursor.fetchall()[0][0]

    #print(svwap, sshar)

    pl1 = (svwap * sshar)
    pl2 = start - balance
    finpl = pl1 - pl2

    # print('svwap', svwap)
    # print('sshar', sshar)
    # print('pl1', pl1)
    # print('pl2', pl2)
    # print('finpl', finpl)

    if isinstance(pl1, float):
        return round(finpl, 2)

    else:
        return 'Your p/l is flat'

    # if float(finpl) == float(0) or finpl == 0:
    #     return 'Your p/l is flat'
    # else:
    #     return round(finpl, 2)

    # cursor.execute('SELECT count(*) FROM transactions;')
    # trans = cursor.fetchall()[0][0]

    # cursor.execute('SELECT SUM(last_price) FROM transactions WHERE transaction_type = 0;')
    # prbuy = cursor.fetchall()[0][0]

    # cursor.execute('SELECT SUM(last_price) FROM transactions WHERE transaction_type = 1;')
    # prsell = cursor.fetchall()[0][0]
    cursor.close()
    connection.close()
