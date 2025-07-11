# ------------------------------
# File: utils/html.py
# ------------------------------
import unicodedata
import warnings
import logging
import json
from bs4 import BeautifulSoup, MarkupResemblesLocatorWarning  # type: ignore
from pydantic import BaseModel
from typing import Any, Type, List, Optional, Dict, Union
from utils.logger import log_if_verbose
from utils.analyzer_state import get_verbosity

logger = logging.getLogger("cde_analyzer.strip")
verbosity = get_verbosity()


def normalize_string(text: str) -> str:
    return unicodedata.normalize("NFC", text).strip().lower()


def strip_html(text: str) -> str:
    if text is None:
        return None
    #    print(f"stripping html: {text}")
    warnings.filterwarnings("ignore", category=MarkupResemblesLocatorWarning)
    soup = BeautifulSoup(text, "html.parser")
    return soup.get_text()


def clean_text_values(obj: Any, set_keys, tables: bool, colnames: bool) -> Any:
    if isinstance(obj, str):
        if not tables:
            log_message = f"processing cell with plain html: {obj}"
            log_if_verbose(log_message, 3)
            return strip_html(obj)
        else:
            # value = process_html_blob(obj, colnames)
            log_message = f"processing cell with html table: {obj}"
            log_if_verbose(log_message, 3)
            return process_html_blob(obj, colnames)
    elif isinstance(obj, BaseModel):
        cleaned = {
            k: clean_text_values(v, set_keys, tables, colnames)
            for k, v in obj.model_dump(
                exclude_unset=True if set_keys else False,
                exclude_none=True if set_keys else False,
            ).items()
        }
        return obj.__class__(**cleaned)
    elif isinstance(obj, list):
        return [clean_text_values(item, set_keys, tables, colnames) for item in obj]
    elif isinstance(obj, dict):
        return {
            k: clean_text_values(v, set_keys, tables, colnames) for k, v in obj.items()
        }
    else:
        return obj


def process_html_blob(html_string, header_col: bool):
    """
    Analyzes an HTML string to determine if it contains a table.
    If it does, it converts the table to JSON. Otherwise, it extracts plain text.

    Args:
        html_string: The string containing HTML markup.

    Returns:
        A JSON string representing the table data (if a table is found)
        or a simple string containing the extracted text.
    """

    warnings.filterwarnings("ignore", category=MarkupResemblesLocatorWarning)
    soup = BeautifulSoup(html_string, "lxml")  # Use lxml parser

    # Check if the HTML contains any table tags
    table_tags = soup.find_all("table")

    if table_tags:
        # If tables are found, process the first table found
        table = table_tags[0]
        table_data = []

        rows = table.find_all("tr")

        # Add logical, e.g., header_col T/F
        #   if header_col( == T):
        #      process as below
        if header_col:
            if len(rows) <= 1:
                raise ValueError(
                    "Detected a table with only a header row (one-line table). "
                    "You should not use the --colnames option."
                )
            # Assuming the first row is the header, if applicable
            header_row = table.find("tr")
            headers = [
                cell.get_text(strip=True) for cell in header_row.find_all(["th", "td"])
            ]

            for row in table.find_all("tr")[1:]:  # Start from the second row
                row_data = [
                    cell.get_text(strip=True) for cell in row.find_all(["td", "th"])
                ]
                # Create a dictionary for each row using headers as keys
                row_dict = dict(zip(headers, row_data))
                table_data.append(row_dict)

        #   else: # (header_col is false)
        #      add arbitrary rowname dictionary keys.
        else:
            row_cnt = 0
            log_message = f"Processing headerless table"
            log_if_verbose(log_message, 3)
            for row in table.find_all("tr")[0:]:  # Start from the first row
                row_cnt += 1
                row_data = [
                    cell.get_text(strip=True) for cell in row.find_all(["td", "th"])
                ]
                log_message = (
                    f"Processing headerless table. row: {row_cnt}, data: {row_data}"
                )
                log_if_verbose(log_message, 3)
                header = f"row_{row_cnt}"
                row_dict = dict([(header, row_data)])
                table_data.append(row_dict)

        # create a new dictionary structure to incorporate instead of a list with text
        # rendered by json.dump
        new_dict = {"table": table_data[0]}
        return new_dict

    else:
        # If no tables are found, extract plain text
        return soup.get_text(strip=True)  # Extract text and strip whitespace
