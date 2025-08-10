import re
import logging
from collections import defaultdict
from typing import Any, Dict, List, Set, Optional, DefaultDict, Tuple, Union, TypeAlias
from utils.helpers import safe_nested_append
from utils.logger import log_if_verbose
from utils.phrase_pruning import (
    prune_subphrases_threshold,
    prune_subphrases_by_tinyid,
    prune_subphrases_global,
)
from utils.phrase_extraction import collect_phrases_from_item, PhraseMap, NestedDict


# logger = logging.getLogger("cde_analyzer.phrase")
logger = logging.getLogger(__name__)


def collect_all_phrase_occurrences(
    items: List[Any],
    field_names: List[str],
    verbosity: int = 0,
    min_words: int = 2,
    remove_stopwords: bool = True,
    min_ids: int = 2,
    prune: str = "none",
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
        if prune == "tinyid":
            phrase_map = prune_subphrases_by_tinyid(phrase_map)
        if prune == "global":
            phrase_map = prune_subphrases_global(phrase_map)

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


def prune_subphrases(
    phrase_map: Dict[str, Set[str]],
    strategy: str = "none",
    min_ids: int = 2,
    min_words: int = 1,
) -> Dict[str, Set[str]]:
    if strategy == "none":
        return phrase_map
    if strategy == "tinyid":
        return prune_subphrases_by_tinyid(phrase_map)
    elif strategy == "global":
        return prune_subphrases_global(phrase_map)
    elif strategy == "threshold":
        return prune_subphrases_threshold(
            phrase_map, min_ids=min_ids, min_words=min_words
        )
    else:
        raise ValueError("Invalid prune strategy: choose {strategy}")
