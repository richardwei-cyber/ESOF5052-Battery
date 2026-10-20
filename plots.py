"""Simple SOH plots for checking the cleaned data."""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def plot_soh(data, output, threshold=0.8):
    """Plot sources separately because their cycling conditions are different."""
    sources = sorted(data["dataset"].unique())
    fig, axes = plt.subplots(len(sources), 1, figsize=(9, 6), squeeze=False)
    for ax, source in zip(axes[:, 0], sources):
        for battery, group in data[data["dataset"] == source].groupby("battery"):
            ax.plot(group["cycle"], group["SOH"], label=battery, linewidth=1)
        ax.axhline(threshold, color="black", linestyle="--", label="80% threshold")
        ax.set(title=source, xlabel="Observed discharge-attempt index", ylabel="SOH")
        ax.legend(fontsize=8)
        ax.grid(alpha=0.2)
    fig.tight_layout()
    fig.savefig(output, dpi=160)
    plt.close(fig)
