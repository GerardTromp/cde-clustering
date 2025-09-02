from typing import Dict, Set, Union
from collections import defaultdict


def prune_subphrases_threshold(
    phrase_map: Dict[str, Set[str]],
    min_ids: int = 2,
    min_words: int = 1,
) -> Dict[str, Set[str]]:
    """
    Retain phrases shared by at least `min_ids` IDs that are not substrings of
    longer phrases with equal or greater support.
    """
    # Sort by descending word count, then lexically
    sorted_phrases = sorted(phrase_map.keys(), key=lambda p: (-len(p.split()), p))

    retained: Dict[str, Set[str]] = {}
    for phrase in sorted_phrases:
        ids = phrase_map[phrase]
        if len(ids) < min_ids or len(phrase.split()) < min_words:
            continue  # Doesn't meet minimum thresholds

        # Check if it's a substring of any already-retained longer phrase
        is_subsumed = False
        for longer_phrase in retained:
            if phrase in longer_phrase and retained[longer_phrase] >= ids:
                is_subsumed = True
                break

        if not is_subsumed:
            retained[phrase] = ids

    return retained


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


def prune_subphrases_global(phrase_map: Dict[str, Set[str]]) -> Dict[str, Set[str]]:
    """
    Collapse shorter phrases globally if they are substrings of longer phrases.
    Retains only globally longest (non-sub)phrases.
    """
    all_phrases = list(phrase_map.keys())

    # Sort phrases by descending word count, then lexically
    sorted_phrases = sorted(all_phrases, key=lambda p: (-len(p.split()), p))

    kept_phrases = set()
    for p in sorted_phrases:
        if not any(p in longer and p != longer for longer in kept_phrases):
            kept_phrases.add(p)

    # Rebuild phrase map using only retained phrases
    collapsed_map: Dict[str, Set[str]] = {
        phrase: phrase_map[phrase] for phrase in kept_phrases
    }

    return collapsed_map
