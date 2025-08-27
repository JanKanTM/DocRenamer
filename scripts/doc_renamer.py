import os
import time
import logging
import spacy
import re
from datetime import datetime
from PyPDF2 import PdfReader
from watchdog.events import FileSystemEventHandler
from config.settings import SCAN_FOLDER

### NER-Models (German + English) ###
nlp_de = spacy.load("de_core_news_md")
nlp_en = spacy.load("en_core_web_md")

### Regex for company names ###
COMPANY_REGEX = re.compile(
    r"\b([A-ZÄÖÜ][A-Za-zÄÖÜäöüß&\s,\.-]+?(?:GmbH|AG|KG|UG|OHG|SE|Inc\.|Ltd\.|Corp\.|LLC|PLC))\b"
)

class DocRenameHandler(FileSystemEventHandler):
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)

    def on_created(self, event):
        if not event.is_directory and event.src_path.lower().endswith('.pdf'):
            self.logger.info(f"new pdf found: {event.src_path}")
            self.process_pdf(event.src_path)
    
    def extract_company_names(self, text: str):
        orgs = set()

        # german
        doc_de = nlp_de(text)
        orgs.update([ent.text.strip() for ent in doc_de.ents if ent.label_ == "ORG"])

        # english
        doc_en = nlp_en(text)
        orgs.update([ent.text.strip() for ent in doc_en.ents if ent.label_ == "ORG"])

        # regex
        filtered_orgs = [o for o in orgs if COMPANY_REGEX.search(o)]

        return filtered_orgs

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
                reader = PdfReader(file_path)
                title = reader.metadata.get('/Title')

                if not title:
                    original_filename: str = os.path.basename(file_path)
                    title = original_filename.rsplit('.', 1)[0]
                    self.logger.warning(f"Found no title in metadate. Using filename: {title}")

                text = ""
                for page in reader.pages:
                    text += page.extract_text() or ""
        
                companies = self.extract_company_names(text)
                if companies:
                    company_name = companies[0]
                    self.logger.info(f"Company detected with NER: {company_name}")
                else:
                    company_name = "UnknownCompany"
                    self.logger.warning(f"No company detected!")

                title = "".join(c for c in title if c.isalnum() or c in (' ', '_', '-')).strip()
                company_name = "".join(c for c in company_name if c.isalnum() or c in (' ', '_', '-')).strip()
                company_name = company_name.replace(" ", "_")

                current_date: datetime = datetime.now().strftime('%Y-%m-%d')

                new_filename: str = f"{current_date}_{title}_{company_name}.pdf"
                new_file_path = os.path.join(SCAN_FOLDER, new_filename)

                os.rename(file_path, new_file_path)
                self.logger.info(f"File was successfully renamed in: {new_file_path}")
            except Exception as e:
                self.logger.error(f"An unexpected error occurred while trying to rename the file {file_path}: {e}")        
