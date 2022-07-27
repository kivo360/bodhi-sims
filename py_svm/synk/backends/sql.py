"""
These queries are used to create the tables and insert data into the database for the accounting system within for the duckdb arrow interface.

The primary reason for using SQL commands is to make it easier to port to other databases within the future. 
In all likelihood this will be the grounds for a large-scale agent-based modelling framework, a large-scale financial modelling framework, then (likely) a full-blown operations framework.

SQL commands can be transferred quickly.
"""

CREATE_ACCOUNT = """
CREATE TABLE IF NOT EXISTS accounts(
        id TEXT NOT NULL,
        episode VARCHAR, 
        address VARCHAR, 
        balance Numeric, 
        timestamp INTEGER, 
        PRIMARY KEY (id)
)"""
CREATE_STORAGE = """
CREATE TABLE IF NOT EXISTS storage (
        id TEXT NOT NULL DEFAULT gen_random_uuid(), 
        episode VARCHAR, 
        address VARCHAR, 
        slot VARCHAR, 
        value VARCHAR,
        vtype VARCHAR, 
        timestamp INTEGER, 
        PRIMARY KEY (id)
)
"""
# INSERT INTO accounts (episode, address, balance, timestamp)
# VALUES ({episode}, {address},{balance},{timestamp})


# two_x FLOAT GENERATED ALWAYS AS (2 * x) VIRTUAL
INSERT_ACCOUNT_STATE = """
INSERT INTO accounts (episode, address, balance, timestamp) VALUES ('{episode}', '{address}', {balance}, {timestamp}) 
"""
SELECT_ACCOUNT_ONE = "SELECT * FROM accounts  WHERE  episode = '{episode}' and address = '{address}' and timestamp = {timestamp} LIMIT 1"
SELECT_ACCOUNT_HIST = "SELECT * FROM accounts  WHERE  episode = '{episode}' and address = '{address}' order by timestamp desc"

# INSERT_ACCOUNT_STATE = """
# INSERT INTO accounts (episode, address, balance, timestamp) VALUES (?, ?, ?, ?) ON CONFLICT (episode, address, timestamp) DO UPDATE SET balance = accounts.balance
# """

INSERT_STORAGE = "INSERT INTO storage (episode, address, slot, value, vtype, timestamp) VALUES ('{episode}','{address}','{slot}','{value}','{vtype}',{timestamp})"


UPDATE_VALUE = """
INSERT INTO storage (episode, address, slot, value, timestamp) VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT (episode, address, slot, timestamp) DO UPDATE SET data = storage.value
"""


GET_STORAGE_ONE = """SELECT storage.slot, storage.value, storage.vtype, storage.timestamp 
FROM storage 
WHERE storage.episode = '{episode}' AND storage.address = '{address}'  ORDER BY storage.timestamp DESC LIMIT 1
"""
GET_STORAGE_HISTORY = """
SELECT storage.slot, storage.value, storage.vtype, storage.timestamp 
FROM storage 
WHERE storage.episode = '{episode}' AND storage.address = '{address}' ORDER BY storage.timestamp DESC
LIMIT 100 OFFSET 0
"""
