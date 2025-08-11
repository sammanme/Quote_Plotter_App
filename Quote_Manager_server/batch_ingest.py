import logging
from pathlib import Path
from quote_service import QuoteService
from quote_db import QuoteDatabase

logging.basicConfig(level=logging.INFO)

def main():
    folder_path = Path("archives/")  # or whatever your folder is, ensure it exists
    if not folder_path.exists() or not folder_path.is_dir():
        logging.error(f"Folder {folder_path} does not exist or is not a directory: {folder_path}.")
        return
    db = QuoteDatabase("quotes.db")
    service = QuoteService(db)

    service.ingest_archives_from_folder(folder_path)

if __name__ == "__main__":
    main()
