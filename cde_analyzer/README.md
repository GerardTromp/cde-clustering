# cde_analyzer

A python framework for analyzing and extracting data from the NLM Common Data ELements Repository. 

The data model (class model) is implemented in `pydantic`. It is specified in the CDE_Schema subdirectory. Currently `Cd` and `Form` are implmented. Can easily be extended to comport with the 
`SearchDocumentResponse model` (one or more `Cd` records wrapped in fields for a response from a `GET` request to the `API`) and `SearchFormResponse` (same for `Form` response). 

Additional functionality can be added to the main script by adding an appropriate `action` and `logic` set of scripts. 
