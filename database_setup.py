import sqlite3

conn = sqlite3.connect('submissions.db')
cursor = conn.cursor()

#create table 
cursor.execute('''
CREATE TABLE IF NOT EXISTS submissions (
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               name TEXT NOT NULL, 
               email TEXT NOT NULL
               )
               ''')

#create feedback table 
cursor.execute('''
CREATE TABLE IF NOT EXISTS feedback (
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               name TEXT NOT NULL,
               message TEXT NOT NULL               
               )
               ''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               name TEXT NOT NULL,
               email TEXT NOT NULL UNIQUE,
               password TEXT NOT NULL
               )


''')

conn.commit()
conn.close()
