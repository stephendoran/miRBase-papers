import os
from pathlib import Path
os.environ.setdefault('DJANGO_SETTINGS_MODULE','mirbase_new.settings')
import django
django.setup()
import codecs

from mirbase_app.models import Hairpin, Paper, Sentence, Hairpin2Paper, Hairpin2Sentence

#max_sentence_id = Sentence.objects.all().order_by("-id").values_list("id",flat="true")[0]
#max_h2s_id = Hairpin2Sentence.objects.all().order_by("-id").values_list("id",flat="true")[0]
max_sentence_id=0
max_h2s_id=0
max_h2p_id = Hairpin2Paper.objects.all().order_by("-id").values_list("id",flat="true")[0]

#print(max_sentence_id)
next_sentence_id=max_sentence_id+1
next_h2s_id = max_h2s_id+1
next_h2p_id= max_h2p_id+1

scores_dir = Path('/Users/user/Documents/text_mining_outputs/old_noncomm_scores/')
files = scores_dir.iterdir()
sentence_list=[]

for file in files:
   print(file)
   file_str=str(file)
   org=file_str.split('/')[6:]
   org=org[0].split('_')[0]
   print(org)
   with codecs.open(file,'r',encoding='utf-8', errors='replace') as file_handle:
      for line in file_handle:
         pmid = line.split('\t')[0].strip()
         hairpin = line.split('\t')[1].strip()
         hairpin = org + '-' + hairpin
         print(hairpin)
         if hairpin.endswith('-3p'):
            hairpin=hairpin[:-3]
         if hairpin.endswith('-5p'):
            hairpin=hairpin[:-3]
         if hairpin.endswith('-'):
            hairpin=hairpin[:-1]
         sentence = line.split('\t')[2].strip()
         sentence = ''.join(sentence)
         print(sentence)
         if sentence.startswith('"') and sentence.endswith('"'):
            sentence = sentence[1:-1]
         score = line.split('\t')[3].strip()
         print(score)
         try:
            paper=Paper.objects.get(pubmed_id=pmid)
         except:
            continue
         try:
            hairpin=Hairpin.objects.get(name=hairpin)
         except:
            continue
         if score != 0:
            terms = line.split('\t')[4].strip()
            try:
                Sentence.objects.get(text=sentence)
            #if sentence not in sentence_list:  
            except:             
               Sentence.objects.create(id=next_sentence_id, text=sentence, score=score, terms=terms, paper=paper, upvotes=0, downvotes=0)
               next_sentence_id += 1 
               #sentence_list.append(sentence)
            sentence=Sentence.objects.get(text=sentence)                
            Hairpin2Sentence.objects.create(id=next_h2s_id, match='', hairpin=hairpin, paper=paper, sentence=sentence)
            Hairpin2Paper.objects.create(id=next_h2p_id, is_reference=0, paper_score=0, hairpin=hairpin, paper=paper)
            next_h2s_id += 1
            next_h2p_id += 1
            print(next_sentence_id)

   os.rename(file, "/Users/user/Documents/text_mining_outputs/old_noncomm_papers_added/" + org + ".txt")

# Update Hairpin2Paper tables with new paper scores for each hairpin
for i in Hairpin2Paper.objects.values_list('id', flat =True):
    entry_to_update = Hairpin2Paper.objects.get(pk=i)
    hp_id = Hairpin2Paper.objects.filter(id=i).values_list('hairpin_id', flat=True)[0]
    p_id = Hairpin2Paper.objects.filter(id=i).values_list('paper_id', flat=True)[0]
    score = 0
    for sentence_id in Hairpin2Sentence.objects.filter(paper_id=p_id, hairpin_id=hp_id).values_list('sentence_id',flat=True):
        if Sentence.objects.filter(id=sentence_id).values_list('score', flat=True)[0] > 0:
            score += Sentence.objects.filter(id=sentence_id).values_list('score', flat=True)[0]
    if score > 0:
        print(hp_id, p_id,score)
    entry_to_update.paper_score = score
    entry_to_update.save()


