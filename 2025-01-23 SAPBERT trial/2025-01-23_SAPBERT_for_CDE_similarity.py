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

def topk(array, k, axis=-1, sorted=True):
    # Use np.argpartition is faster than np.argsort, but do not return the values in order
    # We use array.take because you can specify the axis
    partitioned_ind = (
        np.argpartition(array, -k, axis=axis)
        .take(indices=range(-k, 0), axis=axis)
    )
    # We use the newly selected indices to find the score of the top-k values
    partitioned_scores = np.take_along_axis(array, partitioned_ind, axis=axis)
    
    if sorted:
        # Since our top-k indices are not correctly ordered, we can sort them with argsort
        # only if sorted=True (otherwise we keep it in an arbitrary order)
        sorted_trunc_ind = np.flip(
            np.argsort(partitioned_scores, axis=axis), axis=axis
        )

        # We again use np.take_along_axis as we have an array of indices that we use to
        # decide which values to select
        ind = np.take_along_axis(partitioned_ind, sorted_trunc_ind, axis=axis)
        scores = np.take_along_axis(partitioned_scores, sorted_trunc_ind, axis=axis)
    else:
        ind = partitioned_ind
        scores = partitioned_scores
    
    return scores, ind


def run_query(tokenizer, model, all_reps_emb, term_id_pairs, query, topn):
    query_toks = tokenizer.batch_encode_plus([query], padding="max_length", max_length=25, truncation=True, return_tensors="pt")
    query_output = model(**query_toks)
    query_cls_rep = query_output[0][:,0,:]
    #dist = cdist(query_cls_rep.cpu().detach().numpy(), all_reps_emb)
    dist = cdist(query_cls_rep.cpu().detach().numpy(), all_reps_emb, metric="cosine")
    topn_scores, topn_indices = topk(-dist, topn)
    #print("topn_scores = {} topn_indices = {}".format(type(topn_scores), type(topn_indices)))
    #print("topn_scores = {} topn_indices = {}".format(topn_scores, topn_indices))
    topn_results = list()
    for ii in range(len(topn_indices[0])):
        #print("ii = {} type = {}".format(ii, type(ii)))
        index = topn_indices[0][ii]
        score = topn_scores[0][ii]
        #print("index = {} type = {}".format(index, type(index)))
        #print("score = {} type = {}".format(score, type(score)))
        name, identifier = term_id_pairs[index]
        #print("identifier = {} type = {}".format(identifier, type(identifier)))
        topn_results.append((name, identifier, score))
    return topn_results


def get_query_texts_from_txt(input_filename):
    mentions = []
    print("Loading mention texts from file " + input_filename)
    with open(input_filename, "r") as fp:
        for line in fp:
            line = line.strip()
            if line not in mentions:
                mentions.append(line)
    return mentions

def process_collection(input_filename, normalized, output_filename, min_similarity):
    print("Processing file " + input_filename + " to " + output_filename)
    with open(input_filename, "r") as fp:
        input_collection = bioc.load(fp)
    output_collection = bioc.BioCCollection()
    for document in input_collection.documents:
        for passage in document.passages:
            for annotation in passage.annotations:
                topn_results = normalized.get((document.id, annotation.text))
                if topn_results is None:
                    print("WARN: No normalized identifier found for document id = {} mention text = {}".format(document.id, annotation.text))
                    annotation.infons["identifier"] = "-"
                    for index in range(topn):
                        annotation.infons["id_" + str(index)] = "-"
                else:
                    for index in range(topn):
                        identifier = topn_results[index][1] if index < len(topn_results) else "-"
                        if index == 0:
                            
                            annotation.infons["identifier"] = identifier # removed below if score is too low
                            
                            if True: # previously, the condition here was: if len(topn_results) > 0:
                                identifier_score = 1.0 + topn_results[index][2]
                                identifier_score *= identifier_score
                                annotation.infons["identifier_score"] = identifier_score
                                if min_similarity > identifier_score:
                                    annotation.infons["identifier"] = ""
                                span_score = float(annotation.infons.get("score", 1.0))
                                #print("span_score = {} type(span_score) = {}".format(span_score, type(span_score)))
                                annotation.infons["span_score"] = span_score
                                annotation.infons["score"] = span_score * identifier_score
                                annotation.infons["identifier_name"] = topn_results[index][0]
                        annotation.infons["id_" + str(index)] = identifier
        output_collection.add_document(document)
    ## change entity name:
    for doc in output_collection.documents:
        for passage in doc.passages:
            for ann in passage.annotations:
                ann.infons['type'] = "cell"
                if ('identifier_name' in ann.infons) and ('identifier' in ann.infons) and \
                    (ann.infons['identifier'] is not None) and (len(ann.infons['identifier']) > 0):
                    ann.infons['note'] = f"{ann.infons['identifier']} == {ann.infons['identifier_name']}"
    with open(output_filename, "w") as fp:
        bioc.dump(output_collection, fp)



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



