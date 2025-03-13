# -*- coding: utf-8 -*-
"""
Created on Sat Jan 25 12:02:41 2025

@author: rotenbergnh
"""

# code copied from: https://github.com/ncbi/MedCPT/blob/main/README.md

import torch
from transformers import AutoTokenizer, AutoModel, AutoModelForSequenceClassification
import numpy as np
import os
import sys
import argparse
import json
import datetime


"""
Inputs:
    - input_database_path: tsv with 2 columns: description, identifier; there is 1 header line skipped
    - output_filename: output json file mapping identifier to the description embeddings
    - encoder_type (optional): either MedCPT's "Article-Encoder" (default) or "Query-Encoder"
    - article_delimiter: if you choose Article-Encoder, then this delimiter splits the title from article (required if using Article-Encoder)
"""

print(sys.argv)
if len(sys.argv) > 1:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_database_path", "-i", type=str, required=True, help="tsv with 2 columns: description, identifier; there is 1 header line skipped")
    parser.add_argument("--output_filename", "-o", type=str, required=True, help="The type of evaluation to perform")
    parser.add_argument("--encoder_type", "-e", choices = {"Article-Encoder", "Query-Encoder"}, default="Article-Encoder", help="either MedCPT's Article-Encoder (default) or Query-Encoder")
    parser.add_argument("--article_delimiter", "-d", type=str, default=None, help="this delimiter splits the title from article (required if using Article-Encoder); default is '.'")
    args = parser.parse_args()

else:
    raise Exception("expected commandline args")

if args.encoder_type != "Article-Encoder" and args.article_delimiter is not None:
    raise Exception("article_delimiter is incompatible with models other than Article-Encoder")
elif args.article_delimiter is None:
    args.article_delimiter = '.'


def MedCPT_query_encoder(queries):
    model = AutoModel.from_pretrained("ncbi/MedCPT-Query-Encoder")
    tokenizer = AutoTokenizer.from_pretrained("ncbi/MedCPT-Query-Encoder")
    
    
    with torch.no_grad():
        # tokenize the queries
        encoded = tokenizer(
            queries, 
            truncation=True, 
            padding=True, 
            return_tensors='pt', 
            max_length=64,
        )
        
        # encode the queries (use the [CLS] last hidden states as the representations)
        q_embeds = model(**encoded).last_hidden_state[:, 0, :]
    
        print(q_embeds)
        print("query embeds size:", q_embeds.size())
    return q_embeds


def MedCPT_article_encoder(articles):
    model = AutoModel.from_pretrained("ncbi/MedCPT-Article-Encoder")
    tokenizer = AutoTokenizer.from_pretrained("ncbi/MedCPT-Article-Encoder")
    
    with torch.no_grad():
        # tokenize the queries
        encoded = tokenizer(
            articles, 
            truncation=True, 
            padding=True, 
            return_tensors='pt', 
            max_length=512,
        )
        
        # encode the queries (use the [CLS] last hidden states as the representations)
        a_embeds = model(**encoded).last_hidden_state[:, 0, :]
        
        print(a_embeds)
        print("articles embeds size:", a_embeds.size())
    return a_embeds

def load_terms(filename):
    term_id_pairs = list()
    with open(filename, "r") as file:
        for i, line in enumerate(file):
            line = line.strip()
            if len(line) == 0:
                continue
            if i==0:
                print("skipping header line")
                continue
            fields = line.split("\t")
            if len(fields) != 2:
                raise ValueError("more than 1 tabs in a line:", line)
            name = fields[0]
            id = fields[1]
            term_id_pairs.append((name, id))
    return term_id_pairs

print("Loading terms")
term_id_pairs = []
if os.path.isfile(args.input_database_path):
    term_id_pairs = load_terms(args.input_database_path)
elif os.path.isdir(args.input_database_path):
    for path, dirnames, filenames in os.walk(args.input_database_path):
        for filename in filenames:
            term_id_pairs += load_terms(os.path.join(path, filename))
else:
    raise Exception("Could not load input path; it wasn't a file nor directory:", args.input_database_path)
            
print("Loaded {} terms".format(len(term_id_pairs)))
all_names = [p[0] for p in term_id_pairs]
all_ids = [p[1] for p in term_id_pairs]

start_time = datetime.datetime.now()
if args.encoder_type == "Query-Encoder":
    embeddings = MedCPT_query_encoder(all_names)
elif args.encoder_type == "Article-Encoder":
    all_names = [name.split(args.article_delimiter, maxsplit=1) if args.article_delimiter in name else ["", name] for name in all_names]
    # all descriptions must have length 2, even if the 1st or 2nd string is empty
    all_names = [(a[0].strip(), a[1].strip()) for a in all_names]
    embeddings = MedCPT_article_encoder(all_names)
else:
    raise Exception()

# dump embeddings:
with open(args.output_filename, 'w') as writefp:
    json.dump({"IDs": all_ids, "names": all_names, "embeddings": embeddings.tolist()}, writefp, indent=3)
print("Done. Encoding and writing took", (datetime.datetime.now() - start_time).total_seconds(), "seconds.")



