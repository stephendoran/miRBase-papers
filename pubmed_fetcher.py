import os
import requests
import calendar
from bs4 import BeautifulSoup
from Bio import Entrez as en

en.email = "" # Replace with your email
en.api_key = os.getenv("NCBI_API_KEY") # Instead of this you can just put your API key, but we carefull others can see it and might use it :)

output_dir = "/Users/user/Documents/papers/output"
def get_pmcid(pmids, output_dir):
    """
    Fetches and saves XML data for articles linked to given PMIDs.

    This function takes a list of PubMed IDs (PMIDs) and for each PMID, it attempts 
    to find the corresponding PubMed Central ID (PMCID). If a PMCID is found, it 
    retrieves the XML data for the article and saves it to the specified output 
    directory with the filename format "PMC{pmcid}.xml". If no PMCID is found for 
    a PMID, a message is printed. Any exceptions encountered during the process 
    are caught and an error message is printed.

    Parameters:
    pmids (list of str): A list of PubMed IDs to be processed.
    output_dir (str): The directory where the XML files will be saved.

    """
    for pmid in pmids:
        try:
            handle = en.elink(dbfrom="pubmed", db="pmc", id=pmid)
            record = en.read(handle)
            handle.close()

            linkset = record[0]["LinkSetDb"]
            if linkset:
                pmcid = linkset[0]["Link"][0]["Id"]

                handle_pmc = en.efetch(db="pubmed", id=pmid, retmode="xml")
                xml_data = handle_pmc.read().decode("utf-8")
                handle_pmc.close()

                xml_filename = os.path.join(output_dir, f"PMC{pmcid}.xml")
                with open(xml_filename, "w", encoding="utf-8") as xml_file:
                    xml_file.write(xml_data)
            else:
                print(f"No PMCID found for PMID: {pmid}")

        except Exception as e:
            print(f"Error fetching PMCID for PMID {pmid}: {e}")

def fetch_pmc_metadata(pmcid):
    """
    Fetches metadata for a given PMC ID.

    This function retrieves metadata from the PubMed Central (PMC)
    database for a specified PMC ID. The metadata includes information
    about the article such as PMID, title, authors, journal, publication 
    date, volume, and page numbers (or e-location ID).

    Args:
        pmcid (str): The PubMed Central ID of the article.

    Returns:
        dict: A dictionary containing the article's metadata.
            - 'pmid': The PubMed ID associated with the article.
            - 'title': The title of the article.
            - 'authors': A list of authors in "Given Name Surname" format.
            - 'journal': The title of the journal where the article is published.
            - 'pub_date': The publication date in "Mon YYYY" format.
            - 'volume': The volume of the journal in which the article appears.
            - 'elocation_id' or 'pages': The e-location ID or page range of the article.
    """
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    params = {"db": "pmc", "id": pmcid, "retmode": "xml"}

    response = requests.get(url, params=params)
    soup = BeautifulSoup(response.text, "xml")

    metadata = {}

    # Journal info
    pmid_tag = soup.find("article-id", {"pub-id-type": "pmid"}).text
    metadata["pmid"] = pmid_tag if pmid_tag else None
    metadata["title"] = soup.find("article-title").text

    # Authors
    authors = []
    for contrib in soup.find_all("contrib", {"contrib-type": "author"}):
        surname = contrib.find("surname").text
        given = contrib.find("given-names").text
        if surname and given:
            authors.append(f"{given} {surname}")
    metadata["authors"] = authors

    metadata["journal"] = soup.find("journal-title").text
    year_tag = soup.find("year").text
    month_tag = soup.find("month").text
    metadata["pub_date"] = f"{calendar.month_abbr[int(month_tag)]} {year_tag}"
    metadata["volume"] = soup.find("volume").text

    # Pages (look inside front only)
    front = soup.find("front")

    eloc = front.find("elocation-id") if front else None
    fpage = front.find("fpage") if front else None
    lpage = front.find("lpage") if front else None

    if eloc:
        metadata["elocation_id"] = eloc.text.strip()
    elif fpage and lpage:
        metadata["pages"] = f"{fpage.text.strip()}-{lpage.text.strip()}"
    else:
        metadata["pages"] = None
    
    return metadata


if __name__ == "__main__":
    
    with open('mirbase_papers_v22.txt', 'r') as f:
        for i, j in enumerate(f.readlines()):
            if i == 0:
                pass
            else:
                info = j.split("\t")
                if info[0] == '19061':
                    break
                else:
                    get_pmcid([info[1]], output_dir)
