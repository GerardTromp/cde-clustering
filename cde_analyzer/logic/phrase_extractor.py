import re
import logging
from collections import defaultdict
from typing import Any, Dict, List, Set, Optional, DefaultDict, Tuple, Union, TypeAlias
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords
from nltk.tag import pos_tag
from nltk import word_tokenize, pos_tag
from nltk.corpus import wordnet
import nltk
from utils.helpers import safe_nested_append
from utils.logger import log_if_verbose

# Download resources quietly
nltk.download("punkt", quiet=True)
nltk.download("punkt_tab", quiet=True)
nltk.download("wordnet", quiet=True)
nltk.download("stopwords", quiet=True)
nltk.download("averaged_perceptron_tagger_eng", quiet=True)

# Global resources
STOPWORDS = set(stopwords.words("english"))
lemmatizer = WordNetLemmatizer()

# Type alias for clarity
PhraseMap = DefaultDict[str, DefaultDict[str, Set[str]]]
NestedDict: TypeAlias = Dict[str, Union[List, "NestedDict"]]

logger = logging.getLogger("cde_analyzer.phrase")


def get_wordnet_pos(tag: str) -> str:
    """Map POS tag to format WordNetLemmatizer accepts."""
    if tag.startswith("J"):
        return wordnet.ADJ
    elif tag.startswith("V"):
        return wordnet.VERB
    elif tag.startswith("N"):
        return wordnet.NOUN
    elif tag.startswith("R"):
        return wordnet.ADV
    return wordnet.NOUN  # default to noun


def extract_phrases(
    text: str, min_words: int, remove_stopwords: bool, lemmatize: bool, verbosity: int
) -> List[str]:
    log_if_verbose(f"[TOKENIZE] raw: {repr(text)}", 3)
    tokens = word_tokenize(text.lower())
    log_if_verbose(f"[TOKENIZE] tokens: {tokens}", 3)

    # Filter out non-alphanumeric before POS tagging
    tokens = [w for w in tokens if w.isalnum()]

    if lemmatize:
        pos_tags = pos_tag(tokens)
        log_if_verbose(f"[POS] tags: {pos_tags}", 3)

        words = [
            lemmatizer.lemmatize(word, get_wordnet_pos(pos)) for word, pos in pos_tags
        ]
    else:
        words = tokens

    log_if_verbose(f"[CLEANED] lemmas: {words}", 3)

    if remove_stopwords:
        words = [w for w in words if w not in STOPWORDS]
        log_if_verbose(f"[CLEANED] without stopwords: {words}", 3)

    phrases = []
    for size in range(min_words, len(words) + 1):
        for i in range(len(words) - size + 1):
            phrases.append(" ".join(words[i : i + size]))

    log_if_verbose(f"[PHRASES] total: {len(phrases)}", 2)
    return phrases


def collect_phrases_from_item(
    item: Any,
    field_names: Set[str],
    tiny_id: str,
    current_path: str = "",
    results: Optional[PhraseMap] = None,
    verbatim_results: Optional[PhraseMap] = None,
    min_words: int = 2,
    remove_stopwords: bool = True,
    verbosity: int = 0,
    lemmatize: bool = True,
    verbatim: bool = False,
) -> Tuple[PhraseMap, PhraseMap]:
    """Recursively walk the object and collect phrases from fields matching field_names."""
    if results is None:
        results = defaultdict(lambda: defaultdict(set))
    if verbatim_results is None:
        verbatim_results = defaultdict(lambda: defaultdict(set))

    #    print("descended into collect phrases from item")
    if isinstance(item, dict):
        iterator = item.items()
    elif hasattr(item, "__dict__"):
        iterator = vars(item).items()
    elif isinstance(item, list):
        for elem in item:
            collect_phrases_from_item(
                elem,
                field_names,
                tiny_id,
                current_path + ".*" if current_path else "*",
                results,
                verbatim_results,
                min_words,
                remove_stopwords,
                verbosity,
                verbatim,
            )
        return results, verbatim_results
    else:
        return results, verbatim_results

    for key, value in iterator:
        new_path = f"{current_path}.{key}" if current_path else key

        if key in field_names and isinstance(value, str):
            log_message = f"[MATCH] {new_path}"
            log_if_verbose(log_message, 2)
            phrases = extract_phrases(
                value, min_words, remove_stopwords, lemmatize, verbosity
            )
            # No need to use log_if_verbose here. Want to ONLY execute if logger desired
            if verbosity >= 3:
                log_if_verbose(f"         value: {repr(value)}")
                log_if_verbose(f"[PHRASES] Extracted from {new_path}:")
                for phrase in phrases:
                    log_if_verbose(f"  - {phrase}")

            #  rename value to ensure readability of code below
            # verbatim_phrase = value

            for phrase in phrases:
                results[new_path][phrase].add(tiny_id)
                verbatim_results[new_path][phrase].add(value)

        elif isinstance(value, list):
            for elem in value:
                collect_phrases_from_item(
                    elem,
                    field_names,
                    tiny_id,
                    new_path + ".*",
                    results,
                    verbatim_results,
                    min_words,
                    remove_stopwords,
                    verbosity,
                )

        elif hasattr(value, "__dict__") or isinstance(value, dict):
            collect_phrases_from_item(
                value,
                field_names,
                tiny_id,
                new_path,
                results,
                verbatim_results,
                min_words,
                remove_stopwords,
                verbosity,
            )

    return results, verbatim_results


