import nltk
import spacy
import functools
from collections import Counter
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
_spacy_initialized = False

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


def lemmatize(
    text: str, remove_stopwords: bool, verbosity: int
) -> List[str]:
    log_if_verbose(f"[TOKENIZE] raw: {repr(text)}", 3)
    tokens = word_tokenize(text.lower())
    log_if_verbose(f"[TOKENIZE] tokens: {tokens}", 3)

    # Filter out non-alphanumeric before POS tagging
    tokens = [w for w in tokens if w.isalnum()]
    if not tokens:
        log_if_verbose(f"[POS] Skipped empty token list: {repr(text)}", 3)
        return []

    
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

    if remove_stopwords:
        words = [w for w in words if w not in STOPWORDS]
        log_if_verbose(f"[CLEANED] without stopwords: {words}", 3)

    log_if_verbose(
        f"[POS] Number of words: {len(words)}", 3
    )

    return words


def collect_lemmas_from_item(
    item: Any,
    field_names: Set[str],
    tiny_id: str,
    current_path: str = "",
    results: Optional[PhraseMap] = None,
    verbatim_results: Optional[PhraseMap] = None,
    remove_stopwords: bool = True,
    verbosity: int = 0,
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
            collect_lemmas_from_item(
                elem,
                field_names,
                tiny_id,
                current_path + ".*" if current_path else "*",
                results,
                verbatim_results,
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
            phrases = lemmatize(
                value, remove_stopwords, verbosity
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
                collect_lemmas_from_item(
                    elem,
                    field_names,
                    tiny_id,
                    new_path + ".*",
                    results,
                    verbatim_results,
                    remove_stopwords,
                    verbosity,
                )

        elif hasattr(value, "__dict__") or isinstance(value, dict):
            collect_lemmas_from_item(
                value,
                field_names,
                tiny_id,
                new_path,
                results,
                verbatim_results,
                remove_stopwords,
                verbosity,
            )

    return results, verbatim_results


def initalize_spacy(setup_func):
    """
    A decorator to ensure a setup function is called before the decorated function.
    The setup function is called only once per decorated function.
    """
    spacy_initialized = False

    @functools.wraps(setup_func)
    def wrapper(*args, **kwargs):
        nonlocal spacy_initialized
        if not spacy_initialized:
            setup_func()
            spacy_initialized = True
        return setup_func(*args, **kwargs)
    return wrapper


def _initialize_spacy():
    global nlp
    nlp = spacy.load("en_core_web_sm", disable=["ner","parser"])

@initalize_spacy(_initialize_spacy)

# def vocab_decorator(func):
#     def wrapper(*args, **kwargs):
#         _initialize_spacy()
#         result = func(*args, **kwargs)
#         return result
#     return wrapper

# def build_vocab(docs, max_vocab=32000):
#     _initialize_spacy()  # Ensure initialization before use
#     _build_vocab(docs, max_vocab)
    
# @vocab_decorator
def build_vocab(docs, max_vocab):
    all_tokens = []
    for doc in docs:
        lemmas = [t.lemma_.lower() for t in nlp(doc) if t.is_alpha and len(t) > 2]
        all_tokens.extend(lemmas)
    freq = Counter(all_tokens)
    vocab = {w: i+1 for i, (w, _) in enumerate(freq.most_common(max_vocab))}
    return vocab


def encode_doc(doc, vocab):
    return [vocab.get(t.lemma_.lower(), 0) for t in nlp(doc) if t.is_alpha]


# # Example usage
# docs = ["History of breast cancer", "Family history of cancer"]
# vocab = build_vocab(docs)
# encoded = [encode_doc(d, vocab) for d in docs]
