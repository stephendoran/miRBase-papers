import re, ast
import numpy as np
import difflib
from nltk.corpus import stopwords
from nltk.corpus import wordnet
from textblob import TextBlob
stops=set(stopwords.words('english'))

miR_file = open('/Users/user/Documents/mirbase_new/organisms.txt')
ors_and_abbrevs_dict = {}
abbrs = []
orgss = []

for l in miR_file:
    ors_and_abbrevs_dict[l.split("\t")[2].lower()] = {}
    ors_and_abbrevs_dict[l.split("\t")[2].lower()]['abbrev'] = l.split("\t")[1].lower()
    ors_and_abbrevs_dict[l.split("\t")[2].lower()]['tax_ID'] = l.split('\t')[5].rstrip()
    abbrs.append(l.split("\t")[1].lower())
    orgss.append(l.split("\t")[2].lower())

del(ors_and_abbrevs_dict['name'])
del abbrs[0]
del orgss[0]

#abbrs = ['dme']
#orgss = ['drosophila melanogaster']


pmid_new_paper_list = []
pmid_new_papers = open('/Users/user/Documents/papers/all_pmids.txt')
for line in pmid_new_papers:
   pmid_new_paper_list.append(line.rstrip())
pmc_ids_new_papers = np.array(pmid_new_paper_list)


ontology_terms = []

# An ontology of cell types.
cl = open('/Users/user/Documents/papers/mappings_sssom/cl.ols.sssom.tsv','r')
for line in cl:
   if line.startswith('subject_id'):
      continue
   else:
      ontology_term = line.split('\t')[4]
      if ontology_term not in ontology_terms:
         ontology_terms.append(ontology_term)


# Uberon is an integrated cross-species anatomy ontology representing a variety of entities classified according to traditional anatomical criteria such as structure, function and developmental lineage. 
uberon = open('/Users/user/Documents/papers/mappings_sssom/uberon.ols.sssom.tsv','r')
for line in uberon:
   if line.startswith('subject_id'):
      continue
   else:
      ontology_term = line.split('\t')[4]
      if ontology_term not in ontology_terms:
         ontology_terms.append(ontology_term)


# GO terms
go = open('/Users/user/Documents/papers/mappings_sssom/go.ols.sssom.tsv','r')
for line in go:
   if line.startswith('subject_id') or line.startswith('#'):
      continue
   else:
      ontology_term = line.split('\t')[4]
      if 'activity' in ontology_term:
          ontology_term = ontology_term.split('activity')[0].strip()
      if 'process' in ontology_term:
          ontology_term = ontology_term.split('process')[0].strip()
      if ontology_term not in ontology_terms:
         ontology_terms.append(ontology_term)


# A semi-automatically constructed ontology that merges in multiple disease resources to yield a coherent merged ontology.
mondo = open('/Users/user/Documents/papers/mappings_sssom/mondo.ols.sssom.tsv','r')
for line in mondo:
   if line.startswith('subject_id') or line.startswith('#'):
      continue
   else:
      ontology_term = line.split('\t')[4]
      if ontology_term not in ontology_terms:
         ontology_terms.append(ontology_term)


# The Disease Ontology has been developed as a standardized ontology for human disease with the purpose of providing the biomedical community with consistent, reusable and sustainable descriptions of human disease terms, phenotype characteristics and related medical vocabulary disease concepts.
doid = open('/Users/user/Documents/papers/mappings_sssom/doid.ols.sssom.tsv','r')
for line in doid:
   if line.startswith('subject_id') or line.startswith('#'):
      continue
   else:
      ontology_term = line.split('\t')[4]
      if ontology_term not in ontology_terms:
         ontology_terms.append(ontology_term)

ontology_dict = {}
for ter in ontology_terms:
    ontology_dict[ter] = 2


# Hgnc gene symbols      
hgnc = open("hgnc_complete_set.txt", 'r')
#hgnc = hgnc.readlines()
gene_list = []

for line in hgnc:
   gene = line.split('\t')[1]
   gene_list.append(gene)


# Drosophila gene names from Flybase
with open('/Users/user/Documents/papers/fly_gene_list.txt','r') as f:
   fly_genes = ast.literal_eval(f.read())

f = open('word_freq_dist.txt','r')

i = 1
common_words = []
for line in f:
   if i <= 46:
      word = line.split(' ')[0]
      common_words.append(word)
      i += 1
   else:
      break

for gene in fly_genes:
   if gene not in common_words:
      gene_list.append(gene)

#print(gene_list)

gene_dict = {}
for ter in gene_list:
    gene_dict[ter] = 1


#tax_f = open('/Users/user/Documents/text_mining_outputs/tax_report.txt', 'r')
tax_IDs = []
spec = []

