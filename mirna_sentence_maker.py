import os, re
import pandas as pd
import requests
import argparse
from bs4 import BeautifulSoup
from nltk.tokenize.punkt import PunktSentenceTokenizer, PunktParameters

mir_terms = [
    "mir-", "miR-", "miRNA-", "bantam", "Bantam", "let-7", "let7", "Let-7", "lin-", "LIN-"
]

# Flexible miRNA regex pattern
MIRNA_PATTERNS = [
    rf"\b{re.escape(term)}[A-Za-z0-9\-]+(?:-[35]p)?\b" for term in mir_terms
] + [
    r"\bbantam\b", r"\blet-7[a-z]?\b", r"\blin-\d+\b"
]
COMPILED_PATTERNS = [re.compile(p, re.IGNORECASE) for p in MIRNA_PATTERNS]


def expand_grouped_mirna(text):
    expanded = set()

    # Normalize casing
    text = re.sub(r"\b[Mm][Ii][Rr]\b", "miR", text)

    # Pattern: miR-17/20a/106b/93
    pattern1 = r"\bmiR-((?:\d+[a-z]?)(?:/\d+[a-z]?)+)"
    matches = re.findall(pattern1, text)
    for match in matches:
        parts = match.split("/")
        for p in parts:
            expanded.add(f"miR-{p}")

    # Pattern: miR-20a/b/c/d
    pattern2 = r"\b(miR-\d+)([a-z](?:/[a-z]){1,})\b"
    matches2 = re.findall(pattern2, text)
    for base, suffixes in matches2:
        for suffix in suffixes.split("/"):
            expanded.add(f"{base}{suffix}")

    # Pattern: gga-miR-16, -30e, -30d, ..., -29a
    pattern3 = (
        r"\b([\w\-]*miR-\d+[a-z]?)\b((?:,\s*-?\d+[a-z]?)*(?:,\s*and\s*-?\d+[a-z]?)?)"
    )
    matches3 = re.findall(pattern3, text)
    for base, suffix_str in matches3:
        base_prefix = re.match(r"^(.*miR-)", base).group(1)
        expanded.add(base)  # <-- Add the base miRNA
        suffixes = re.findall(r"-\d+[a-z]?", suffix_str)
        for suffix in suffixes:
            expanded.add(f"{base_prefix}{suffix[1:]}")  # strip dash

    return list(expanded)

def get_sentence_tokenizer():
    punkt_param = PunktParameters()
    abbrevs = ['al', 'fig', 'e.g', 'i.e', 'et'] + [chr(i) for i in range(ord('a'), ord('z')+1)]
    punkt_param.abbrev_types = set(abbrevs)
    return PunktSentenceTokenizer(punkt_param)

def extract_text_from_xml(xml_path):
    with open(xml_path, 'r') as file:
        soup = BeautifulSoup(file.read(), 'lxml-xml')
    text_blocks = []
    for sec in soup.find_all('sec'):
        title = sec.find('title')
        if title:
            text_blocks.append(title.text.strip() + '.')
        for p in sec.find_all('p'):
            text_blocks.append(p.text.strip())
    return ' '.join(text_blocks), soup

def extract_mirna_sentences(text, tokenizer):
    # text = re.sub(r'([a-zA-Z0-9,;\)])([A-Z][a-z])', r'\1. \2', text)
    text = re.sub(r"\b[Mm][Ii][Rr]\b", "miR", text)
    sentences = tokenizer.tokenize(text)
    results = set()
    for sent in sentences:
        found_mirnas = set()
        for pattern in COMPILED_PATTERNS:
            matches = pattern.findall(sent)
            for match in matches:
                found_mirnas.add(match.replace(" ", ""))
        for expanded in expand_grouped_mirna(sent):
            found_mirnas.add(expanded)
        for mirna in found_mirnas:
            results.add((mirna, sent.strip()))
    return list(results)

def extract_pubmed_id(file):
    pmcid = file.split(".xml")[0]
    pmid_df = pd.read_csv("pmid_info.tsv", sep="\t")
    return pmid_df["PMID"][pmid_df["PMCID"] == pmcid].values[0]

def process_directory(xml_dir, output_dir):
    sentence_file = os.path.join(output_dir, "sentences.txt")
    paper_file = os.path.join(output_dir, "Papers.txt")
    os.makedirs(output_dir, exist_ok=True)
    tokenizer = get_sentence_tokenizer()
    with open('log.txt', 'w') as log_file:
        with open(sentence_file, 'w') as sent_out, open(paper_file, 'w') as paper_out, open('pmid_not_found.txt', 'w') as not_pmid:
            for root, _, files in os.walk(xml_dir):
                for idx, file in enumerate(files, 1):
                    if not file.endswith('.xml'):
                        continue
                    xml_path = os.path.join(root, file)
                    try:
                        text, soup = extract_text_from_xml(xml_path)
                        pmid = extract_pubmed_id(file)
                        if pmid == "NotFound":
                            print(f"No PubMed ID in {file}")
                            not_pmid.write(f"{file}\n")
                            continue
                        mirna_sents = extract_mirna_sentences(text, tokenizer)
                        for mirna, sentence in mirna_sents:
                            sent_out.write(f"{pmid}\t{mirna}\t{sentence}\n")
                        total_files = len(files)
                        rem_files = total_files - idx
                        log_file.write(f"[{idx}/{total_files}] Processed {file}, {rem_files} remaining\n")
                        paper_out.write(f"{xml_path}\n")
                    except Exception as e:
                        print(f"Error processing {file}: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract miRNA-related sentences from XML files with grouped miRNA support")
    parser.add_argument("-i", "--input_dir", required=True, help="Directory containing .xml files")
    parser.add_argument("-o", "--output_dir", required=True, help="Output folder path for sentences.txt and Papers.txt")
    args = parser.parse_args()

    process_directory(args.input_dir, args.output_dir)
