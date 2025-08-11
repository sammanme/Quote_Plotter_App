import sqlite3
from typing import List, Tuple, Optional
from datetime import datetime, timezone, timedelta
import logging
import pandas as pd
from pydantic import field_validator

logger = logging.getLogger(__name__)

class QuoteDatabase:
    def __init__(self, db_path="quotes.db"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.execute("PRAGMA foreign_keys = ON")

        self._create_tables()

    def _create_tables(self):
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            broker TEXT NOT NULL,
            symbol TEXT NOT NULL,
            archive_name TEXT NOT NULL,
            start_time INTEGER NOT NULL,
            end_time INTEGER NOT NULL
        );
        """)
    
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS quotes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            timestamp INTEGER NOT NULL,
            bid REAL NOT NULL,
            ask REAL NOT NULL,
            FOREIGN KEY(session_id) REFERENCES sessions(session_id),
            UNIQUE(session_id, timestamp)
        )
        """)
        self.conn.commit()

    def session_exists(self, session_id: str) -> bool:
        query = "SELECT 1 FROM sessions WHERE session_id = ? LIMIT 1"
        cursor = self.conn.execute(query, (session_id,))
        return cursor.fetchone() is not None

    # -------- Insertion Methods --------

    def insert_session(self, session_data: Tuple[str, str, str, str, int, int]):
        logger.info(f"Inserting session: {session_data[0]}")
        """Insert a session: (session_id, broker, symbol, archive_name, start_time, end_time)"""
        self.conn.execute("""
            INSERT INTO sessions (session_id, broker, symbol, archive_name, start_time, end_time)
            VALUES (?, ?, ?, ?, ?, ?)
        """, session_data)
        self.conn.commit()
        logger.info(f"Inserted session: {session_data[0]}, time range: {session_data[4]} to {session_data[5]}")

    def insert_quotes_bulk(self, session_id: str, quotes: List[Tuple[int, float, float]]):
        if not quotes:
            logger.warning(f"Skipped empty quote list for session {session_id}")
            return

        query = """
        INSERT INTO quotes (session_id, timestamp, bid, ask)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(session_id, timestamp)
        DO UPDATE SET
            bid = excluded.bid,
            ask = excluded.ask
        """
        try:
            self.conn.executemany(query, [(session_id, *q) for q in quotes])
            self.conn.commit()
            logger.info(f"Quotes inserted successfully for session {session_id} ({len(quotes)} quotes)")
        except Exception as e:
            logger.error(f"Error inserting quotes for session {session_id}: {e}", exc_info=True)

    # -------- Fetching Methods --------

    def fetch_quotes(
        self,
        broker: Optional[str] = None,
        symbol: Optional[str] = None,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None
    ) -> List[Tuple[str, str, float, float]]:
        query = """
        SELECT q.session_id, q.timestamp, q.bid, q.ask
        FROM quotes q
        JOIN sessions s ON q.session_id = s.session_id
        WHERE 1=1
        """
        params = []

        if broker is not None:
            query += " AND s.broker = ?"
            params.append(broker)
        if symbol is not None:
            query += " AND s.symbol = ?"
            params.append(symbol)
        if start_time is not None:
            query += " AND q.timestamp >= ?"
            params.append(start_time)
        if end_time is not None:
            query += " AND q.timestamp <= ?"
            params.append(end_time)

        cursor = self.conn.execute(query, params)
        results = cursor.fetchall()
        
        def to_iso(ts: int) -> str:
            if ts > 1e12:
                ts = ts / 1000
            return datetime.fromtimestamp(ts / 1000, tz=timezone.utc).isoformat().replace("+00:00", "Z")
        
        return[
            (session_id, to_iso(timestamp), bid, ask)
            for session_id, timestamp, bid, ask in results
        ]



    def get_all_brokers(self) -> List[str]:
        cursor = self.conn.execute("SELECT DISTINCT broker FROM sessions")
        return [row[0] for row in cursor.fetchall()]
    

    def get_symbols_by_broker(self, broker: str) -> List[str]:
        cursor = self.conn.execute("""
        SELECT DISTINCT symbol FROM sessions
        WHERE broker = ?
        """, (broker,))
        return [row[0] for row in cursor.fetchall()]
    
    
    def get_brokers_and_symbols(self):
        cursor = self.conn.execute("SELECT DISTINCT broker FROM sessions")
        brokers_list = [row[0] for row in cursor.fetchall()]

        result = {}
        for broker in brokers_list:
            result[broker] = self.get_symbols_by_broker(broker)
        return result

    def get_dates_by_broker_symbol(self, broker: str, symbol: str) -> List[str]:
        cursor = self.conn.execute("""
        SELECT DISTINCT DATE(q.timestamp / 1000, 'unixepoch')
        FROM quotes q
        JOIN sessions s ON q.session_id = s.session_id
        WHERE s.broker = ? AND s.symbol = ?
        ORDER BY 1
        """, (broker, symbol))
        return [row[0] for row in cursor.fetchall() if row[0] is not None]

    def get_sessions_by_date(self, broker: str, symbol: str, date: str) -> List[str]:
        cursor = self.conn.execute("""
        SELECT DISTINCT s.session_id
        FROM sessions s
        JOIN quotes q ON s.session_id = q.session_id
        WHERE s.broker = ? AND s.symbol = ? AND DATE(q.timestamp / 1000, 'unixepoch') = ?
        """, (broker, symbol, date))
        return [row[0] for row in cursor.fetchall()]

    def get_quotes_by_session(self, session_id: str) -> List[Tuple[str, float, float]]:
        cursor = self.conn.execute("""
        SELECT datetime(timestamp, 'unixepoch') as ts, bid, ask
        FROM quotes
        WHERE session_id = ?
        ORDER BY timestamp
        """, (session_id,))
        return cursor.fetchall()

    def get_sessions_by_date_range(self, broker: str, symbol: str, date: str) -> List[str]:
        cursor = self.conn.execute("""
        SELECT session_id
        FROM sessions
        WHERE broker = ? AND symbol = ? AND DATE(start_time, 'unixepoch') <= ? AND DATE(end_time, 'unixepoch') >= ?
        ORDER BY start_time
        """, (broker, symbol, date, date))
        return [row[0] for row in cursor.fetchall()]
    
    def get_data(self, broker_a, symbol_a, broker_b, symbol_b, limit=1000, time_range_hours='all'):
        try:
            # Debug: Check if brokers and symbols exist
            available_brokers = pd.read_sql_query("SELECT DISTINCT broker FROM sessions", self.conn)['broker'].tolist()
            available_symbols = pd.read_sql_query("SELECT DISTINCT symbol FROM sessions", self.conn)['symbol'].tolist()
            if broker_a not in available_brokers or broker_b not in available_brokers:
                print(f"Broker not found: broker_a={broker_a}, broker_b={broker_b}, available={available_brokers}")
                return pd.DataFrame()
            if symbol_a not in available_symbols or symbol_b not in available_symbols:
                print(f"Symbol not found: symbol_a={symbol_a}, symbol_b={symbol_b}, available={available_symbols}")
                return pd.DataFrame()

            # Base query
            query = """
            SELECT q.session_id, q.bid, q.ask, q.timestamp, s.broker, s.symbol
            FROM quotes q
            JOIN sessions s ON q.session_id = s.session_id
            WHERE (
                (s.broker = ? AND s.symbol = ?) OR
                (s.broker = ? AND s.symbol = ?)
            )
            """
            params = [broker_a, symbol_a, broker_b, symbol_b]

            # Add time range filter if not 'all'
            if time_range_hours != 'all':
                current_time_ms = int(datetime.now().timestamp() * 1000)
                time_range_ms = int(time_range_hours) * 3600 * 1000  # Convert hours to milliseconds
                query += " AND q.timestamp >= ?"
                params.append(current_time_ms - time_range_ms)

            query += " ORDER BY q.timestamp DESC LIMIT ?"
            params.append(limit)

            df = pd.read_sql_query(query, self.conn, params=tuple(params))
            if df.empty:
                print(f"No data returned for query: broker_a={broker_a}, symbol_a={symbol_a}, "
                      f"broker_b={broker_b}, symbol_b={symbol_b}, time_range={time_range_hours}")
                return pd.DataFrame()

            # Convert Unix epoch milliseconds to datetime
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms', errors='coerce')

            return df
        except Exception as e:
            print(f"Error in get_data: {e}")
            return pd.DataFrame()





    def close(self):
        if self.conn:
            self.conn.close()
    def __del__(self):
        self.close()
