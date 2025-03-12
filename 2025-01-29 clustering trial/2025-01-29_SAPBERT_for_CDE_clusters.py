"""
To work, this needs:
    - cell_types.tsv (CL names and identifiers)
    - abbreviations file
"""


import sys
import json
import datetime

import numpy as np
# import torch
from tqdm.auto import tqdm            
from transformers import AutoTokenizer, AutoModel  
from scipy.spatial.distance import cdist
import bioc
import os
import scipy.stats
import json

# os.chdir(r"C:\Users\rotenbergnh\OneDrive - National Institutes of Health\cell type NLP extraction\2024 07 12 SAPBERT model")

# topn = 5

def load_terms(filename):
    term_id_pairs = list()
    with open(filename, "r") as file:
        for line in file:
            line = line.strip()
            if len(line) == 0:
                continue
            fields = line.split("\t")
            if len(fields) != 2:
                raise ValueError("more than 1 tabs in a line:", line)
            name = fields[0]
            id = fields[1]
            term_id_pairs.append((name, id))
    return term_id_pairs

def encode_names(tokenizer, model, names):
    bs = 128
    all_reps = []
    for i in tqdm(np.arange(0, len(names), bs)):
        toks = tokenizer.batch_encode_plus(names[i:i+bs], 
                                           padding="max_length", 
                                           max_length=25, 
                                           truncation=True,
                                           return_tensors="pt")
        output = model(**toks)
        cls_rep = output[0][:,0,:]
        
        all_reps.append(cls_rep.cpu().detach().numpy())
    all_reps_emb = np.concatenate(all_reps, axis=0)
    return all_reps_emb



# add abbrevations.py

import codecs
import gzip
import re

from bioc import biocxml

class AbbreviationExpander:

	def __init__(self, abbr_freq_dict = dict()):
		self.abbr_freq_dict = abbr_freq_dict
		self.abbr_dict = dict()

	def load(self, path):
		if os.path.isdir(path):
			# Load abbreviations from any files found
			dir = os.listdir(path)
			for item in dir:
				if os.path.isfile(path + "/" + item):
					self.load_file(path + "/" + item)				
		elif os.path.isfile(path):  
			# load directly
			self.load_file(path)
		else:  
			raise RuntimeError("Path is not a directory or normal file: " + path)

	def load_file(self, filename):
		if filename.endswith(".xml"):
			self.load_biocxml(filename)
		elif filename.endswith(".tsv"):
			self.load_tsv(filename)
		else:
			print("Abbreviation file does not end in xml or tsv, ignoring: \"{}\"".format(filename))

	def load_tsv(self, filename):
		print("Loading abbreviations from TSV file " + filename)
		count = 0
		if filename.endswith(".gz"):
			file = gzip.open(filename, 'rt', encoding="utf-8") 
		else:
			file = codecs.open(filename, 'r', encoding="utf-8") 
		for line in file:
			line = line.strip()
			if len(line) == 0:
				continue
			try:
				fields = line.split("\t")
				document_ID = fields[0]
				short = fields[1]
				long = fields[2]
				self.add(document_ID, short, long)
				# Handle plural abbreviations
				if short.endswith("s") and long.endswith("s"):
					self.add(document_ID, short[:-1], long[:-1])
				count += 1
			except:
				print("Abbreviation line malformed: \"{}\"".format(line))
		file.close()
		print("Loaded " + str(count) + " abbreviations")
	
	def load_biocxml(self, filename):
		print("Loading abbreviations from BioC file " + filename)
		count = 0
		with open(filename, 'r') as input_file:
			collection = biocxml.load(input_file)
		for document in collection.documents:
			for passage in document.passages:
				annotation_id2text = dict()
				for annotation in passage.annotations:
					if not "type" in annotation.infons or annotation.infons["type"] != "ABBR":
						continue
					annotation_id2text[annotation.id] = annotation.text
				for relation in passage.relations:
					if not "type" in relation.infons or relation.infons["type"] != "ABBR":
						continue
					long = None
					short = None
					for node in relation.nodes:
						if node.role=="LongForm":
							long=annotation_id2text.get(node.refid)
						elif node.role=="ShortForm":
							short=annotation_id2text.get(node.refid)
					if not long is None and not short is None:
						self.add(document.id, short, long)
						# Handle plural abbreviations
						if short.endswith("s") and long.endswith("s"):
							self.add(document.id, short[:-1], long[:-1])
						count += 1
					else:
						print("WARN Could not identify long form & short form for document " + document.id + " relation " + relation.id)
		print("Loaded " + str(count) + " abbreviations")
	
	def add(self, document_ID, short, long):
		if not document_ID in self.abbr_dict:
			self.abbr_dict[document_ID] = dict()
		doc_dict = self.abbr_dict[document_ID]
		# TODO Figure out why Java version used word boundaries
		regex = re.compile("\\b" + re.escape(short) + "\\b")
		if regex.search(long):
			print("INFO Ignoring abbreviation \"" + short + "\" -> \"" + long + "\" because long form contains short form")
		elif short in doc_dict:
			previous_long = doc_dict[short]
			if long != previous_long:
				count = self.get_abbr_freq(short, long)
				previous_count = self.get_abbr_freq(short, previous_long)
				print("WARN Abbreviation \"" + short + "\" -> \"" + long + "\" (count "+str(count)+") is already defined as \"" + previous_long + "\" (count "+str(previous_count)+")")
				if count > previous_count:
					doc_dict[short] = long			
		else:
			doc_dict[short] = long

	def get_abbr_freq(self, short, long):
		if not short in self.abbr_freq_dict:
			return 0
		return self.abbr_freq_dict[short].get(long, 0)

	def do_sub(self, short, long, text):
		if text.find(long) >= 0:
			return re.sub("\s*\(\s*" + re.escape(short) + "\s*\)\s*", " ", text);
		# Change all non-overlapping instances of short to long
		updated = ""
		index = 0
		for match in re.finditer("\\b" + re.escape(short) + "\\b", text):
			start, end = match.span()
			updated += text[index:start] + long
			index = end
		# Add text from last match to end (or whole thing if no matches)
		updated += text[index:]
		return updated

	def expand(self, document_ID, text, expanded_text_dict = dict()):
		if not document_ID in self.abbr_dict:
			return text
		doc_list = list(self.abbr_dict[document_ID].items())
		used = [False] * len(doc_list)
		history = set()
		result = text
		while not result in history:
			history.add(result)
			for index, (short, long) in enumerate(doc_list):
				if not used[index] and result.find(short) >= 0:
