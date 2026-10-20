from pathlib import Path
import pandas as pd
from load_data import load_nasa, load_calce
from preprocessing import clean_data, add_rul
from plots import plot_soh

ROOT = Path(__file__).resolve().parent


def main():
    """Run the small preprocessing workflow; no model is trained at Stage 2."""
    data_dir = ROOT / "data"
    output = ROOT / "results"
    output.mkdir(exist_ok=True)
    for name in ["nasa.zip", "CS2_35.zip", "CS2_36.zip"]:
        if not (data_dir / name).exists():
            raise FileNotFoundError(
                f"Missing {name}. Run python download_data.py first."
            )
    nasa = load_nasa(data_dir / "nasa.zip")
    calce35 = load_calce(data_dir / "CS2_35.zip", "CS2_35")
    calce36 = load_calce(data_dir / "CS2_36.zip", "CS2_36")
    raw = pd.concat([nasa, calce35, calce36], ignore_index=True)
    clean, removed, summary = clean_data(raw)
    labeled, endpoints = add_rul(clean, threshold=0.8)
    labeled.to_csv(output / "cleaned_data.csv", index=False)
    removed.to_csv(output / "removed_rows.csv", index=False)
    summary.to_csv(output / "cleaning_summary.csv", index=False)
    endpoints.to_csv(output / "eol_summary.csv", index=False)
    plot_soh(labeled, output / "soh.png")
    print("\nCleaning summary:")
    print(summary.to_string(index=False))
    print("\nEOL summary:")
    print(endpoints.to_string(index=False))
    print(f"\nSaved {len(labeled)} cleaned observations in results/.")


if __name__ == "__main__":
    main()
