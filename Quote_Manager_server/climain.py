import logging
from datetime import datetime
from quote_service import QuoteService
from quote_db import QuoteDatabase
from quote_contracts import (
    FetchQuoteRequest,
    ListSymbolsRequest,
    ListDatesRequest,
    ListSessionRequest,
    IngestRequest,
)
import argparse
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def to_unix(date_str):
    return int(datetime.strptime(date_str, "%Y-%m-%d").timestamp())

def parse_args():
    parser = argparse.ArgumentParser(description="Quote Manager Workflow")
    parser.add_argument("--broker", required=False, help="Broker name")
    parser.add_argument("--symbol", required=False, help="Symbol")
    parser.add_argument("--date", required=False, help="Date (YYYY-MM-DD)")
    parser.add_argument("--archive", required=False, help="Path to archive zip")
    return parser.parse_args()

def main():
    args = parse_args()
    db = QuoteDatabase("quotes.db")
    service = QuoteService(db)

    # 1. Ingest archive
    # if args.batch_folder:
    #     service.ingest_archives_from_folder(Path(args.batch_folder))
    # else:
    #     result = service.ingest_archive(IngestRequest(zip_path=args.archive))
    #     logging.info(f"{result.status} - {result.message}")

    # 2. List all brokers
    logging.info("All Brokers:")
    brokers_response = service.get_all_brokers()
    logging.info(f"Brokers: {brokers_response.brokers}")

    # 3. List symbols for broker
    symbols_response = service.get_symbols(ListSymbolsRequest(broker=args.broker))
    logging.info(f"Symbols for broker '{args.broker}': {symbols_response.symbols}")

    # 4. List dates for symbol
    dates_response = service.get_dates(ListDatesRequest(broker=args.broker, symbol=args.symbol))
    logging.info(f"Dates for {args.broker} - {args.symbol}: {dates_response.dates}")

    # 5. List sessions for date
    sessions_response = service.get_sessions(ListSessionRequest(broker=args.broker, symbol=args.symbol, date=args.date))
    logging.info(f"Sessions for {args.broker} - {args.symbol} on {args.date}: {sessions_response.sessions}")

    # 6. Fetch quotes
    start = to_unix(args.date) * 1000
    end = start + 86400 * 1000
    quotes_response = service.get_quotes(FetchQuoteRequest(
        broker=args.broker,
        symbol=args.symbol,
        start_time=start,
        end_time=end
    ))
    logging.info(f"Quotes fetched: {quotes_response.quotes}")


