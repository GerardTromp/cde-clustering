# CDE Analyzer CLI Cheat Sheet

# `cde_analyzer` Command

```typescript
usage: export_help_docs.py [-h] {} ...

CDE Analyzer CLI

positional arguments:
  {}

options:
  -h, --help  show this help message and exit
```

---

# `phrase` Command

```typescript
usage: phrase [-h] [--input INPUT] --fields FIELDS [FIELDS ...] \
              [--min-words MIN_WORDS] [--min-ids MIN_IDS] [--remove-stopwords] \
              [--lemmatize | --no-lemmatize] [--prune-subphrases] \
              [--output-format {json,csv,tsv}] [--output OUTPUT] [--verbatim]

phrase command

options:
  -h, --help            show this help message and exit
  --input INPUT         Input JSON file
  --fields FIELDS [FIELDS ...]
                        Field names from pydantic classes
  --min-words MIN_WORDS
                        Minimum length of phrases, i.e., discard shorter phrases
  --min-ids MIN_IDS     Minimum number of objects that share a phrase
  --remove-stopwords    Remove common English stop words (articles, prepositions, conjunctions)?
  --lemmatize, --no-lemmatize
                        Convert the text to standardized (lemma) form so that similar phrases match? 
                        (default: True)
  --prune-subphrases    Collect longest shared phrases?
  --output-format {json,csv,tsv}
                        Choose output format
  --output OUTPUT       Path, including filename, to store results.
  --verbatim            Include verbatim (non-lemmatized) phrases alongside lemma phrases
```

---

# `count` Command

```typescript
usage: count [-h] [--input INPUT] --fields FIELDS [FIELDS ...] \
             [--match-type {non_null,null,fixed,regex}] [--value VALUE] \
             [--output-format {json,csv,tsv}] [--output OUTPUT] [--group-by GROUP_BY] \
             [--group-type {top,path,terminal}] [--logic LOGIC] [--verbose] [--count-type]
             [--char-limit CHAR_LIMIT] [--output-flat]

count command

options:
  -h, --help            show this help message and exit
  --input INPUT         Input JSON file.
  --fields FIELDS [FIELDS ...]
  --match-type {non_null,null,fixed,regex}
                        Type of match, null type is empty string or list, or None.
  --value VALUE         Value to match if match-type is fixed or regex.
  --output-format {json,csv,tsv}
                        Output format.
  --output OUTPUT       Path, including filename, to store results.
  --group-by GROUP_BY   Dotted path or key name to group by (e.g. tinyId or path.to.tinyId)
  --group-type {top,path,terminal}
                        Interpret group-by field as a top-level, full-path, or terminal 
                        (deepest) component of model
  --logic LOGIC         Logical expression (e.g. 'A and not B')
  --verbose             Enable debug output for group-by resolution
  --count-type          Classify and count field values by type (int, float, strN)
  --char-limit CHAR_LIMIT
                        Character limit for short string classification
  --output-flat         Flatten nested result keys for easier analysis
```

---

# `strip` Command

```typescript
usage: strip [-h] [--input INPUT] [--output OUTPUT] \
             --model {CDE,Form} [--outdir OUTDIR] [--format {json,yaml,csv}] \
             [--dry-run] [--verbosity] [--logfile LOGFILE] [--pretty | --no-pretty] \
             [--set-keys | --no-set-keys] [--tables | --no-tables] [--colnames]

strip command

options:
  -h, --help            show this help message and exit
  --input INPUT         Input JSON file that has underscore tags fixed.
  --output OUTPUT       Path, including filename, to store results.
  --model {CDE,Form}, -m {CDE,Form}
                        Model to use for validation
  --outdir OUTDIR       Directory for output files (default: current directory)
  --format {json,yaml,csv}
                        Output format (default: json)
  --dry-run             Do not write output files
  --verbosity, -v       Increase verbosity level (-vv for debug)
  --logfile LOGFILE     Optional log file path
  --pretty, --no-pretty
                        Produce pretty (default: --pretty) or minified (--no-pretty) 
                        JSON (no whitespace) (default: True)
  --set-keys, --no-set-keys
                        Save model with keys only represented if they are set 
                        (no null, None, or empty sets) (default: True)
  --tables, --no-tables
                        Convert html tables to JSON representation (default: --tables, 
                        i.e., true) or munged text (--no-tables) (default: True)
  --colnames            Use first row of table as column names (default: false). 
                        Only relevant if --tables.---

```

---

# `extract_embed` Command

```typescript
usage: extract_embed [-h] [--input INPUT] \
                     --fields FIELDS [FIELDS ...] [--min-words MIN_WORDS] \
                     [--min-ids MIN_IDS] [--remove-stopwords]
                     [--lemmatize | --no-lemmatize] [--prune-subphrases] 
                     [--output-format {json,csv,tsv}] [--output OUTPUT] 
                     [--verbatim]

extract_embed command

options:
  -h, --help            show this help message and exit
  --input INPUT         Input JSON file.
  --fields FIELDS [FIELDS ...]
                        Field names from pydantic classes.
  --min-words MIN_WORDS
                        Minimum length of phrases, i.e., discard shorter phrases. (default: 2)
  --min-ids MIN_IDS     Minimum number of objects that share a phrase. (default: 2)
  --remove-stopwords    Remove common English stop words (articles, prepositions, conjunctions)? 
                        (default: False)
  --lemmatize, --no-lemmatize
                        Convert the text to standardized (lemma) form so that similar phrases 
                        match? (default: True)
  --prune-subphrases    Collect longest shared phrases? (default: False)
  --output-format {json,csv,tsv}
                        Choose output format. (default JSON)
  --output OUTPUT       Path, including filename, to store results.
  --verbatim            Include verbatim (non-lemmatized) phrases alongside lemma phrases. 
                        (default: False)
```

---

# `fix_underscores` Command

```typescript
usage: fix_underscores [-h] [--input INPUT] [--output OUTPUT] [--prefix PREFIX] \
                       [--depth DEPTH]

fix_underscores command

options:
  -h, --help       show this help message and exit
  --input INPUT    Full path, including name, of input JSON file
  --output OUTPUT  Full path, including name, of output JSON file
  --prefix PREFIX  Character to prepend on fields starting with an underscore
  --depth DEPTH    Maximum depth (JSON nesting) to process
```