# for backwards compatibility
def main(term_filename, abbr_freq_filename, config_path):
    with open(config_path) as config_file:
        config = json.load(config_file)
    return main(term_filename, abbr_freq_filename, config['abbr_paths'],
                config["input"], config["output"])




def main(input_database_path, input_query_CDE_filepath, output_dirpath, topn = "all", abbr_freq_filename = None, abbr_paths = None):
    
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
    all_reps_emb = encode_names(tokenizer, model, all_names)

    # Process files
    files = list()

    mentions = get_query_texts_from_txt(input_query_CDE_filepath)
    if topn == "all":
        topn = all_reps_emb.shape[0]

    normalized = dict()
    query_cache = dict()
    expanded_text_dict = dict()
    start = datetime.datetime.now()
    for index, mention_text in enumerate(tqdm(mentions)):
        expanded_text = abbr.expand("", mention_text, expanded_text_dict) # supposed to have document_id
        if expanded_text in query_cache:
            topn_results = query_cache[expanded_text]
            # elapsed = datetime.datetime.now() - start
            # total_time = len(mentions) * (elapsed / (index + 1))
#             print (" {} / {} mention_text: \"{}\" expanded_text: \"{}\" topn_results: {}".format(index, len(mentions), elapsed.total_seconds(), total_time.total_seconds(), mention_text, expanded_text, topn_results))
        else:
            topn_results = run_query(tokenizer, model, all_reps_emb, term_id_pairs, expanded_text, topn)
            # lexicon_name = topn_results[0][0]
            # lexicon_identifier = topn_results[0][1]
            # lexicon_score = topn_results[0][2]
            query_cache[expanded_text] = topn_results
            # elapsed = datetime.datetime.now() - start
            # total_time = len(mentions) * (elapsed / (index + 1))
#             print (" {} / {}: {} / {} mention_text: \"{}\" expanded_text: \"{}\" predicted label: ({}, {}, {}) topn_results: {}".format(index, len(mentions), elapsed.total_seconds(), total_time.total_seconds(), mention_text, expanded_text, lexicon_name, lexicon_identifier, lexicon_score, topn_results))
        normalized[mention_text] = topn_results # previously: normalized[(document_id, mention_text)] = topn_results

    print("Writing output files.")
    write_tsv_output(output_dirpath, normalized)

    print("Done. Encoding and writing took", (datetime.datetime.now() - start).total_seconds(), "seconds.")
    


if __name__ == "__main__":
    if len(sys.argv) > 1:
        main(*sys.argv[1:])
    else:
        print("not using cmd args")
        # main("cell_types.tsv", '.', ".\SapBERT_config_referenceSpans2.json")
        main(input_database_path=r"C:\Users\rotenbergnh\OneDrive - National Institutes of Health\cell type NLP extraction\2025-01-23 SAPBERT for Matt\sample_cde_batch.tsv", 
             input_query_CDE_filepath=r"C:\Users\rotenbergnh\OneDrive - National Institutes of Health\cell type NLP extraction\2025-01-23 SAPBERT for Matt\sample_query_cde.txt",
             output_dirpath=r"C:\Users\rotenbergnh\OneDrive - National Institutes of Health\cell type NLP extraction\2025-01-23 SAPBERT for Matt\sample_outputdir", 
             topn = "all", abbr_freq_filename = None, abbr_paths = None)

