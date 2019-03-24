#
# Database connection object
#
from retrying import retry
from typing import Optional
import MySQLdb
import json
import logging


_logger = logging.getLogger("FinalProjectApp")
def retry_on_dberror(exception: Exception) -> bool:
    _logger.info("********retry_on_dberror")
    """ Used in the retrying decorator to retry queries if there is a database error.
    Args:
        exception (Exception): the exception to test.

    Returns:
        bool: True if the exception is a DatabaseError.
    """
    return isinstance(exception, MySQLdb.DatabaseError)


class _rollback(object):
    """ Mini class to ensure failed transactions are rolled back prior to a retry """
    _logger.info("ERROR-------->rolling back database")

    def __init__(self, conn):
        self.conn = conn

    def __enter__(self):
        return self.conn.cursor().__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.conn.rollback()


class Database(object):
    """ Database connection manager.

    This is accessed as the context manager 'transaction' defined below.
    """
    _conn = None

    def connect(self) -> None:
        """ Establishes a global database connection object.
        """
        _logger.info("Connecting to Database")
        with open('db_configs.json') as shh:
            secret = json.load(shh)

        if hasattr(self._conn, 'close'):
            self._conn.close()
        self._conn = MySQLdb.connect(host=secret.get('host'),
                                     port=secret.get('port'),
                                     db=secret.get('db'),
                                     user=secret.get('user'),
                                     password=secret.get('password'),
                                     connect_timeout=secret.get('connect_timeout')
                                     )
        self._conn.autocommit = False

    @property
    def conn(self) -> MySQLdb.connection:
        """ Property that lazily established, or reestablishes, a DB connection.

        Returns:
            Database connection
        """
        if not self._conn or self._conn.closed:
            self.connect()
        return self._conn

    def __enter__(self):
        return self

    @retry(retry_on_exception=retry_on_dberror, stop_max_delay=600000,
           wait_exponential_multiplier=1000, wait_exponential_max=10000)
    def execute_sql(self, sql: str, data: any):
        with _rollback(self.conn) as _db:
            _db.execute(sql, data)
            new_id = _db.lastrowid
        return new_id

    def delete(self, sql: str, data: any):
        with _rollback(self.conn) as _db:
            _db.execute(sql, data)

    def select_all(self, sql: str) -> any:
        query = 'SELECT * FROM {} '.format(sql)

        with _rollback(self.conn) as _db:
            _db.execute(query)
            row = _db.fetchall()
        return row

    def select(self, query: str) -> any:
        with _rollback(self.conn) as _db:
            _db.execute(query)
            result = _db.fetchall()
        return result

    def select_with_params(self, query: str, params: any) -> any:

        with _rollback(self.conn) as _db:
            _db.execute(query, params)
            result = _db.fetchall()
        return result

    # noinspection PyUnusedLocal,PyUnusedLocal
    def __exit__(self, ttype, value, traceback) -> None:
        """ Context manager exit. Commits transaction.

        We don't roll back if there is an exception, as that is handled in _rollback().
        """
        if ttype is None:
            self.conn.commit()
