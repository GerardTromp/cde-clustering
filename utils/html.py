# ------------------------------
# File: utils/html.py
# ------------------------------
import unicodedata
import warnings
from bs4 import BeautifulSoup, MarkupResemblesLocatorWarning  # type: ignore
from pydantic import BaseModel
from typing import Any, Type, List, Optional, Dict, Union


def normalize_string(text: str) -> str:
    return unicodedata.normalize("NFC", text).strip().lower()


def strip_html(text: str) -> str:
    if text is None:
        return None
    #    print(f"stripping html: {text}")
    warnings.filterwarnings("ignore", category=MarkupResemblesLocatorWarning)
    soup = BeautifulSoup(text, "html.parser")
    return soup.get_text()


def clean_text_values(obj: Any, set_keys) -> Any:
    if isinstance(obj, str):
        return strip_html(obj)
    elif isinstance(obj, BaseModel):
        cleaned = {
            k: clean_text_values(v, set_keys)
            for k, v in obj.model_dump(
                exclude_unset=True if set_keys else False,
                exclude_none=True if set_keys else False,
            ).items()
        }
        return obj.__class__(**cleaned)
    elif isinstance(obj, list):
        return [clean_text_values(item, set_keys) for item in obj]
    elif isinstance(obj, dict):
        return {k: clean_text_values(v, set_keys) for k, v in obj.items()}
    else:
        return obj
