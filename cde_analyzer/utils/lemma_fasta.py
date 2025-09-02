import base64
import sys
import struct
from typing import Any, Dict, List, Set, Optional, DefaultDict, Tuple, Union, TypeAlias
from collections import Counter
from utils.logger import log_if_verbose
from utils.phrase_extraction import make_lemma, rm_stopwords, word_tokenize

system_endianness = sys.byteorder
if system_endianness == "little":
    byte_order = "<"
elif system_endianness == "big":
    byte_order = ">"

def gen_vocab(rows: List[Dict]) -> Dict:
    '''
    Convert the content fields of each dictionary in a list of dictionaries to
    a counter of tokens (words). Each dict is {tinyID: xxx, content_fields: tokens}
    '''
    # vocab: List[Tuple[str,int]]
    vocab_list = Counter()
    for obj in rows:
        for k in obj.keys():
            if k == "tinyId":
                continue
            else:
                vocab_list.update(Counter(obj[k]))
    
    # Sort descending by frequency, then alphabetically.
    vocab_list = sorted(vocab_list.items(), key=lambda item: (-item[1], item[0]))
    
    # Convert to dict with the value the rank order starting with 1,
    #    leaving 0 (0x00) to be the bitbucket for discarded or low-frequency words
    vocab = {}
    counter = 0
    for item in vocab_list: # type: ignore  pylance is wrong Counter is iterable
        # 
        if counter > 32000:
            counter = 0
        else:
            counter += 1
        key, value = item
        my_dict = {}
        if key not in vocab:
            my_dict["encode"] = counter
            my_dict["freq"] = value
            vocab[key] = my_dict
        #     vocab[key] = []  # Initialize an empty list if key is new
        # vocab[key].append(value) 
        else:
            print(f"****************************\n[ERROR] This should not happen: duplicate entry in `vocab`for key: {key}\n*****************************" )
        freq = vocab[key]["freq"]
        log_msg =f"Count of key {key:>35}:\t{freq:6d}"
        log_if_verbose(log_msg, 4)
        
               
    
    return vocab


def enc_vocab(rows: List[Dict], vocab: Dict):
    """
    enc_vocab: encode data fields into uint16 based on frequency

    Args:
        rows (List[Dict]): List of dictionary, each an abstract
            of a CDE. Usually Name, Question, Definition 
            and Permissible Values
        vocab (Dict): Dictionary of the most common words and a 
            corresponding uint16 value
    Return value: List(Dict): The dictionary with data fields encoded
        as uint16_t
    """
    ret_rows =[]
    for obj in rows:
        ret_obj = {}
        for key, value in obj.items():
            if key == "tinyId":
                ret_obj[key] = obj[key]
                continue
            else:
                # for token in value:
                #     uint_word = vocab[token]
                ret_value = [vocab[token]['encode'] for token in value]
                ret_obj[key] = ret_value
                
        ret_rows.append(ret_obj)
    
    return ret_rows
    
    
    
def lemma_data(rows: List[Dict], remove_stopwords: bool) -> List[Dict]:
    """
    lemma_data: lemmatize the data fields (all but tinyId), if remove_stopwords, then
         apply the nltk removal of stopwords
    Args:
        rows (List[Dict]): List of dictionary, each an abstract of a 
            CDE. Usually Name, Question, Definition and Permissible Values.
        remove_stopwords (bool): flag to determine if stopwords should 
            be removed.
    Return value: 
        List(Dict): The data fields are _lists_ of lemmatized words. These
            need to be 'join'-ed to reconstitute the text string. Since the 
            next step is usually enc_vocab, lists of lemmatized tokens is 
            more useful.
    """ 
    ret_rows = []   
    for  obj in rows:
        for key in obj.keys():
            if key == "tinyId":
                my_id =  key
                continue
            else:
                value = obj[key]
                tokens = word_tokenize(value.lower())
                value = make_lemma(tokens, remove_stopwords)
                if remove_stopwords:
                    value = rm_stopwords(value)
            obj[key] = value
            log_msg = f"[LEMMA DATA] tinyId: {my_id}, key {key:<20}, value: value"
            log_if_verbose(log_msg, 3)
        ret_rows.append(obj)
    
    return ret_rows 

def enc_base85(rows: List[Dict]) -> List[Dict]:
    """Encode the data components in base85

    Args:
        rows (List[Dict]): List of simplified CDE with
            payloads encoded as uint16 integers concatenated into 
            a single key:val pair

    Returns:
        List[Dict]: List of simplified CDE dicts with payloads 
            (uint16 data strings) encoded in base85
            
    Note: Must be on concatenated uint16. Cannot concatenate b85 
        payloads
    """
    ret_rows = []
    for obj in rows:
        ret_obj = {}
        for key, value in obj.items():
            if key == "tinyId":
                ret_obj[key] = obj[key]
                my_id = obj[key]
                continue
            else:
                log_msg = f"[ENC_B85] ID: {my_id}, KEY: {key}, VALUE: {value}"
                log_if_verbose(log_msg, 4)
                format_str = byte_order + "{}H".format(len(value))
                packed_value = struct.pack(format_str, *value)
                value = base64.b85encode(packed_value)
                # Since all subsequent use requires a regular string, decode here
                ret_obj[key] = value.decode('utf-8')
                log_msg = f"[ENC_B85] ID: {my_id}, KEY: {key}, VALUE: {value}"
                log_if_verbose(log_msg, 4)
        
        ret_rows.append(ret_obj)
    
    return ret_rows


def append_dict_values(rows: List[Dict]) -> List[Dict]:
    """Concatenate all values but tinyId into a single string

    Args:
        rows (List[Dict]): List of simplifed CDE dict that have
            payload encoded as uint16  

    Returns:
        List[Dict]: _description_
        
    Note: This must precede b85 encoding 
    """
    ret_rows = []
    for obj in rows:
        ret_dict= {}
        concat = []
        for key, value in obj.items():
            if key == "tinyId":
                ret_dict[key] = obj[key]
                continue
            else:
                # print(f"tinyId {ret_dict['tinyId']}, value: {value}")
                concat.extend(value)
        ret_dict["fasta_uint16"] =  concat
        
        ret_rows.append(ret_dict)
    
    return ret_rows