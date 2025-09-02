import nltk
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords
from nltk.tag import pos_tag
from nltk import word_tokenize, pos_tag
from nltk.corpus import wordnet
from collections import defaultdict
from typing import Any, Dict, List, Set, Optional, DefaultDict, Tuple, Union, TypeAlias
from utils.logger import log_if_verbose

# Download resources quietly
nltk.download("punkt", quiet=True)
nltk.download("punkt_tab", quiet=True)
nltk.download("wordnet", quiet=True)
nltk.download("stopwords", quiet=True)
nltk.download("averaged_perceptron_tagger_eng", quiet=True)
nltk.download("omw-1.4", quiet=True)

# Global resources
STOPWORDS = set(stopwords.words("english"))
lemmatizer = WordNetLemmatizer()

# Type alias for clarity
PhraseMap = DefaultDict[str, DefaultDict[str, Set[str]]]
NestedDict: TypeAlias = Dict[str, Union[List, "NestedDict"]]


def get_wordnet_pos(tag: str) -> Union[str, None]:
    """Map POS tag to format WordNetLemmatizer accepts."""
    if tag.startswith("J"):
        return wordnet.ADJ
    elif tag.startswith("V"):
        return wordnet.VERB
    elif tag.startswith("N"):
        return wordnet.NOUN
    elif tag.startswith("R"):
        return wordnet.ADV
    return None  # do not convert POS-less word


def make_lemma(
    tokens: list, remove_stopwords: bool
) -> List[str]:
    
    pos_tags = pos_tag(tokens)
    log_if_verbose(f"[POS] tokens: {tokens}", 3)
    log_if_verbose(f"[POS] pos_tags: {pos_tags}", 3)

    words = []
    for word, pos in pos_tags:
        wn_pos = get_wordnet_pos(pos)
        if wn_pos:
            lemma = lemmatizer.lemmatize(word, pos=wn_pos)
        else:
            lemma = word
        words.append(lemma)

    log_if_verbose(f"[CLEANED] lemmas: {words}", 3)
    
    return words


def rm_stopwords(words: list) -> List:
    words = [w for w in words if w not in STOPWORDS]
    log_if_verbose(f"[CLEANED] without stopwords: {words}", 3)

    log_if_verbose(
        f"[POS] Number of words: {len(words)}", 3
    )

    return words

def tokenize_text(text:str) -> List[str]:
    '''Simple tokenization
    
    Args:
        text (str): Some sentence or phrase.
    Return:
        list (str): separated alphanumeric tokens. 
    '''
    log_if_verbose(f"[TOKENIZE] raw: {repr(text)}", 3)
    tokens = word_tokenize(text.lower())
    log_if_verbose(f"[TOKENIZE] tokens: {tokens}", 3)

    # Filter out non-alphanumeric before POS tagging
    tokens = [w for w in tokens if w.isalnum()]
    if not tokens:
        log_if_verbose(f"[POS] Skipped empty token list: {repr(text)}", 3)
        return []
    
    return tokens
 
    
def extract_phrases(
    text: str, min_words: int, remove_stopwords: bool, lemmatize: bool
) -> List[str]:
    # log_if_verbose(f"[TOKENIZE] raw: {repr(text)}", 3)
    # tokens = word_tokenize(text.lower())
    # log_if_verbose(f"[TOKENIZE] tokens: {tokens}", 3)

    # # Filter out non-alphanumeric before POS tagging
    # tokens = [w for w in tokens if w.isalnum()]
    # if not tokens:
    #     log_if_verbose(f"[POS] Skipped empty token list: {repr(text)}", 3)
    #     return []
    tokens = tokenize_text(text)

    if lemmatize:
        words = make_lemma(tokens=tokens, remove_stopwords=remove_stopwords)
        
    #     pos_tags = pos_tag(tokens)
    #     log_if_verbose(f"[POS] tokens: {tokens}", 3)
    #     log_if_verbose(f"[POS] pos_tags: {pos_tags}", 3)

    #     words = []
    #     for word, pos in pos_tags:
    #         wn_pos = get_wordnet_pos(pos)
    #         if wn_pos:
    #             lemma = lemmatizer.lemmatize(word, pos=wn_pos)
    #         else:
    #             lemma = word
    #         words.append(lemma)
    else:
        words = tokens
    

    log_if_verbose(f"[CLEANED] lemmas: {words}", 3)

    if remove_stopwords:
        words = rm_stopwords(words)
    #     words = [w for w in words if w not in STOPWORDS]
    #     log_if_verbose(f"[CLEANED] without stopwords: {words}", 3)

    log_if_verbose(
        f"[POS] Just before phrase collection. length words: {len(words)}", 3
    )

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
                value, min_words, remove_stopwords, lemmatize
            )
            # No need to use log_if_verbose here. Want to ONLY execute if logger desired
            if verbosity >= 3:
                log_if_verbose(f"         value: {repr(value)}")
                log_if_verbose(f"[PHRASES] Extracted from {new_path}:")
                for phrase in phrases:
                    log_if_verbose(f"  - {phrase}")

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
