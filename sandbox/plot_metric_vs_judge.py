# sandbox/plot_metric_vs_judge.py
import argparse
import pandas as pd
import matplotlib.pyplot as plt


def quadrant(j, m, j_hi=0.25, m_hi=0.6):
    if j >= j_hi and m >= m_hi:
        return "HIGH metric + HIGH judge"
    if j >= j_hi and m < m_hi:
        return "LOW metric + HIGH judge"
    if j < j_hi and m >= m_hi:
        return "HIGH metric + LOW judge"
    return "LOW metric + LOW judge"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default="sample_mc_vs_judge.csv")
    ap.add_argument("--principle", default="enable-meaningful-choices")
    ap.add_argument("--j_hi", type=float, default=0.25)
    ap.add_argument("--m_hi", type=float, default=0.6)
    ap.add_argument("--n_examples", type=int, default=5)
    ap.add_argument("--out", default="", help="Optional output png path")
    args = ap.parse_args()

    df = pd.read_csv(args.csv)

    # Filter to principle
    sub = df[df["principle"] == args.principle].copy()
    print(f"Principle: {args.principle}")
    print(f"Rows total (principle-filtered): {len(sub)}")

    if len(sub) == 0:
        print("No rows for this principle.")
        return

    # Choose judge column
    judge_col = None
    if "overseer_value" in sub.columns and sub["overseer_value"].notna().any():
        judge_col = "overseer_value"
    elif "judge_score" in sub.columns and sub["judge_score"].notna().any():
        judge_col = "judge_score"

    if judge_col is None:
        print("No judge column populated (overseer_value/judge_score).")
        return

    # Drop rows missing judge or metric
    sub = sub.dropna(subset=[judge_col, "mc_score"])
    print(f"Rows with judge+metric: {len(sub)} (judge_col={judge_col})")
    if len(sub) == 0:
        print("No rows for this principle with judge+metric after dropna.")
        return

    # Scatter (save, never show)
    plt.figure()
    plt.scatter(sub[judge_col], sub["mc_score"])
    plt.xlabel(f"{judge_col}")
    plt.ylabel("mc_score")
    plt.title(f"{args.principle}: {judge_col} vs mc_score")
    plt.tight_layout()

    out = args.out.strip() or f"judge_vs_metric_{args.principle}.png"
    plt.savefig(out, dpi=200)
    print(f"Saved plot to {out}")

    # Quadrants
    sub["quadrant"] = [
        quadrant(j, m, j_hi=args.j_hi, m_hi=args.m_hi)
        for j, m in zip(sub[judge_col], sub["mc_score"])
    ]

    print("\nQuadrant counts:")
    print(sub["quadrant"].value_counts())

    # Sample examples per quadrant
    for q in ["HIGH metric + HIGH judge", "LOW metric + HIGH judge", "HIGH metric + LOW judge", "LOW metric + LOW judge"]:
        ex = sub[sub["quadrant"] == q].head(args.n_examples)
        if len(ex) == 0:
            continue
        print("\n" + "=" * 80)
        print(q)
        print("=" * 80)
        for _, r in ex.iterrows():
            jv = float(r[judge_col])
            mv = float(r["mc_score"])
            gate = float(r["mc_gate"]) if "mc_gate" in r and pd.notna(r["mc_gate"]) else None
            print(f"\njudge={jv:.3f}  metric={mv:.3f}" + (f"  gate={gate:.2f}" if gate is not None else ""))
            print(f"eval_file={r.get('eval_file','')}")
            prompt = str(r.get("prompt", ""))
            resp = str(r.get("response", ""))
            print("PROMPT:", (prompt[:200] + "…") if len(prompt) > 200 else prompt)
            print("RESPONSE:", (resp[:200] + "…") if len(resp) > 200 else resp)


if __name__ == "__main__":
    main()
