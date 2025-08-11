import os
from decimal import Decimal
import pandas as pd
import logging

from sqlalchemy import Float
from ingest import ingest_zip_archive
from quote_db import QuoteDatabase
from quote_contracts import (
    FetchQuoteRequest,
    QuoteResponse,
    FetchQuoteResponse,
    FetchBrokersResponse,
    ListSymbolsRequest,
    ListSymbolsResponse,
    ListDatesRequest,
    ListDatesResponse,
    ListSessionRequest,
    ListSessionResponse,
    IngestRequest, 
    IngestResponse,
    FetchData,
    FetchDataResponse,
    BrokersSymbolsResponse
)
from pathlib import Path

logger = logging.getLogger(__name__)

class QuoteService:
    def __init__(self, db: QuoteDatabase):
        self.db = db

    

    def ingest_archives_from_folder(self, folder: Path):
        for zip_file in folder.glob("*.zip"):
            if not zip_file.exists():
                logger.warning(f"ZIP archive not found: {zip_file}")
                continue
            logger.info(f"Ingesting archive: {zip_file}")
            result = self.ingest_archive(IngestRequest(zip_path=str(zip_file)))
            if result.status == "success":
                logger.info(f"Archive ingested successfully: {zip_file}")
            else:
                logger.error(f"Ingestion error for {zip_file}: {result.message}")

    def ingest_archive(self, request: IngestRequest) -> IngestResponse:
        """Ingest a ZIP archive into the database."""
        zip_path = Path(request.zip_path)

        if not zip_path.exists():
            logger.warning(f"ZIP archive not found: {zip_path}")
            return IngestResponse(status="failed", message="ZIP archive not found.")

        try:
            ingest_zip_archive(zip_path, db=self.db)
            return IngestResponse(
                status="success",
                message="Archive ingested successfully."
            )
        except Exception as e:
            logger.error(f"Ingestion error: {e}", exc_info=True)
            return IngestResponse(
                status="failed",
                message=f"Ingestion error: {e}"
            )



    def get_all_brokers(self) -> FetchBrokersResponse:
        """Return all brokers in the database."""
        brokers = self.db.get_all_brokers()
        return FetchBrokersResponse(brokers=brokers)
    
    def get_brokers_and_symbols(self) -> BrokersSymbolsResponse:
        """Return all brokers and their symbols in mapping form."""
        mapping = self.db.get_brokers_and_symbols()
        return BrokersSymbolsResponse(brokers=mapping)

    def get_symbols(self, request: ListSymbolsRequest) -> ListSymbolsResponse:
        """Return all symbols for a broker."""
        symbols = self.db.get_symbols_by_broker(request.broker)
        return ListSymbolsResponse(symbols=symbols)

    def get_dates(self, request: ListDatesRequest) -> ListDatesResponse:
        """Return all dates for a broker and symbol."""
        dates = self.db.get_dates_by_broker_symbol(request.broker, request.symbol)
        return ListDatesResponse(dates=dates)

    def get_sessions(self, request: ListSessionRequest) -> ListSessionResponse:
        """Return all sessions for a broker, symbol, and date."""
        sessions = self.db.get_sessions_by_date(
            request.broker, request.symbol, request.date
        )
        return ListSessionResponse(sessions=sessions)

    def get_quotes(self, request: FetchQuoteRequest) -> FetchQuoteResponse:
        """Return all quotes for a broker, symbol, and time range."""
        quotes = self.db.fetch_quotes(    
            broker=request.broker,
            symbol=request.symbol,
            start_time=request.start_time,
            end_time=request.end_time
        )
        return FetchQuoteResponse(
            quotes=[
                QuoteResponse(
                    session_id=row[0],
                    timestamp=row[1],
                    bid=row[2],
                    ask=row[3]
                )
                for row in quotes
            ]
        )
    def get_data(self, broker_a, symbol_a, broker_b, symbol_b, limit=1000, time_range_hours='all'):
        df = self.db.get_data(broker_a, symbol_a, broker_b, symbol_b, limit, time_range_hours)
        if df.empty:
            print(f"No data after initial fetch: broker_a={broker_a}, symbol_a={symbol_a}, "
                  f"broker_b={broker_b}, symbol_b={symbol_b}")
            return []

        # Separate data for each broker/symbol pair
        df_a = df[(df['broker'] == broker_a) & (df['symbol'] == symbol_a)].copy()
        df_b = df[(df['broker'] == broker_b) & (df['symbol'] == symbol_b)].copy()

        result = []

        # Process df_a (Tradeview/XAUUSD)
        if not df_a.empty:
            df_a = df_a.dropna(subset=['timestamp'])  # Only drop invalid timestamps
            if df_a.empty:
                print(f"No valid data for {broker_a}/{symbol_a} after dropping invalid timestamps")
            else:
                result_a = [
                    FetchData(
                        session_id=row['session_id'],
                        bid_price=(row['bid']) if pd.notna(row['bid']) else None,
                        ask_price=(row['ask']) if pd.notna(row['ask']) else None,
                        timestamp=str(row['timestamp']),
                        broker=broker_a,
                        symbol=symbol_a
                    )
                    for _, row in df_a.iterrows()
                ]
                result.extend(result_a)

        # Process df_b (Zeal Capital/XAUUSDe)
        if not df_b.empty:
            df_b = df_b.dropna(subset=['timestamp'])  # Only drop invalid timestamps
            if df_b.empty:
                print(f"No valid data for {broker_b}/{symbol_b} after dropping invalid timestamps")
            else:
                result_b = [
                    FetchData(
                        session_id=row['session_id'],
                        bid_price=(row['bid']) if pd.notna(row['bid']) else None,
                        ask_price=(row['ask']) if pd.notna(row['ask']) else None,
                        timestamp=str(row['timestamp']),
                        broker=broker_b,
                        symbol=symbol_b
                    )
                    for _, row in df_b.iterrows()
                ]
                result.extend(result_b)

        if not result:
            print(f"No valid data after processing: broker_a={broker_a}, symbol_a={symbol_a}, "
                  f"broker_b={broker_b}, symbol_b={symbol_b}")
            return []

        # Limit the total number of records
        return result[:limit]
        
    

