# sandbox/extract_mc_eval.py
print("Extracting MC eval data...")

import sys
import csv
import math
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from inspect_ai.log import read_eval_log
from humanebench.metrics.meaningful_choices import meaningful_choices_score

# Find the most recent mc-eval log
log_dir = project_root / "logs"
log_files = sorted(log_dir.glob("*mc-eval*.eval"), key=lambda f: f.stat().st_mtime, reverse=True)

if not log_files:
    # Fall back to most recent any eval
    log_files = sorted(log_dir.glob("*.eval"), key=lambda f: f.stat().st_mtime, reverse=True)

if not log_files:
    print("No .eval files found")
    exit(1)

log_path = log_files[0]
print(f"Reading: {log_path.name}")

log = read_eval_log(str(log_path))
print(f"Model: {log.eval.model}")
print(f"Samples: {len(log.samples)}")

rows = []

for sample in log.samples:
    # Extract prompt
    prompt_text = ""
    if hasattr(sample, 'input'):
        if isinstance(sample.input, str):
            prompt_text = sample.input
        elif hasattr(sample.input, 'text'):
            prompt_text = sample.input.text
    
    # Extract response
    response_text = ""
    if hasattr(sample, 'output') and sample.output:
        if hasattr(sample.output, 'completion'):
            response_text = sample.output.completion or ""
    
    # Get judge score from overseer scorer
    judge_score = None
    principle = None
    if sample.scores:
        # Prefer 'overseer' scorer for judge score
        if 'overseer' in sample.scores:
            score_obj = sample.scores['overseer']
            if score_obj.value is not None and not math.isnan(score_obj.value):
                judge_score = score_obj.value
            if hasattr(score_obj, 'answer'):
                principle = score_obj.answer
        else:
            # Fallback: take first non-MC scorer
            for score_name, score_obj in sample.scores.items():
                if score_name == 'meaningful_choices_scorer':
                    continue
                if score_obj.value is not None and not math.isnan(score_obj.value):
                    judge_score = score_obj.value
                if hasattr(score_obj, 'answer'):
                    principle = score_obj.answer
                break

    # Compute MC score (fresh computation, not from log)
    mc = meaningful_choices_score(prompt_text, response_text)
    
    rows.append({
        'sample_id': sample.id if hasattr(sample, 'id') else None,
        'principle': principle,
        'judge_score': judge_score,
        'mc_score': mc.score,
        'mc_score_raw': mc.score_raw,
        'mc_gate': mc.gate,
        'mc_option_count': mc.option_count,
        'mc_m_opt': mc.m_opt,
        'mc_m_dist': mc.m_dist,
        'mc_m_trade': mc.m_trade,
        'mc_m_ctrl': mc.m_ctrl,
        'prompt': prompt_text[:500],
        'response': response_text[:1000],
    })

# Write CSV
output_file = project_root / "tables" / "sample_mc_vs_judge.csv"
output_file.parent.mkdir(exist_ok=True)

with open(output_file, 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)

print(f"\nWrote {len(rows)} samples to {output_file}")

# Quick summary
valid = [r for r in rows if r['judge_score'] is not None]
print(f"Samples with judge scores: {len(valid)}")
if valid:
    judge_scores = [r['judge_score'] for r in valid]
    mc_scores = [r['mc_score'] for r in valid]
    print(f"Judge mean: {sum(judge_scores)/len(judge_scores):.3f}")
    print(f"MC mean: {sum(mc_scores)/len(mc_scores):.3f}")

    # Spearman correlation
    try:
        from scipy.stats import spearmanr
        correlation, p_value = spearmanr(mc_scores, judge_scores)
        print(f"Spearman correlation: {correlation:.3f} (p={p_value:.4f})")
    except ImportError:
        print("(scipy not installed - skipping correlation)")