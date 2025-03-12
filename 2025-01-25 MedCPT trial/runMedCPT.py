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

# queries_filepath = r"C:\Users\rotenbergnh\OneDrive - National Institutes of Health\cell type NLP extraction\2025-01-23 encoding CDEs (Matt)\sample_query_cde.txt"
# articles_filepath = r"C:\Users\rotenbergnh\OneDrive - National Institutes of Health\cell type NLP extraction\2025-01-23 encoding CDEs (Matt)\sample_cde_batch.tsv"
# output_dirpath = r"C:\Users\rotenbergnh\OneDrive - National Institutes of Health\cell type NLP extraction\2025-01-23 encoding CDEs (Matt)\2025-01-25 MedCPT trial\sample_outputdir"

queries_filepath = "../sample_query_cde.txt"
articles_filepath = "../sample_cde_batch.tsv"
output_dirpath = "sample_output_rd_2"
topn_for_crossEncoder = 100

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
    
    # # each article contains a list of two texts (usually a title and an abstract)
    # articles = [
    #      [
    #         "Diagnosis and Management of Central Diabetes Insipidus in Adults",
    #         "Central diabetes insipidus (CDI) is a clinical syndrome which results from loss or impaired function of vasopressinergic neurons in the hypothalamus/posterior pituitary, resulting in impaired synthesis and/or secretion of arginine vasopressin (AVP). [...]",
    #      ],
    #      [
    #         "Adipsic diabetes insipidus",
    #         "Adipsic diabetes insipidus (ADI) is a rare but devastating disorder of water balance with significant associated morbidity and mortality. Most patients develop the disease as a result of hypothalamic destruction from a variety of underlying etiologies. [...]",
    #      ],
    #      [
    #         "Nephrogenic diabetes insipidus: a comprehensive overview",
    #         "Nephrogenic diabetes insipidus (NDI) is characterized by the inability to concentrate urine that results in polyuria and polydipsia, despite having normal or elevated plasma concentrations of arginine vasopressin (AVP). [...]",
    #      ],
    # ]
    
    
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


# def main():

with open(queries_filepath, 'r') as readfp:
    queries = readfp.readlines()
    queries = [q.strip() for q in queries] ##**** I wonder whether we can make it a nested list, just like the "articles"


# with open(articles_filepath, 'r') as readfp:
with open(articles_filepath, 'r') as readfp:
    unformatted_articles = readfp.readlines()
    article_IDs = [a.split('\t')[-1].strip() for a in unformatted_articles]
    articles = [a.split('\t')[0].strip().split('.', maxsplit=1) for a in unformatted_articles]
    articles = [(a[0].strip(), a[1].strip()) for a in articles]
    for a in articles: ## all of them must have length 2, even if the 2nd string is empty
        if len(a) != 2:
            print(len(a), ":", a)
    print("formatted articles (sample):", articles[:5])

# query_embeds = q_embeds
# article_embeds = a_embeds

query_embeds = MedCPT_query_encoder(queries)
article_embeds = MedCPT_article_encoder(articles)
print("query_embeds.shape:", query_embeds.shape, ';', 'article_embeds.shape:', article_embeds.shape)
raw_initial_rankings = np.matmul(query_embeds, article_embeds.T) ##*** this might be wrong. article says E(q)^T E(d) but I think it's the opposite

for idx in range(len(queries)):
    rankings_i = np.asarray(np.argsort(raw_initial_rankings[idx, :]))[::-1]
    articles_for_crossEncoder = np.asarray(articles)[rankings_i[:topn_for_crossEncoder]]
    
    query = queries[idx]
    article_list = articles_for_crossEncoder
    # MedCPT_cross_encoder(queries[idx], )
    
    # def MedCPT_cross_encoder(query, article_list):
    
    tokenizer = AutoTokenizer.from_pretrained("ncbi/MedCPT-Cross-Encoder")
    model = AutoModelForSequenceClassification.from_pretrained("ncbi/MedCPT-Cross-Encoder")
    
    # query = "diabetes treatment"
    
    # # 6 articles to be ranked for the input query
    # articles = [
    #      "Type 1 and 2 diabetes mellitus: A review on current treatment approach and gene therapy as potential intervention. Type 1 and type 2 diabetes mellitus is a serious and lifelong condition commonly characterised by abnormally elevated blood glucose levels due to a failure in insulin production or a decrease in insulin sensitivity and function. [...]",
    #      "Diabetes mellitus and its chronic complications. Diabetes mellitus is a major cause of morbidity and mortality, and it is a major risk factor for early onset of coronary heart disease. Complications of diabetes are retinopathy, nephropathy, and peripheral neuropathy. [...]",
    #      "Diagnosis and Management of Central Diabetes Insipidus in Adults. Central diabetes insipidus (CDI) is a clinical syndrome which results from loss or impaired function of vasopressinergic neurons in the hypothalamus/posterior pituitary, resulting in impaired synthesis and/or secretion of arginine vasopressin (AVP). [...]",
    #      "Adipsic diabetes insipidus. Adipsic diabetes insipidus (ADI) is a rare but devastating disorder of water balance with significant associated morbidity and mortality. Most patients develop the disease as a result of hypothalamic destruction from a variety of underlying etiologies. [...]",
    #      "Nephrogenic diabetes insipidus: a comprehensive overview. Nephrogenic diabetes insipidus (NDI) is characterized by the inability to concentrate urine that results in polyuria and polydipsia, despite having normal or elevated plasma concentrations of arginine vasopressin (AVP). [...]",
    #      "Impact of Salt Intake on the Pathogenesis and Treatment of Hypertension. Excessive dietary salt (sodium chloride) intake is associated with an increased risk for hypertension, which in turn is especially a major risk factor for stroke and other cardiovascular pathologies, but also kidney diseases. Besides, high salt intake or preference for salty food is discussed to be positive associated with stomach cancer, and according to recent studies probably also obesity risk. [...]"
    # ]
    
    # combine query article into pairs
    ### *** for some reason, now articles must be a single string, not a list...
    pairs = [[query, article[0] + '. ' + article[1]] for article in article_list]
    print("sample pairs:", pairs[:2])
    
    with torch.no_grad():
        encoded = tokenizer(
            pairs,
            truncation=True,
            padding=True,
            return_tensors="pt",
            max_length=512,
        )
        
        logits = model(**encoded).logits.squeeze(dim=1)
        
        print(logits)
    
    # def write_tsv_output(output_dirpath, normalized_mentions_dict):
    with open(os.path.join(output_dirpath, f"output_{idx}-{query[:10]}.tsv"), 'w') as writefp:
        writefp.write("Input query CDE: " + query + '\n')
        writefp.write("MedCPT re-ranker (i.e.,CrossEncoder-sorted) top CDEs:\n")
        for logit_idx in np.asarray(np.argsort(logits))[::-1]:
            # write: identifier, re-ranker score (logit), database_mention
            writefp.write('\t'.join([str(article_IDs[rankings_i[logit_idx]]), str(logits[logit_idx]), str(articles_for_crossEncoder[logit_idx])]) + '\n')
        
        writefp.write("\nThe rest of the CDEs, ranked by MedCPT retriever only:\n")
        for ranking_idx in rankings_i[topn_for_crossEncoder:]:
            # write: identifier, retriever score, database_mention
            writefp.write('\t'.join([str(article_IDs[ranking_idx]), str(raw_initial_rankings[idx, ranking_idx]), str(articles[ranking_idx])]) + '\n')