# 					print(f"expanded acryonym: {short} ({long})")
					updated = self.do_sub(short, long, result)
					if updated != result:
						result = updated
						used[index] = True
		while (text in expanded_text_dict) and (expanded_text_dict[text] != result):
			text += "#"
		expanded_text_dict[text] = result
		return result

## end abbreviations.py


def write_tsv_output(output_dirpath, normalized_mentions_dict):
    for i, (query_mention, topn_results) in enumerate(normalized_mentions_dict.items()):
        with open(os.path.join(output_dirpath, f"output_{i}-{query_mention[:10]}.tsv"), 'w') as writefp:
            for result in topn_results:
                # write: identifier, identifier_score, database_mention
                writefp.write(str(result[1]) + '\t' + str(result[2]) + '\t' + str(result[0]) + '\n')




def main(input_database_path, output_filename, topn = "all", abbr_freq_filename = None, abbr_paths = None):
    
    # Load abbreviations
    print("Loading abbreviations (if applicable)")
    if (abbr_freq_filename is not None) or (abbr_freq_filename == "") or (abbr_freq_filename == "."):
        with open(abbr_freq_filename, "r") as abbr_freq_file:
            abbr_freq_dict = json.load(abbr_freq_file) # Load the abbreviation frequency file
        abbr = AbbreviationExpander(abbr_freq_dict)
    else:
        abbr = AbbreviationExpander()
        
    if abbr_paths is not None:
        if type(abbr_paths) == str:
            abbr_paths = [abbr_paths]
        for abbr_path in abbr_paths:
            abbr.load(abbr_path)


    print("Loading terms")
    term_id_pairs = []
    if os.path.isfile(input_database_path):
        term_id_pairs = load_terms(input_database_path)
    elif os.path.isdir(input_database_path):
        for path, dirnames, filenames in os.walk(input_database_path):
            for filename in filenames:
                term_id_pairs += load_terms(input_database_path)
    else:
        raise Exception("Could not load input path; it wasn't a file nor directory:", input_database_path)
                
    print("Loaded {} terms".format(len(term_id_pairs)))
    all_names = [p[0] for p in term_id_pairs]
    all_ids = [p[1] for p in term_id_pairs]

    # Load model
    print("Loading model")
    tokenizer = AutoTokenizer.from_pretrained("cambridgeltl/SapBERT-from-PubMedBERT-fulltext")  
    model = AutoModel.from_pretrained("cambridgeltl/SapBERT-from-PubMedBERT-fulltext")

    # Encode terms
    print("Encoding names")
    start = datetime.datetime.now()
    all_reps_emb = encode_names(tokenizer, model, all_names)
    with open(output_filename, 'w') as writefp:
        json.dump({"IDs": all_ids, "names": all_names, "embeddings": all_reps_emb.tolist()}, writefp, indent=3)
    print("Done. Encoding and writing took", (datetime.datetime.now() - start).total_seconds(), "seconds.")
    


if __name__ == "__main__":
    if len(sys.argv) > 1:
        main(*sys.argv[1:])
    else:
        print("not using cmd args")
        # main("cell_types.tsv", '.', ".\SapBERT_config_referenceSpans2.json")
        main(input_database_path=r"C:\Users\rotenbergnh\OneDrive - National Institutes of Health\cell type NLP extraction\2025-01-23 encoding CDEs (Matt)\sample_cde_batch.tsv", 
             # input_query_CDE_filepath=r"C:\Users\rotenbergnh\OneDrive - National Institutes of Health\cell type NLP extraction\2025-01-23 SAPBERT for Matt\sample_query_cde.txt",
             output_filename=r"C:\Users\rotenbergnh\OneDrive - National Institutes of Health\cell type NLP extraction\2025-01-23 encoding CDEs (Matt)\2025-01-29 clustering trial\2025-01-29_SAPBERT_trial_embeddings.json", 
             topn = "all", abbr_freq_filename = None, abbr_paths = None)

