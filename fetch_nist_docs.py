import os
import argparse
import requests


def _download(url: str, output_path: str) -> None:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    headers = {
        "User-Agent": "Holokia-RAG (contact: local-dev)",
        "Accept": "application/pdf",
    }
    with requests.get(url, headers=headers, stream=True, timeout=120) as r:
        r.raise_for_status()
        with open(output_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 256):
                if chunk:
                    f.write(chunk)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-dir", default=os.path.join("data", "raw", "Cybersecurity", "en"))
    args = parser.parse_args()

    csf_20_url = "https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=957258"
    sp_1308_url = "https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.1308.pdf"

    csf_20_out = os.path.join(args.base_dir, "2024", "NIST_CSF_2.0_CSWP_29.pdf")
    sp_1308_out = os.path.join(args.base_dir, "2026", "NIST_SP_1308_CSF2.0_QSG.pdf")

    print(f"Download: {csf_20_url}")
    _download(csf_20_url, csf_20_out)
    print(f"Saved: {csf_20_out}")

    print(f"Download: {sp_1308_url}")
    _download(sp_1308_url, sp_1308_out)
    print(f"Saved: {sp_1308_out}")


if __name__ == "__main__":
    main()

