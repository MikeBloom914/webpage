#!/usr/bin/env python3

import sqlite3

connection = sqlite3.connect('master.db', check_same_thread=False)
cursor = connection.cursor()

cursor.execute(
    """CREATE TABLE users(
        pk INTEGER PRIMARY KEY AUTOINCREMENT,
        firstname VARCHAR(32),
        lastname VARCHAR(32),
        email VARCHAR(32),
        password VARCHAR(32),
        balance FLOAT
    );"""
)

cursor.execute(
    """CREATE TABLE positions(
        pk INTEGER PRIMARY KEY AUTOINCREMENT,
        ticker_symbol VARCHAR,
        number_of_shares INTEGER,
        vwap FLOAT
    );"""
)

cursor.execute(
    """CREATE TABLE transactions(
        pk INTEGER PRIMARY KEY AUTOINCREMENT,
        fk INTEGER,
        unix_time FLOAT,
        transaction_type BOOL,
        last_price FLOAT,
        trade_volume INTEGER,
        ticker_symbol VARCHAR,
        FOREIGN KEY(fk) REFERENCES users(pk)
    );"""
)

cursor.close()
connection.close()
