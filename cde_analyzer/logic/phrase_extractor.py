import re
from collections import defaultdict
from typing import Any, Dict, List, Set, Optional, DefaultDict, Tuple, Union, TypeAlias
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords
import nltk
from utils.helpers import safe_nested_append

# Download resources quietly
nltk.download("punkt", quiet=True)
nltk.download("punkt_tab", quiet=True)
nltk.download("wordnet", quiet=True)
nltk.download("stopwords", quiet=True)

# Global resources
STOPWORDS = set(stopwords.words("english"))
lemmatizer = WordNetLemmatizer()

# Type alias for clarity
PhraseMap = DefaultDict[str, DefaultDict[str, Set[str]]]
NestedDict: TypeAlias = Dict[str, Union[List, "NestedDict"]]


def extract_phrases(
    text: str, min_words: int, remove_stopwords: bool, lemmatize: bool, verbosity: int
) -> List[str]:
    if verbosity > 2:
        print(f"[TOKENIZE] raw: {repr(text)}")
    words = word_tokenize(text.lower())
    if verbosity > 2:
        print(f"[TOKENIZE] tokens: {words}")

    words = [lemmatizer.lemmatize(w) for w in words if w.isalnum()]
    if verbosity > 2:
        print(f"[CLEANED] lemmas: {words}")
    if lemmatize:
        words = [lemmatizer.lemmatize(w) for w in words if w.isalnum()]
    else:
        words = [w for w in words if w.isalnum()]

    if remove_stopwords:
        words = [w for w in words if w not in STOPWORDS]
        if verbosity > 2:
            print(f"[CLEANED] without stopwords: {words}")

    phrases = []
    for size in range(min_words, len(words) + 1):
        for i in range(len(words) - size + 1):
            phrases.append(" ".join(words[i : i + size]))

    if verbosity > 1:
        print(f"[PHRASES] total: {len(phrases)}")
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

        #        if isinstance(value, str):
        #            if verbosity >= 1:
        #                print(f"[__x__] {new_path}")

        if key in field_names and isinstance(value, str):
            if verbosity >= 1:
                print(f"[MATCH] {new_path}")
            phrases = extract_phrases(
                value, min_words, remove_stopwords, lemmatize, verbosity
            )
            if verbosity >= 2:
                print(f"         value: {repr(value)}")
                print(f"[PHRASES] Extracted from {new_path}:")
                for phrase in phrases:
                    print(f"  - {phrase}")

            #  rename value to ensure readability of code below
            verbatim_phrase = value

            for phrase in phrases:
                results[new_path][phrase].add(tiny_id)
                verbatim_results[new_path][phrase].add(value)
                # if verbatim:
                #    safe_nested_append(
                #        results, new_path, phrase, verbatim_phrase, value=tiny_id
                #    )
                # else:
                #    safe_nested_append(results, new_path, phrase, value=tiny_id)

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
                if verbosity > 1:
                    print(f"OUTPUT: lemma phrase {lemma_phrase}")
                    for verbatim_phrase in (
                        verbatim_map.get(path, {}).get(lemma_phrase, []) or []
                    ):
                        print(f"OUTPUT: verbatim phrase {verbatim_phrase}")
                        for tid in tinyids:
                            safe_nested_append(
                                output,
                                path,
                                lemma_phrase,
                                verbatim_phrase,
                                value=tid,
                            )
                else:
                    for verbatim_phrase in (
                        verbatim_map.get(path, {}).get(lemma_phrase, []) or []
                    ):
                        for tid in tinyids:
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
