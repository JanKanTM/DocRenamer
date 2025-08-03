import os
import time
import logging
from datetime import datetime
from PyPDF2 import PdfReader
from watchdog.events import FileSystemEventHandler
from config.settings import SCAN_FOLDER

class DocRenameHandler(FileSystemEventHandler):
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)

    def on_created(self, event):
        if not event.is_directory and event.src_path.lower().endswith('.pdf'):
            self.logger.info(f"new pdf found: {event.src_path}")
            self.process_pdf(event.src_path)
    
    def process_pdf(self, file_path):
        max_retries: int = 3
        is_ready: bool = False

        for attempt in range(max_retries):
            try:
                with open(file_path, 'rb') as f:
                    self.logger.info(f"File '{file_path}' opened successfully on attempt {attempt + 1}.")
                    is_ready = True
                    break
            except IOError:
                self.logger.debug(f"File '{file_path}' is locked. Retrying in 1 second... (Attempt {attempt + 1}/{max_retries})")
                time.sleep(1)
            except Exception as e:
                self.logger.error(f"An unexpected error occurred while trying to open {file_path}: {e}")
                self.logger.error(f"Could not process file '{file_path}' after {max_retries} attempts. It may be in use by another process.")
                break
        
        if is_ready:
            try:
                with open(file_path, 'rb') as f:
                    reader = PdfReader(f)
                    title = reader.metadata.get('/Title')
                
                if not title:
                    original_filename: str = os.path.basename(file_path)
                    title = original_filename.rsplit('.', 1)[0]
                    self.logger.warning(f"Found no title in metadate. Using filename: {title}")

                title = "".join(c for c in title if c.isalnum() or c in (' ', '_', '-')).strip()

                current_date: datetime = datetime.now().strftime('%Y-%m-%d')

                new_filename: str = f"{current_date}_{title}.pdf"
                new_file_path = os.path.join(SCAN_FOLDER, new_filename)

                os.rename(file_path, new_file_path)
                self.logger.info(f"File was successfully renamed in: {new_file_path}")
            except Exception as e:
                self.logger.error(f"An unexpected error occurred while trying to rename the file {file_path}: {e}")        


        
