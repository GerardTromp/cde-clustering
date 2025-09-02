import re
import logging
import json
from collections import defaultdict
from pydantic import BaseModel
from typing import Any, Dict, List, Set, Optional, DefaultDict, Tuple, Union, TypeAlias, Type, TypeVar
from utils.helpers import safe_nested_append
from utils.logger import log_if_verbose
from utils.lemma_fasta import enc_vocab, gen_vocab, lemma_data,  enc_base85, append_dict_values
from utils.phrase_extraction import make_lemma, rm_stopwords, extract_phrases
from logic.extract_embed import extract_path
from datetime import datetime
from pathlib import Path


# logger = logging.getLogger("cde_analyzer.phrase")
logger = logging.getLogger(__name__)

ModelType = TypeVar("ModelType", bound=BaseModel)

def encode_pfasta(rows: List[Dict], schema: Dict, remove_stopwords: bool) -> List:
    '''
    Encode each of data fields in the list of Dicts (ID is not encoded). 
       1. Lemmatize content fields [fields other than ID (tinyId)]
          
       2. Concatenate content fields in order of schema, and:
          a. generate a vocab dictionary
          b. encode the words in the concatenated strings into uint16_t
          c. encode the uint16_t "strings" into base85  
       Dicts are simple dicts (nested flattened) with ID (tinyId) and
       fields specified by schema read from --path-file (schema in file). 
    Return is dict of ID, base85-encoded concatenated "string"
    
    Permits output of ASCII file that is pseudo-FASTA:
       > tinyId (or other ID)
       "base85-encoded payload"
    Technically no need to wrap the payload although probably more readable.
    '''
    # lemmatize 
    lrows = lemma_data(rows, remove_stopwords)
    vocab = gen_vocab(lrows)
    
    
    return rows


def make_pfasta(
    model_class: Type[ModelType],
    data: List[Dict],
    tinyids: List[str],
    output: Optional[str] = None,
    format: str = "json",
    schema_path: Optional[str] = None,
    exclude: bool = False,
    collapse: bool = False,
    simplify: bool = False,
    remove_stopwords: bool = False, 
):
    """Converts text components of CDE to pseudo fasta format

    Args:
        model_class (Type[ModelType]): _description_
        data (List[Dict]): _description_
        tinyids (List[str]): _description_
        output (Optional[str], optional): _description_. Defaults to None.
        format (str, optional): _description_. Defaults to "json".
        schema_path (Optional[str], optional): _description_. Defaults to None.
        exclude (bool, optional): _description_. Defaults to False.
        collapse (bool, optional): _description_. Defaults to False.
        simplify (bool, optional): _description_. Defaults to False.
        remove_stopwords (bool, optional): _description_. Defaults to False.
    
    Return value:
        None.
        This function writes out 2 files. One a compound JSON and the other a 
        FASTA-like file.
    """
    if output is None:
       print(f"""******************************\nHere `output` MUST be defined.
Multiple files are generated and cannot be accommodated as terminal output.
""") 
    format = "pfasta"
    rows = extract_path(
        model_class,
        data,
        tinyids,
        output,
        format,
        schema_path,
        exclude,
        collapse,
        simplify,        
    )
    lemmas = lemma_data(rows, remove_stopwords) # type: ignore
    vocab = gen_vocab(lemmas)
    # Should be list of Dicts with keys as in schema_path with
    #     values encoded in uint16 
    uint16_lemmas = enc_vocab(lemmas,vocab) 
    
    b85_cde_values =  enc_base85(uint16_lemmas)
    concatenated_uint16 = append_dict_values(uint16_lemmas)
    b85_concatenated = enc_base85(concatenated_uint16)
    complex_json = {}
    complex_json["lemmatized"] = lemmas
    complex_json["verbatim"] = rows
    complex_json["b85"] = b85_cde_values
    complex_json["b85_concat"] = b85_concatenated
    complex_json["vocab"] = vocab
    
    
    now = datetime.now()
    datestring =  now.strftime("%Y%m%d-%H%M")
    
    if output is not None:
        output = Path(output).stem # type: ignore -- check that output is defined above
        json_file = f"{output}_compound_{datestring}.json"
        pfasta_file = f"{output}_{datestring}.pfasta"
        with open(json_file, "w") as f:  
            json.dump(complex_json, f, indent=2)
        with open(pfasta_file, "w") as f:  
            for obj in b85_concatenated:
                for key, value in obj.items():
                    if key == "tinyId":
                        f.write(f">{value}\n")
                    else:
                        for i in range(0, len(value), 80): # ideally need a chunk_size var
                            chunk = value[i:i+80]
                            f.write(f"-{chunk}\n")
    
    
                        
    
     
    
    
    
    


