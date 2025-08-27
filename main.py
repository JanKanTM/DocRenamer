import os
import time
import logging
from watchdog.observers import Observer
from scripts.doc_renamer import DocRenameHandler
from config.settings import SCAN_FOLDER, LOG_FILE_PATH

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.FileHandler(LOG_FILE_PATH),
            logging.StreamHandler()
        ]
    )

if __name__ == "__main__":
    setup_logging()

    if not os.path.exists(SCAN_FOLDER):
        logging.error(f"The configurated folder does not exist: {SCAN_FOLDER}")
    else:
        event_handler = DocRenameHandler()
        observer = Observer()
        observer.schedule(event_handler, SCAN_FOLDER, recursive=False)
        observer.start()
        logging.info(f"Starting the observation of: '{SCAN_FOLDER}'")

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logging.info("Program was stopped by the user!")
            observer.stop()
        observer.join()        