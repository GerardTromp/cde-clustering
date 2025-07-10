# `strip` Command

```
usage: export_help_docs.py strip [-h] [--input INPUT] --fields FIELDS [FIELDS ...] [--min-words MIN_WORDS] [--min-ids MIN_IDS] [--remove-stopwords]
                                 [--lemmatize | --no-lemmatize] [--prune-subphrases] [--output-format {json,csv,tsv}] [--output OUTPUT] [--verbatim]

strip command

options:
  -h, --help            show this help message and exit
  --input INPUT         Input JSON file that has underscore tags fixed.
  --fields FIELDS [FIELDS ...]
                        Field names from pydantic classes
  --min-words MIN_WORDS
                        Minimum length of phrases, i.e., discard shorter phrases. (default: 2)
  --min-ids MIN_IDS     Minimum number of objects that share a phrase. (default: 2)
  --remove-stopwords    Remove common English stop words (articles, prepositions, conjunctions)? (default: False)
  --lemmatize, --no-lemmatize
                        Convert the text to standardized (lemma) form so that similar phrases match? (default: True)
  --prune-subphrases    Collect longest shared phrases? (default: False)
  --output-format {json,csv,tsv}
                        Choose output format. (default JSON)
  --output OUTPUT       Path, including filename, to store results.
  --verbatim            Include verbatim (non-lemmatized) phrases alongside lemma phrases. (default: False)
```