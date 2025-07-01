import re
from collections import defaultdict
from typing import Any, Dict, List, Set, Optional, DefaultDict
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords
import nltk

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


# def extract_phrases(text: str, min_words: int, remove_stopwords: bool) -> List[str]:
#    """Tokenize and lemmatize text into all phrases of length >= min_words."""
#    words = word_tokenize(text.lower())
#    words = [lemmatizer.lemmatize(w) for w in words if w.isalnum()]
#    if remove_stopwords:
#        words = [w for w in words if w not in STOPWORDS]
#
#    phrases = []
#    for size in range(min_words, len(words) + 1):
#        for i in range(len(words) - size + 1):
#            phrases.append(" ".join(words[i : i + size]))
#    return phrases


def extract_phrases(
    text: str, min_words: int, remove_stopwords: bool, lemmatize: bool
) -> List[str]:
    print(f"[TOKENIZE] raw: {repr(text)}")
    words = word_tokenize(text.lower())
    print(f"[TOKENIZE] tokens: {words}")

    words = [lemmatizer.lemmatize(w) for w in words if w.isalnum()]
    print(f"[CLEANED] lemmas: {words}")
    if lemmatize:
        words = [lemmatizer.lemmatize(w) for w in words if w.isalnum()]
    else:
        words = [w for w in words if w.isalnum()]

    if remove_stopwords:
        words = [w for w in words if w not in STOPWORDS]
        print(f"[CLEANED] without stopwords: {words}")

    phrases = []
    for size in range(min_words, len(words) + 1):
        for i in range(len(words) - size + 1):
            phrases.append(" ".join(words[i : i + size]))

    print(f"[PHRASES] total: {len(phrases)}")
    return phrases


def collect_phrases_from_item(
    item: Any,
    field_names: Set[str],
    tiny_id: str,
    current_path: str = "",
    results: Optional[PhraseMap] = None,
    min_words: int = 2,
    remove_stopwords: bool = True,
    verbosity: int = 0,
    lemmatize: bool = True,
) -> PhraseMap:
    """Recursively walk the object and collect phrases from fields matching field_names."""
    if results is None:
        results = defaultdict(lambda: defaultdict(set))

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
                min_words,
                remove_stopwords,
                verbosity,
            )
        return results
    else:
        return results

    for key, value in iterator:
        new_path = f"{current_path}.{key}" if current_path else key

        #        if isinstance(value, str):
        #            if verbosity >= 1:
        #                print(f"[__x__] {new_path}")

        if key in field_names and isinstance(value, str):
            if verbosity >= 1:
                print(f"[MATCH] {new_path}")
            phrases = extract_phrases(value, min_words, remove_stopwords, lemmatize)
            if verbosity >= 2:
                print(f"         value: {repr(value)}")
                print(f"[PHRASES] Extracted from {new_path}:")
                for phrase in phrases:
                    print(f"  - {phrase}")

            phrases = extract_phrases(value, min_words, remove_stopwords, lemmatize)
            for phrase in phrases:
                results[new_path][phrase].add(tiny_id)

        elif isinstance(value, list):
            for elem in value:
                collect_phrases_from_item(
                    elem,
                    field_names,
                    tiny_id,
                    new_path + ".*",
                    results,
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
                min_words,
                remove_stopwords,
                verbosity,
            )

    return results


def collect_all_phrase_occurrences(
    items: List[Any],
    field_names: List[str],
    verbosity: int = 0,
    min_words: int = 2,
    remove_stopwords: bool = True,
    min_ids: int = 2,
    prune_subphrases: bool = True,
    lemmatize: bool = True,
) -> Dict[str, Dict[str, List[str]]]:
    """
    Process all items and return a dict:
      field_path -> phrase -> list of tinyIDs
    Only includes phrases appearing in at least min_ids unique tinyIDs.
    """
    final_result: PhraseMap = defaultdict(lambda: defaultdict(set))
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
            min_words=min_words,
            remove_stopwords=remove_stopwords,
            verbosity=verbosity,
            lemmatize=lemmatize,
        )

    # Post-process to convert sets to sorted lists and apply filtering
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