pm_ids = []
spec_ids_file = []
spec_publ = open('/Users/user/Documents/papers/pmid2txid.txt')

for line in spec_publ:
    pm_ids.append(line.split('\t')[2].rstrip())
    spec_ids_file.append(line.split("\t")[1].rstrip())


for i in range(len(spec)):
    print (spec[i])
    if spec[i].lower() in list(ors_and_abbrevs_dict.keys()):
        ors_and_abbrevs_dict[spec[i].lower()] = tax_IDs[i]




for x in list(ors_and_abbrevs_dict.keys()):
    print("SPECIES:   " + str(x))


    species_input = ors_and_abbrevs_dict[x]['abbrev']
    species_abbrev_input = ors_and_abbrevs_dict[x]
    
    
    pmc_ids_spec = []
    for i in range(len(pm_ids)):
        if ors_and_abbrevs_dict[x]['tax_ID'] in spec_ids_file[i]:
            pmc_ids_spec.append(pm_ids[i])

    pmc_ids_spec = np.array(pmc_ids_spec)
    #print(pmc_ids_spec)

    ####getting organism abbreviations
    org_abbrev_list = []
    for line in miR_file:
        if line.startswith("ID"):
            org_abbrev_list.append(line.split("   ")[1].split('-')[0])
    org_abbrev_list = list(set(org_abbrev_list))

    del_indexes_1 = []
    for i in range(len(org_abbrev_list)):
        if org_abbrev_list[i] == species_abbrev_input:
            del_indexes_1.append(i)

    for ind in del_indexes_1:
        del org_abbrev_list[ind]

    scores = {"compared": -1, "development": 1, "differentiation":1, "differentially":1, "myogenesis":1, "knock": 1, "knockout": 1, "primer": -1, "considered": -1, "direct": 1, "bind": 2, "binding": 2, "investigat": -2, "evaluat": -2, "measur": -2, "calculat": -2, "target": 2, "express": 2, "regulat": 1, "suppress": 2, "promote": 2, "downregulat": 2, "down-regulat": 2, "upregulat": 2, "up-regulat": 2, "inhib": 2, "mutation": 1, "characteriz": -2, "characteris": -2, "disease": 2, "pathogenesis": 2, "assay": -1, "translat": 2}

    miR_terms = ['mir ', 'mir-', 'miR-', 'miR ', 'miRNA-', 'miRNA ', 'microRNA-', 'microRNA ', 'MicroRNA', 'micro RNA ', 'micro RNA-', 'micro-RNA ', 'micro-RNA-', 'mir', 'miR', 'MIR', 'MiR', 'Mir', 'bantam', 'Bantam', 'let-7', 'let7', 'Let-7', 'lin-', 'LIN-']
    
    spec_miRs = list()
    miR_terms_dict = {}
    for ter in miR_terms:
        miR_terms_dict[ter] = 1
   
    def score (sentence):
        #print(sentence)
        sentence = sentence.replace('  ',' ')
        n_plus_terms = 0
        n_minus_terms = 0
        n_words = len(sentence.split(' '))
        keywords = []
        scor  = 0
        l = list(miR_terms_dict.keys())
        gl = list(gene_dict.keys())
        otd = list(ontology_dict.keys())
        for word in sentence.split(' '):
            for s in list(scores.keys()):
                syns = [i for i in wordnet.synsets(s)]
                #print("WORD " + str(s))
                syns_list = list(set([i for sl in syns for i in sl.lemma_names()]))
                #print("SYN_LIST " + str(syns_list))
                if difflib.SequenceMatcher(None, s, word).ratio() >= 0.8 and scores[s] > 0 and word not in stops and word not in keywords:
                    n_plus_terms += scores[s]
                    keywords.append(str(word))
                    #print("DICT MATCH" + ' ' + word)
                if difflib.SequenceMatcher(None, s, word).ratio() >= 0.8 and scores[s] < 0 and word not in stops :
                    n_minus_terms += scores[s]                    

                for syn in syns_list:
                    if difflib.SequenceMatcher(None, syn, word).ratio() >= 0.8 and scores[s] > 0 and word not in stops and syn not in stops and word not in keywords:
                        n_plus_terms += scores[s]
                        keywords.append(str(word))
                        #print("SYNONYM" + ' ' + word + ' ' + syn)
                    if difflib.SequenceMatcher(None, syn, word).ratio() >= 0.8 and scores[s] < 0 and word not in stops and syn not in stops:
                        n_minus_terms+= scores[s]

            for mirna_term in l:
               if mirna_term in word and word not in keywords:
                    n_plus_terms += 1
                    keywords.append(str(word))

            for gene in gl:
               if gene==word and word not in keywords:
                    n_plus_terms += 1
                    keywords.append(str(word))

            for term in otd:
               if term in word and word not in keywords:
                    n_plus_terms += 1
                    keywords.append(str(word))
 
        if n_words <= 3:
            scor = 0
        elif n_words > 3 and n_words <= 10:
            scor = int((n_plus_terms - n_minus_terms)/n_words * 50)
        elif n_words > 10 and n_words <= 20:
            scor = int((n_plus_terms - n_minus_terms)/n_words * 75)          
        else:
            scor = int((n_plus_terms - n_minus_terms)/n_words * 100)
        vb_count = 0
        keyword_string = ''
        keywords = [x for x in keywords if 'miRDB' not in x]
        keywords = [x for x in keywords if 'miRanda' not in x]
        #print(keywords)  
        for word in keywords:
           keyword_string += word.strip() + '; ' 
        for wd, pos in TextBlob(sentence).tags:
            if pos == 'VBZ':
                vb_count += 1
        if vb_count == 0:
            scor = int (scor/2)
        return str(scor) + '\t' + keyword_string
    
    
                
    f = open('/Users/user/Documents/papers/output/sentences.txt')
    scores_out = open('/Users/user/Documents/text_mining_outputs/old_noncomm_scores/{}_scores.txt'.format(
        species_input), 'w')

    lines = []
    for line in f:
        lines.append("\t".join(line.rstrip().split("\t")[:3]))

    #print(lines)
    ###lines check
    '''
    pattern = re.compile('^[0-9]{8}[ \t]')

    for l in lines:
        if not re.match(pattern, l):
            print(l)
    '''     

    my_array = np.intersect1d(pmc_ids_new_papers, pmc_ids_spec)
    print(my_array)
    comm_indexes = np.nonzero(np.in1d(pmc_ids_new_papers, pmc_ids_spec))[0]
    print("COMM_INDEX")
    print(comm_indexes)
 
    

    def t_scored(sentence):
        terms_found_list = []
        miR_terms_found = []
        for word in sentence.split("\t")[2].split(" "):
            for s in list(scores.keys()):
                #if re.search(str(s), word, re.IGNORECASE):
                if difflib.SequenceMatcher(None, s, word).ratio() >= 0.59 and word not in terms_found_list:
                    terms_found_list.append(word + "({})".format(scores[s]))
        for word in sentence.split("\t")[2].split(" "):
            for p in list(miR_terms_dict.keys()):
                if str(p) in word and not 'mirbase' in word.lower():
                    # print (word)
                    miR_terms_found.append(word.strip())
        if len(miR_terms_found) == 0:
            #print(0)
            miR_terms_found.append('miR-' + sentence.split("\t")[1])
        #print (miR_terms_found)
        #           print (terms_found_list)

        return "; ".join(list(set(terms_found_list))) + "; ({})".format("; ".join(list(set(miR_terms_found)))) + "(1)"


    ls = []
