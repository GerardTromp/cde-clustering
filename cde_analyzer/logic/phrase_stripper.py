import json
import csv
import re
from typing import Any, List, Tuple, Type
from pydantic import BaseModel
from CDE_Schema import CDEItem, CDEForm
import logging
from utils.logger import log_if_verbose
from utils.analyzer_state import get_verbosity

logger = logging.getLogger(__name__)
verbosity = get_verbosity()


def load_phrase_map(filepath: str) -> List[Tuple[str, str]]:
    if filepath.endswith(".json"):
        with open(filepath) as f:
            data = json.load(f)
        return [(item["path"], item["phrase"]) for item in data]
    else:
        with open(filepath, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(
                f, delimiter="\t" if filepath.endswith(".tsv") else ","
            )
            return [(row["path"], row["phrase"]) for row in reader]


def delete_phrase_at_path(obj: Any, path: str, phrase: str):
    """Delete a phrase from a string at the specified dotted path. Supports wildcards like field[*]."""
    logger.debug(f"Applying phrase '{phrase}' to path '{path}'")
    parts = re.split(r"\.(?![^\[]*\])", path)
    _navigate_and_strip(obj, parts, phrase)


def _navigate_and_strip(current: Any, parts: List[str], phrase: str):
    if not parts:
        return

    part = parts[0]
    match = re.match(r"(\w+)(?:\[(\*|\d+)\])?", part)
    if not match:
        return
    key, index = match.group(1), match.group(2)

    if isinstance(current, dict):
        next_level = current.get(key)
        if next_level is None:
            return

        if index is None:
            if len(parts) == 1:
                _strip_in_place(current, key, phrase)
            else:
                _navigate_and_strip(next_level, parts[1:], phrase)
        elif index == "*":
            if isinstance(next_level, list):
                for item in next_level:
                    _navigate_and_strip(item, parts[1:], phrase)
        else:
            idx = int(index)
            if isinstance(next_level, list) and 0 <= idx < len(next_level):
                if len(parts) == 1:
                    _strip_in_place(next_level, idx, phrase)
                else:
                    _navigate_and_strip(next_level[idx], parts[1:], phrase)


def traverse_and_replace_phrase(
    obj: Any, path: str, phrase: str, replace_with: str = ""
):
    """
    Traverse the object using a dot-separated path with support for wildcards (*)
    and replace the exact phrase (verbatim) in any matching string fields.

    Parameters:
        obj: The nested dict or list to modify in-place.
        path: A dot-separated path like "definitions.*.definition"
        phrase: The exact phrase to remove (must match exactly).
        replace_with: String to replace the phrase with (default: empty string).
    """
    parts = path.split(".")
    _recurse_and_replace(obj, parts, phrase, replace_with)


def _recurse_and_replace(
    current: Any, parts: List[str], phrase: str, replace_with: str
):
    if not parts:
        return

    key = parts[0]
    rest = parts[1:]

    if key == "*":
        if isinstance(current, list):
            for i, item in enumerate(current):
                _recurse_and_replace(item, rest, phrase, replace_with)
        else:
            logger.debug(f"Wildcard expected list but got {type(current).__name__}")
    elif isinstance(current, dict):
        if key in current:
            if not rest:
                _replace_if_match(current, key, phrase, replace_with)
            else:
                _recurse_and_replace(current[key], rest, phrase, replace_with)
        else:
            logger.debug(f"Key '{key}' not found in dict")
    elif isinstance(current, list):
        try:
            index = int(key)
            if index < len(current):
                if not rest:
                    _replace_if_match(current, index, phrase, replace_with)
                else:
                    _recurse_and_replace(current[index], rest, phrase, replace_with)
        except ValueError:
            logger.debug(f"Invalid index '{key}' for list")
    else:
        logger.debug(
            f"Cannot traverse non-collection type at {key}: {type(current).__name__}"
        )


def _replace_if_match(
    container: Any, key_or_index: Any, phrase: str, replace_with: str
):
    try:
        value = container[key_or_index]
        if isinstance(value, str):
            if phrase in value:
                logger.debug(f"Replacing phrase in path: {key_or_index}")
                container[key_or_index] = value.replace(phrase, replace_with)
            else:
                logger.debug(f"Phrase not found at {key_or_index}")
        else:
            logger.debug(f"Value at {key_or_index} is not a string: {value}")
    except Exception as e:
        logger.warning(f"Could not replace phrase at {key_or_index}: {e}")


def _strip_in_place(container: Any, key_or_index: Any, phrase: str):
    try:
        value = container[key_or_index]
        if not isinstance(value, str):
            logger.debug(f"Not a string at {key_or_index}: {value}")
            return
        if phrase not in value:
            logger.debug(f"Phrase '{phrase}' not found in: {value}")
            return

        new_value = value.replace(phrase, "")
        logger.info(f"Replacing phrase '{phrase}' in: {value}")
        container[key_or_index] = new_value

        # if new_value.strip() == "":
        #     logger.warning(f"Value became empty string after stripping: '{phrase}' at {key_or_index}")
        # value = container[key_or_index]
        # if isinstance(value, str) and phrase in value:
        #     new_value = value.replace(phrase, "")
        #     container[key_or_index] = new_value
        #     logger.info(f"Stripped phrase '{phrase}' at path -> {...}")
        #     if new_value.strip() == "":
        #         logger.warning(
        #             f"Empty string after stripping phrase '{phrase}' at path -> {...}"a
    except (KeyError, IndexError, TypeError):
        logger.error(f"Error stripping without index, key or type ")
        pass
    except Exception as e:
        logger.error(f"Error stripping at {key_or_index}: {e}")


def strip_phrases(
    model_list: List[BaseModel], phrase_map: List[Tuple[str, str]]
) -> List[BaseModel]:
    cleaned_models = []
    i = 1
    for model in model_list:
        data = model.model_dump(mode="python", exclude_none=False)
        i += 1
        log_message = f"[strip_phrases] Iterating over models. Model {i}"
        log_if_verbose(log_message, 3)
        for path, phrase in phrase_map:
            log_message = f"changing path: {path} phrase {phrase}"
            log_if_verbose(log_message, 3)
            traverse_and_replace_phrase(data, path, phrase)
            # delete_phrase_at_path(data, path, phrase)
        cleaned = model.__class__.model_validate(data)
        cleaned_models.append(cleaned)
    return cleaned_models
