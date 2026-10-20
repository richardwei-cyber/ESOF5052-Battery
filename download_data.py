"""Download the three original public archives used by this Stage 2 example."""

from pathlib import Path
from urllib.request import urlretrieve

ROOT = Path(__file__).resolve().parent
URLS = {
    "nasa.zip": "https://phm-datasets.s3.amazonaws.com/NASA/5.%20Battery%20Data%20Set.zip",
    "CS2_35.zip": "https://web.calce.umd.edu/batteries/data/CS2_35.zip",
    "CS2_36.zip": "https://web.calce.umd.edu/batteries/data/CS2_36.zip",
}


def main():
    """Keep raw archives unchanged; download once and reuse locally."""
    folder = ROOT / "data"
    folder.mkdir(exist_ok=True)
    for name, url in URLS.items():
        target = folder / name
        if not target.exists():
            print("Downloading", name)
            temporary = target.with_suffix(".part")
            urlretrieve(url, temporary)
            temporary.replace(target)
        print("Ready:", name)


if __name__ == "__main__":
    main()
