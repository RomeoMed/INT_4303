#
# Database connection object
#
from retrying import retry
import MySQLdb
import json
import logging


_logger = logging.getLogger("progress_tracker_api")


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
            _logger.error("DB error ---> exc_type: {}, exc_val: {}".format(exc_type, exc_val))
            _logger.error("DB Rolling Back transaction!")
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
    def execute_sql(self, sql: str, data: any) -> any:
        _logger.info("DB Executing: {}".format(sql))
        with _rollback(self.conn) as _db:
            _db.execute(sql, data)
            new_id = _db.lastrowid
        return new_id

    def delete(self, sql: str, data: any) -> any:
        _logger.info("DB Executing: {}".format(sql))
        with _rollback(self.conn) as _db:
            _db.execute(sql, data)

    def select_all(self, sql: str) -> any:
        query = 'SELECT * FROM {} '.format(sql)
        _logger.info("DB Executing: {}".format(query))
        with _rollback(self.conn) as _db:
            _db.execute(query)
            row = _db.fetchall()
        return row

    def select(self, query: str) -> any:
        _logger.info("DB Executing: {}".format(query))
        with _rollback(self.conn) as _db:
            _db.execute(query)
            result = _db.fetchall()
        return result

    def select_with_params(self, query: str, params: any) -> any:
        _logger.info("DB Executing: {}".format(query))
        with _rollback(self.conn) as _db:
            _db.execute(query, params)
        result = _db.fetchall()
        return result

    def select_into_list(self, query: str, params: any) -> any:
        _logger.info("DB Executing: {}".format(query))
        return_list = []
        with _rollback(self.conn) as _db:
            _db.execute(query, params)
        result = _db.fetchall()

        for res in result:
            count = len(res)
            counter = 1
            tmp_list = []
            while counter <= count:
                tmp_list.append(res[counter - 1])
                counter += 1
            return_list.append(tmp_list)

        return return_list

    def select_no_params(self, query: str) -> any:
        _logger.info("DB Executing: {}".format(query))
        with _rollback(self.conn) as _db:
            _db.execute(query)
        result = _db.fetchall()
        return self.convert_to_list(result)

    @staticmethod
    def convert_to_list(result) -> any:
        ret_list = []
        for res in result:
            tmp_list = []
            for i in res:
                tmp_list.append(i)
            ret_list.append(tmp_list)
        return ret_list

    def __exit__(self, ttype, value, traceback) -> None:
        """ Context manager exit. Commits transaction.

        We don't roll back if there is an exception, as that is handled in _rollback().
        """
        if ttype is None:
            _logger.info("DB query executed successfully, committing results")
            self.conn.commit()
