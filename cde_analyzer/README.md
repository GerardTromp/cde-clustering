# cde_analyzer

A python framework for analyzing and extracting data from the NLM Common Data ELements Repository. 

Design

The layout of the codebase helps to illustrate the design concept.

```typescript
├── CDE_Schema
├── actions
├── core
├── logic
├── tests
├── utils
├── README.md
└── cde_analyzer.py
```

### Scripts

##### main script `cde_analyzer`

`cde_analyzer` is a wrapper script that requires `action` arguments. Each `action` can accept a variety of arguments that tune its behavior.

##### Actions

The overal design is of a master script that parses the desired actions and then invokes those actions. Each `action` is an argument parser, that then invokes a **logic** script, which is the main script for that `action`.

##### Logic

For each `action` there is a `logic` script. This separate the execution detail from the argument parsing in the action `script`. The logic scripts import main functions from the `utils` directory to keep the logic as "clean" as possible.

##### Utilities (utils)

There are a number of utility functions grouped by general function in the `utils` directory.

##### Unit tests (tests)

Some unit tests have been designed and are in the `tests` directory. Much more needs to be done on that front.

##### Recursion (core)

A significant component is recursion through individual data records, since the overall data model permits nesting of the same class (flexible, but more difficult to work with). The recursive descent enging is in `core`.

### Data model

The **CDE** API was used to define a full class-based model in `pydantic`. The model permits meaningful parsing of individual CDE records with minimal *ad hoc* logic.

The data model currently (2025-07-02) consists of the `Cd` (`CDE_Item`) and `Form` (`CDE_Form`) modules, which represent the top-level entities in the repository. Additonal classes, many shared by `Cd` and `Form` are in `classes`.

#### Design Comment

The design is flexible, allowing for more actions that minimally increase the complexity of the base script and prevent a runaway codebase of separate scripts.

**NB** T<u>he project would greatly benefit from consolidating some functions and refactoring to improve consistency of the codebase. For example, the argumens and flags (Boolean arguments) for actions should have identical names, where relevant, and similar names where functionality is semantically related.</u>

### Status (2025-07-02)

At present the non-cache code tree is:

```typescript
├── CDE_Schema
│   ├── CDE_Form.py
│   ├── CDE_Item.py
│   ├── __init__.py
│   └── classes.py
├── README.md
├── actions
│   ├── count.py
│   ├── extract.py
│   ├── html.py
│   └── phrase.py
├── cde_analyzer.py
├── core
│   └── recursor.py
├── logic
│   ├── counter.py
│   ├── extractor.py
│   └── htlm_stripper.py
├── tests
│   └── test_helpers.py
└── utils
    ├── cde_impexport.py
    ├── datatype_check.py
    ├── helpers.py
    ├── html.py
    ├── logger.py
    ├── output_writer.py
    └── path_utils.py
```

## Extension

Can easily be extended to comport with the `SearchDocumentResponse model` (one or more `Cd` records wrapped in fields for a response from a `GET` request to the `API`) and `SearchFormResponse` (same for `Form` response). 