#    print(len(comm_indexes))
#    for i in range(len(comm_indexes)):
#        print (i)
        #print(comm_indexes[i])
    for l in lines:
       pmid=l.split('\t')[0]
       if pmid in my_array:
          if len(l.split('\t')) < 2:
             continue
          else:
             try:
                ls.append(l + '\t' + str(score(l.split('\t')[2])))
             except IndexError:
                continue
        

    del_indexes_4 = []
    if species_abbrev_input != '':
        for i in range(len(ls)):
            for abss in org_abbrev_list:
                if (((abss + '-') in ls[i]) or ((abss + '_') in ls[i])) and not (
                        ((species_abbrev_input + '-') in ls[i]) or ((species_abbrev_input + '_') in ls[i])):
                    del_indexes_4.append(i)

    for ind in sorted(del_indexes_4, reverse=True):
        del ls[ind]
    
    ls_2 = [None] * len(ls)
    for i in range(len(ls)):
        ls_2[i] = ls[i].split("\t")

    mir_ls = [i.split('\t')[1] for i in ls]
    print(mir_ls)

    for i in range(len(ls)):
        print(i)
        if str(mir_ls[i]).endswith('-'):
            ls[i] = [str(ls[i]).split('\t')[1].replace('-', '', 1)]
        if str(mir_ls[i]).startswith('-'):
            ls[i] = [str(ls[i]).split('\t')[1].replace('-','', 1)[1]]
        else:
            ls_2[i][1] = ls_2[i][1].lower()
            print("3rd loop entered")
    
    for l in ls_2:
        if not l[1] == '5p' and not l[1] == '3p':
            scores_out.write("\t".join(l) + "\n")
    scores_out.close()