def collect_all_phrase_occurrences(
    items: List[Any],
    field_names: List[str],
    verbosity: int = 0,
    min_words: int = 2,
    remove_stopwords: bool = True,
    min_ids: int = 2,
    prune_subphrases: bool = True,
    lemmatize: bool = True,
    verbatim: bool = False,
) -> Dict[str, Dict[str, List[str]]]:
    """
    Process all items and return a dict:
      field_path -> phrase -> list of tinyIDs
    Only includes phrases appearing in at least min_ids unique tinyIDs.
    """
    final_result: PhraseMap = defaultdict(lambda: defaultdict(set))
    verbatim_map: PhraseMap = defaultdict(lambda: defaultdict(set))
    field_set = set(field_names)

    for item in items:
        tiny_id = getattr(item, "tinyId", None)
        if not tiny_id:
            continue
        collect_phrases_from_item(
            item=item,
            field_names=field_set,
            tiny_id=tiny_id,
            results=final_result,
            verbatim_results=verbatim_map,
            min_words=min_words,
            remove_stopwords=remove_stopwords,
            verbosity=verbosity,
            lemmatize=lemmatize,
        )

    # Post-process to convert sets to sorted lists and apply filtering
    if verbatim:
        output: Dict[str, Dict[str, Dict[str, List[str]]]] = {}  # type: ignore
    else:
        output: Dict[str, Dict[str, List[str]]] = {}
    for path, phrase_map in final_result.items():
        if prune_subphrases:
            phrase_map = prune_subphrases_by_tinyid(phrase_map)

        filtered = {
            phrase: sorted(list(ids))
            for phrase, ids in phrase_map.items()
            if len(ids) >= min_ids
        }

        if filtered:
            output[path] = filtered
            pruned = {
                phrase: sorted(ids)
                for phrase, ids in phrase_map.items()
                if len(ids) >= min_ids
            }
        if pruned:
            output[path] = pruned

        if verbatim:
            #                for path, lemma_dict in phrase_map.items():
            for lemma_phrase, tinyids in phrase_map.items():
                log_message = f"OUTPUT: lemma phrase {lemma_phrase}"
                log_if_verbose(log_message, 3)
                for verbatim_phrase in (
                    verbatim_map.get(path, {}).get(lemma_phrase, []) or []
                ):
                    log_message = f"OUTPUT: verbatim phrase {verbatim_phrase}"
                    log_if_verbose(log_message, 3)
                    for tid in tinyids:
                        if len(set(tinyids)) < min_ids:
                            continue
                        safe_nested_append(
                            output,
                            path,
                            lemma_phrase,
                            verbatim_phrase,
                            value=tid,
                        )

    return output


def prune_subphrases_by_tinyid(phrase_map: Dict[str, Set[str]]) -> Dict[str, Set[str]]:
    """
    Collapse shorter subphrases per tinyID if the same ID also matches a longer phrase.
    Retains only the longest (non-sub)phrases for each ID.
    """
    # Reverse index: tinyID -> all phrases it appears in
    tinyid_to_phrases = defaultdict(list)
    for phrase, ids in phrase_map.items():
        for tid in ids:
            tinyid_to_phrases[tid].append(phrase)

    # For each ID, keep only longest phrases (by word count) that aren't substrings of others
    longest_phrases_per_tid = defaultdict(set)
    for tid, phrases in tinyid_to_phrases.items():
        # Sort by word length descending, then lexically
        sorted_phrases = sorted(phrases, key=lambda p: (-len(p.split()), p))
        kept = set()
        for p in sorted_phrases:
            if not any(p in longer and p != longer for longer in kept):
                kept.add(p)
        for p in kept:
            longest_phrases_per_tid[p].add(tid)

    # Rebuild collapsed phrase map
    collapsed_map: Dict[str, Set[str]] = defaultdict(set)
    for phrase, ids in longest_phrases_per_tid.items():
        collapsed_map[phrase].update(ids)

    return collapsed_map
