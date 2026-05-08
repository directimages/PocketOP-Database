# requires: requests==2.32.3
import json
import os
import sys
from datetime import date

import requests

CDN_URL = "https://cdn.jsdelivr.net/gh/directimages/PocketOP-Database@main/lenses.json"
OUTPUT_FILE = "lens-details.json"


def main():
    if os.path.exists(OUTPUT_FILE):
        print(f"ERROR: {OUTPUT_FILE} already exists. Aborting to avoid overwrite.", file=sys.stderr)
        sys.exit(1)

    response = requests.get(CDN_URL, timeout=15)
    response.raise_for_status()
    source = response.json()

    skeletons = [
        {
            "id": lens["id"],
            "manufacturerUrl": None,
            "weightG": None,
            "lengthMm": None,
            "frontDiameterMm": None,
            "closeFocusM": None,
        }
        for lens in source["lenses"]
    ]

    output = {
        "version": "1.0.0",
        "updatedAt": date.today().isoformat(),
        "lenses": skeletons,
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(f"Written {len(skeletons)} entries to {os.path.abspath(OUTPUT_FILE)}")


if __name__ == "__main__":
    main()
