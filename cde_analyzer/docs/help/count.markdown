# `count` Command

```
usage: export_help_docs.py count [-h] [--input INPUT] --fields FIELDS [FIELDS ...] [--match-type {non_null,null,fixed,regex}] [--value VALUE] [--output-format {json,csv,tsv}]
                                 [--output OUTPUT] [--group-by GROUP_BY] [--group-type {top,path,terminal}] [--logic LOGIC] [--verbose] [--count-type]
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
                        Interpret group-by field as a top-level, full-path, or terminal (deepest) component of model
  --logic LOGIC         Logical expression (e.g. 'A and not B')
  --verbose             Enable debug output for group-by resolution
  --count-type          Classify and count field values by type (int, float, strN)
  --char-limit CHAR_LIMIT
                        Character limit for short string classification
  --output-flat         Flatten nested result keys for easier analysis
```