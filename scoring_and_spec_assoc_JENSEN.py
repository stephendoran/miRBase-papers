from rpy2.robjects.packages import importr
import rpy2.robjects as robjects
import re
import numpy as np
import difflib
from nltk.corpus import stopwords
from nltk.corpus import wordnet
from textblob import TextBlob
import os


rentrez = importr('rentrez')
entrez_link = robjects.r('entrez_link')
sentences_file = open('/Users/user/Documents/papers/output/sentences.txt')
miR_file = open('/Users/user/Documents/mirbase_new/organisms.txt')
ors_and_abbrevs_dict = {}
tax_IDs = []
lines = [l.strip() for l in sentences_file]

tax_ids= []
orgs = []

for l in miR_file:
    orgs.append(l.split("\t")[1].lower())
    tax_ids.append(l.split('\t')[5].rstrip())

#print(tax_ids)


org2pmid = open('/Users/user/Documents/papers/organism_textmining_mentions.tsv')

with open('/Users/user/Documents/papers/pmid2txid.txt','w') as f:
   for l in org2pmid:
         l.strip()
         tax_id = l.split('\t')[0]
         if tax_id in tax_ids:
            print(tax_id)
            index = tax_ids.index(tax_id)
            org = orgs[index]
            print(org)
            i=1
            lst = l.split(' ')
            lst_len = len(lst)
            for item in l.split(' '):
              if i==1:
                 f.write(org + '\t' + item + '\n')
                 i+=1
              elif i==lst_len:
                 f.write(org + '\t' + tax_id + '\t' + item)
              else:
                 f.write(org + '\t' + tax_id + '\t' + item + '\n')
                 i+=1
         else:
            continue

f.close()
