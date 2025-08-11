import os
import csv
import zipfile
import logging
from quote_db import QuoteDatabase 

logger = logging.getLogger(__name__)

def extract_metadata_from_filename(filename):
    parts = filename.replace(".csv", "").split("_")
    broker, symbol, *_session_parts = parts
    session_id = "_".join(_session_parts)
    return broker, symbol, session_id

def ingest_zip_archive(zip_path: str, db: QuoteDatabase):
    archive_name = os.path.basename(zip_path).replace(".zip", "")

    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        for file_info in zip_ref.infolist():
            if file_info.filename.endswith(".csv"):
                logger.info(f"Processing CSV: {file_info.filename}")
                with zip_ref.open(file_info.filename) as file: 
                    broker, symbol, session_id = extract_metadata_from_filename(file_info.filename)
                    reader = csv.DictReader((line.decode("utf-8") for line in file))
                    quotes = []
                    timestamps = []

                    for row in reader:
                        try:
                            timestamp = int(row["Ts"])
                            bid = float(row["Bid"])
                            ask = float(row["Ask"])
                            quotes.append((timestamp, bid, ask))
                            timestamps.append(timestamp)
                        except KeyError as e:
                            logger.warning(f"Missing column in row: {row} -- {e}")
                        except Exception as e:
                            logger.error(f"Error processing row: {row} -- {e}")

                    if quotes:
                        logger.info(f"Parsed {len(quotes)} quotes for session {session_id}")

                        start_time = min(timestamps)
                        end_time = max(timestamps)
                        if db.session_exists(session_id):
                            logger.info(f"Session {session_id} already exists, skipping insertion.")
                        else:
                            db.insert_session((session_id, broker, symbol, archive_name, start_time, end_time))
                        db.insert_quotes_bulk(session_id, quotes)
                    else:
                        logger.warning(f"No quotes parsed from file: {file_info.filename}")
    db.conn.commit()
    logger.info(f"Ingestion completed for archive: {archive_name}")
