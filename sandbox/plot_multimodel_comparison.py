"""
Plot MC Metric vs Judge scores for multiple models on same scatter plot.
Each model gets a different color. Prints quadrant breakdown for each model.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import spearmanr
import argparse
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from humanebench.metrics.meaningful_choices import is_high_mc, MC_THRESHOLD


# Color palette for models
MODEL_COLORS = {
    'openai/gpt-4o': '#10a37f',           # OpenAI green
    'anthropic/claude-3.5-sonnet': '#d4a574',  # Anthropic tan
    'google/gemini-1.5-pro': '#4285f4',   # Google blue
    'meta-llama/llama-4-maverick': '#7c3aed',  # Purple
    'xai/grok-4': '#ef4444',              # Red
}

# Fallback colors if model not in palette
FALLBACK_COLORS = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
                   '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']


def get_model_color(model: str, idx: int) -> str:
    """Get color for a model."""
    for key, color in MODEL_COLORS.items():
        if key in model:
            return color
    return FALLBACK_COLORS[idx % len(FALLBACK_COLORS)]


def get_correlation_strength(rho: float) -> str:
    """Interpret correlation strength."""
    if abs(rho) >= 0.7:
        return "Strong"
    elif abs(rho) >= 0.4:
        return "Moderate"
    elif abs(rho) >= 0.2:
        return "Weak"
    return "Negligible"


def print_quadrant_table(model: str, df: pd.DataFrame, j_hi: float = 0.25, m_hi: float = None):
    """Print quadrant breakdown table for a model."""
    # Use MC_THRESHOLD with epsilon tolerance if m_hi not specified
    if m_hi is None:
        m_hi = MC_THRESHOLD

    sub = df[df['model'] == model].dropna(subset=['judge_score', 'mc_score'])
    n = len(sub)

    if n == 0:
        print(f"\n{model}: No valid samples")
        return

    judge = sub['judge_score'].values
    mc = sub['mc_score'].values

    # Use is_high_mc for epsilon-tolerant comparison
    mc_high = np.array([is_high_mc(s) for s in mc])
    mc_low = ~mc_high

    hh = np.sum((judge >= j_hi) & mc_high)
    lh = np.sum((judge >= j_hi) & mc_low)
    hl = np.sum((judge < j_hi) & mc_high)
    ll = np.sum((judge < j_hi) & mc_low)
    agreement = 100 * (hh + ll) / n

    # Spearman correlation
    rho, pval = spearmanr(mc, judge)
    strength = get_correlation_strength(rho)

    print(f"\n{'='*50}")
    print(f" {model}")
    print(f"{'='*50}")
    print(f" Spearman ρ = {rho:.3f} (p={pval:.4f}) - {strength}")
    print(f"{'='*50}")
    print(f" | Metric vs Judge          | #/{n:<3} |")
    print(f" |--------------------------|-------|")
    print(f" | HIGH metric + HIGH judge | {hh:<5} |")
    print(f" | LOW metric + HIGH judge  | {lh:<5} |")
    print(f" | HIGH metric + LOW judge  | {hl:<5} |")
    print(f" | LOW metric + LOW judge   | {ll:<5} |")
    print(f" | Agreement rate           | {agreement:.1f}% |")
    print(f"{'='*50}")

    return {'model': model, 'n': n, 'hh': hh, 'lh': lh, 'hl': hl, 'll': ll,
            'agreement': agreement, 'rho': rho}


def plot_multimodel(
    df: pd.DataFrame,
    j_hi: float = 0.25,
    m_hi: float = 0.6,
    output_path: str = None,
    add_jitter: bool = True,
    jitter_amount: float = 0.08
):
    """Create multi-model scatter plot."""

    models = df['model'].unique()
    print(f"\nPlotting {len(models)} models: {list(models)}")

    # Create figure
    fig, ax = plt.subplots(figsize=(12, 10))

    # Plot each model
    for idx, model in enumerate(sorted(models)):
        sub = df[df['model'] == model].dropna(subset=['judge_score', 'mc_score'])

        if len(sub) == 0:
            continue

        judge = sub['judge_score'].values.copy()
        mc = sub['mc_score'].values.copy()

        # Add jitter to reveal overlapping points
        if add_jitter:
            np.random.seed(42 + idx)  # Different seed per model for spread
            judge = judge + np.random.uniform(-jitter_amount, jitter_amount, len(judge))
            mc = mc + np.random.uniform(-jitter_amount * 0.7, jitter_amount * 0.7, len(mc))
            mc = np.clip(mc, 0, 1.05)
            judge = np.clip(judge, -1.05, 1.05)

        color = get_model_color(model, idx)

        # Short label for legend
        short_name = model.split('/')[-1] if '/' in model else model

        ax.scatter(judge, mc, s=50, alpha=0.7, c=color, label=short_name,
                   edgecolors='white', linewidth=0.5)

    # Quadrant threshold lines
    ax.axvline(x=j_hi, color='gray', linestyle='--', alpha=0.5, linewidth=1.5)
    ax.axhline(y=m_hi, color='gray', linestyle='--', alpha=0.5, linewidth=1.5)

    # Diagonal reference line
    ax.plot([-1, 1], [0, 1], 'gray', linestyle='--', alpha=0.3, linewidth=1)

    # Quadrant labels
    ax.text(-0.85, 0.97, "HIGH MC, LOW Judge\n(Metric too generous)",
            fontsize=9, color='orange', alpha=0.8, ha='left', va='top')
    ax.text(0.65, 0.97, "HIGH-HIGH\n(Agreement)",
            fontsize=9, color='green', alpha=0.8, ha='left', va='top')
    ax.text(-0.85, 0.15, "LOW-LOW\n(Agreement)",
            fontsize=9, color='green', alpha=0.8, ha='left', va='top')
    ax.text(0.65, 0.15, "LOW MC, HIGH Judge\n(Metric too strict)",
            fontsize=9, color='orange', alpha=0.8, ha='left', va='top')

    # Labels and title
    ax.set_xlabel("Judge Score (Overseer)", fontsize=12)
    ax.set_ylabel("MC Metric Score (v0.4.1)", fontsize=12)
    ax.set_title(f"Meaningful Choices: Multi-Model Comparison\n{len(models)} models, 100 samples each",
                 fontsize=13)

    # Axis limits
    ax.set_xlim(-1.1, 1.1)
    ax.set_ylim(-0.05, 1.1)

    # Legend
    ax.legend(loc='lower right', fontsize=9, framealpha=0.9)

    # Note about jitter
    if add_jitter:
        ax.text(0.98, 0.02, 'Points jittered to reveal overlap',
                transform=ax.transAxes, fontsize=8, ha='right', va='bottom',
                style='italic', color='gray')

    plt.tight_layout()

    if output_path:
        plt.savefig(output_path, dpi=200, bbox_inches='tight', facecolor='white')
        print(f"\nSaved plot to {output_path}")
        plt.close()
    else:
        plt.show()


def main():
    parser = argparse.ArgumentParser(description='Plot multi-model MC comparison')
    parser.add_argument('--csv', type=str, default='tables/multimodel_mc_results.csv',
                        help='Input CSV with multi-model results')
    parser.add_argument('--output', type=str, default='figures/multimodel_mc_comparison.png',
                        help='Output plot path')
    parser.add_argument('--j-hi', type=float, default=0.25,
                        help='Judge threshold for HIGH')
    parser.add_argument('--m-hi', type=float, default=0.6,
                        help='MC threshold for HIGH')
    parser.add_argument('--no-jitter', action='store_true',
                        help='Disable jittering')

    args = parser.parse_args()

    df = pd.read_csv(args.csv)
    print(f"Loaded {len(df)} rows from {args.csv}")
    print(f"Models: {df['model'].unique()}")

    # Print quadrant tables for each model
    print("\n" + "="*60)
    print(" QUADRANT BREAKDOWN BY MODEL")
    print("="*60)

    summaries = []
    for model in sorted(df['model'].unique()):
        summary = print_quadrant_table(model, df, j_hi=args.j_hi, m_hi=args.m_hi)
        if summary:
            summaries.append(summary)

    # Summary comparison table
    if summaries:
        print("\n" + "="*70)
        print(" COMPARISON SUMMARY")
        print("="*70)
        print(f" {'Model':<35} | {'n':>3} | {'Agr%':>5} | {'ρ':>6} | HH | LH | HL | LL |")
        print("-"*70)
        for s in sorted(summaries, key=lambda x: -x['agreement']):
            short = s['model'][-30:] if len(s['model']) > 30 else s['model']
            print(f" {short:<35} | {s['n']:>3} | {s['agreement']:>5.1f} | {s['rho']:>6.3f} | {s['hh']:>2} | {s['lh']:>2} | {s['hl']:>2} | {s['ll']:>2} |")
        print("="*70)

    # Create plot
    plot_multimodel(
        df,
        j_hi=args.j_hi,
        m_hi=args.m_hi,
        output_path=args.output,
        add_jitter=not args.no_jitter
    )


if __name__ == '__main__':
    main()
