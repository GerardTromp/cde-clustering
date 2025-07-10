# `fix_underscores` Command

```
usage: export_help_docs.py fix_underscores [-h] [--id-list ID_LIST [ID_LIST ...] | --id-file ID_FILE] [--id-type ID_TYPE] [--exclude | --no-exclude] --path-file PATH_FILE
                                           --output OUTPUT [--output-format {json,csv,tsv}]
                                           input

fix_underscores command

positional arguments:
  input                 Input JSON file

options:
  -h, --help            show this help message and exit
  --id-list ID_LIST [ID_LIST ...]
                        List of identifiers to exclude/include (see --exclude)
  --id-file ID_FILE     Path to file with list of identifiers (JSON, csv, or tsv)
  --id-type ID_TYPE     Pydantic path/tag for identifier, i.e., what type of identifier. Required if either --id-list or --id-file is provided.
  --exclude, --no-exclude
                        Should provided tinyId's be excluded (--exclude) or included (--no-exclude) (default: True)
  --path-file PATH_FILE
                        File with the key-value pairs defining the names (key) and paths (value) to be extracted
  --output OUTPUT       Path, including filename, where to store extracted fields.
  --output-format {json,csv,tsv}
                        Format for file with extracted data.
```