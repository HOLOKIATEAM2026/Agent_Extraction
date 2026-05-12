"""
edgar_downloader.py
Télécharge N rapports 10-K depuis SEC EDGAR
Usage : python edgar_downloader.py --count 20 --output ./rapports
"""
#SEC EDGAR full-text search Rapports 10-K 2023
#https://efts.sec.gov/LATEST/search-index?q=%2210-K%22&dateRange=custom&startdt=2023-01-01&enddt=2024-01-01&forms=10-K

import requests
import os
import time
import argparse
import json

# EDGAR exige un User-Agent identifié (obligatoire sinon blocage)
HEADERS = {
    "User-Agent": "MonProjetRAG contact@monprojet.com",
    "Accept-Encoding": "gzip, deflate"
}

BASE_URL = "https://efts.sec.gov/LATEST/search-index"
SUBMISSIONS_URL = "https://data.sec.gov/submissions"


def search_10k_filings(count=20, year=2023):
    """Cherche les dépôts 10-K pour une année donnée."""
    params = {
        "q": '"10-K"',
        "dateRange": "custom",
        "startdt": f"{year}-01-01",
        "enddt": f"{year}-12-31",
        "forms": "10-K",
        "_source": "file_date,entity_name,file_num,period_of_report",
        "from": 0,
        "size": count
    }
    
    url = "https://efts.sec.gov/LATEST/search-index"
    resp = requests.get(url, params=params, headers=HEADERS)
    resp.raise_for_status()
    return resp.json()


def get_filing_document_url(accession_number, cik):
    """Récupère l'URL du document principal d'un dépôt."""
    # Formater l'accession number (enlever les tirets)
    acc_clean = accession_number.replace("-", "")
    cik_padded = str(cik).zfill(10)
    
    index_url = (
        f"https://www.sec.gov/Archives/edgar/data/"
        f"{cik}/{acc_clean}/{accession_number}-index.htm"
    )
    return index_url


def download_10k_texts(count=20, output_dir="./rapports_edgar", year=2023):
    """Pipeline complet : recherche + téléchargement des 10-K en texte."""
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Recherche de {count} rapports 10-K ({year})...")
    
    # 1. Chercher via l'API full-text search
    search_url = "https://efts.sec.gov/LATEST/search-index"
    params = {
        "q": '"10-K"',
        "forms": "10-K",
        "dateRange": "custom",
        "startdt": f"{year}-01-01",
        "enddt": f"{year+1}-01-01",
        "from": 0,
        "size": count
    }
    
    resp = requests.get(search_url, params=params, headers=HEADERS)
    data = resp.json()
    hits = data.get("hits", {}).get("hits", [])
    
    print(f"{len(hits)} résultats trouvés.")
    downloaded = 0
    
    for i, hit in enumerate(hits):
        source = hit.get("_source", {})
        entity = source.get("entity_name", f"company_{i}")
        accession = source.get("adsh", "") or source.get("accession_no", "")
        
        file_nums = source.get("file_num", [])
        if isinstance(file_nums, list) and len(file_nums) > 0:
            cik = str(file_nums[0]).replace("0001-", "")
        else:
            cik = str(file_nums).replace("0001-", "")
            
        ciks = source.get("ciks", [])
        if isinstance(ciks, list) and len(ciks) > 0:
            actual_cik = str(ciks[0])
        else:
            actual_cik = cik
        
        # Nettoyer le nom pour le nom de fichier
        safe_name = "".join(c for c in entity if c.isalnum() or c in " _-")
        safe_name = safe_name.strip().replace(" ", "_")[:50]
        
        # URL du fichier texte brut (format .txt disponible pour tous les 10-K)
        acc_nodash = accession.replace("-", "")
        txt_url = (
            f"https://www.sec.gov/Archives/edgar/data/"
            f"{acc_nodash[:10].lstrip('0')}/{acc_nodash}/{accession}.txt"
        )
        
        output_path = os.path.join(output_dir, f"{safe_name}_{year}.txt")
        
        try:
            print(f"[{i+1}/{len(hits)}] Téléchargement : {entity}...")
            r = requests.get(txt_url, headers=HEADERS, timeout=30)
            
            if r.status_code == 200:
                with open(output_path, "w", encoding="utf-8", errors="ignore") as f:
                    f.write(r.text)
                print(f"  ✓ Sauvegardé : {output_path} ({len(r.text)//1000} Ko)")
                downloaded += 1
            else:
                print(f"  ✗ Erreur {r.status_code} pour {entity}")
        
        except Exception as e:
            print(f"  ✗ Exception : {e}")
        
        # Pause obligatoire — SEC limite à 10 requêtes/seconde
        time.sleep(0.15)
    
    print(f"\nTerminé. {downloaded}/{len(hits)} rapports téléchargés dans {output_dir}/")
    return downloaded


def download_via_company_facts(tickers, output_dir="./rapports_edgar"):
    """
    Alternative : télécharger les données structurées (JSON) 
    directement depuis l'API company facts — déjà parsées, 
    pas besoin de RAG pour les KPIs financiers standards.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Mapping ticker -> CIK (quelques exemples)
    ticker_to_cik = {
        "AAPL": "0000320193",
        "MSFT": "0000789019", 
        "GOOGL": "0001652044",
        "AMZN": "0001018724",
        "META": "0001326801",
        "TSLA": "0001318605",
        "JPM":  "0000019617",
        "JNJ":  "0000200406",
    }
    
    for ticker in tickers:
        cik = ticker_to_cik.get(ticker.upper())
        if not cik:
            print(f"CIK non trouvé pour {ticker}")
            continue
        
        url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
        print(f"Téléchargement company facts : {ticker}...")
        
        try:
            r = requests.get(url, headers=HEADERS, timeout=30)
            data = r.json()
            
            # Extraire quelques KPIs clés
            facts = data.get("facts", {}).get("us-gaap", {})
            
            summary = {
                "ticker": ticker,
                "cik": cik,
                "entity": data.get("entityName", ""),
                "revenus": facts.get("Revenues", {}).get("units", {}).get("USD", [])[-3:] if "Revenues" in facts else None,
                "net_income": facts.get("NetIncomeLoss", {}).get("units", {}).get("USD", [])[-3:] if "NetIncomeLoss" in facts else None,
                "employees": facts.get("EntityNumberOfEmployees", {}).get("units", {}).get("pure", [])[-3:] if "EntityNumberOfEmployees" in facts else None,
            }
            
            out_path = os.path.join(output_dir, f"{ticker}_facts.json")
            with open(out_path, "w") as f:
                json.dump(summary, f, indent=2)
            
            print(f"  ✓ {out_path}")
            time.sleep(0.15)
        
        except Exception as e:
            print(f"  ✗ {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Téléchargeur EDGAR 10-K")
    parser.add_argument("--count", type=int, default=20, help="Nombre de rapports")
    parser.add_argument("--year", type=int, default=2023, help="Année")
    parser.add_argument("--output", type=str, default="./rapports_edgar")
    parser.add_argument("--mode", choices=["text", "facts"], default="text",
                        help="text=PDF/TXT brut | facts=JSON structuré")
    parser.add_argument("--tickers", nargs="+", default=["AAPL", "MSFT", "GOOGL", "AMZN"],
                        help="Tickers pour le mode facts")
    args = parser.parse_args()
    
    if args.mode == "text":
        download_10k_texts(args.count, args.output, args.year)
    else:
        download_via_company_facts(args.tickers, args.output)