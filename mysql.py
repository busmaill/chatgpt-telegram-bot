import mysql.connector
from mysql.connector import errorcode
from typing import List


class MySQL:
    def __init__(self, config):
        self._config = config
        self._cnx = None

    def connect(self):
        try:
            self._cnx = mysql.connector.connect(**self._config)
            print("Connected to MySQL database")
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                print("Something is wrong with your username or password")
            elif err.errno == errorcode.ER_BAD_DB_ERROR:
                print("Database does not exist")
            else:
                print(err)

    def close(self):
        if self._cnx is not None and self._cnx.is_connected():
            self._cnx.close()
            print("Connection to MySQL database closed")

    def execute_query(self, query: str, data: List = None):
        cursor = self._cnx.cursor()
        try:
            cursor.execute(query, data)
            return cursor.fetchall()
        except mysql.connector.Error as err:
            print(f"Error executing query: {err}")
        finally:
            cursor.close()
