# sandbox/analyze_single_log.py
print("Analyzing single eval log...")

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import math
from inspect_ai.log import read_eval_log
from humanebench.metrics.meaningful_choices import meaningful_choices_score

# Find the largest log file (most likely to have real data)
log_dir = project_root / "logs"
log_files = list(log_dir.glob("*.eval"))

if not log_files:
    print("No .eval files found in logs/")
    exit(1)

# Sort by file size, largest first
log_path = sorted(log_files, key=lambda f: f.stat().st_size, reverse=True)[0]
print(f"Reading: {log_path.name} ({log_path.stat().st_size} bytes)\n")

log = read_eval_log(str(log_path))

print(f"Model: {log.eval.model}")
print(f"Samples: {len(log.samples)}")
print("=" * 80)

for i, sample in enumerate(log.samples):
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
    
    # Get judge score
    judge_score = None
    principle = None
    if sample.scores:
        for score_name, score_obj in sample.scores.items():
            if score_obj.value is not None and not math.isnan(score_obj.value):
                judge_score = score_obj.value
            if hasattr(score_obj, 'answer'):
                principle = score_obj.answer
    
    # Compute MC score
    mc = meaningful_choices_score(prompt_text, response_text)
    
    print(f"\n{'─' * 80}")
    print(f"SAMPLE {i+1}: {principle}")
    print(f"{'─' * 80}")
    print(f"Prompt: {prompt_text[:100]}...")
    print(f"Response: {response_text[:200]}...")
    print(f"\n  Judge Score: {judge_score}")
    print(f"  MC Score:    {mc.score:.2f} (raw: {mc.score_raw:.2f}, gate: {mc.gate:.2f})")
    print(f"    m_opt:  {mc.m_opt:.2f} ({mc.option_count} options)")
    print(f"    m_dist: {mc.m_dist:.2f}")
    print(f"    m_trade: {mc.m_trade:.2f}")
    print(f"    m_ctrl: {mc.m_ctrl:.2f}")

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)

# Collect for correlation
judge_scores = []
mc_scores = []

for sample in log.samples:
    if sample.scores:
        for score_name, score_obj in sample.scores.items():
            if score_obj.value is not None and not math.isnan(score_obj.value):
                prompt_text = ""
                if hasattr(sample, 'input'):
                    if isinstance(sample.input, str):
                        prompt_text = sample.input
                    elif hasattr(sample.input, 'text'):
                        prompt_text = sample.input.text
                
                response_text = ""
                if hasattr(sample, 'output') and sample.output:
                    if hasattr(sample.output, 'completion'):
                        response_text = sample.output.completion or ""
                
                mc = meaningful_choices_score(prompt_text, response_text)
                
                judge_scores.append(score_obj.value)
                mc_scores.append(mc.score)

print(f"\nSamples with valid scores: {len(judge_scores)}")
if judge_scores:
    print(f"Judge scores range: [{min(judge_scores):.2f}, {max(judge_scores):.2f}]")
    print(f"MC scores range:    [{min(mc_scores):.2f}, {max(mc_scores):.2f}]")
    print(f"Judge mean: {sum(judge_scores)/len(judge_scores):.2f}")
    print(f"MC mean:    {sum(mc_scores)/len(mc_scores):.2f}")

    # Simple correlation
    if len(judge_scores) > 1:
        mean_j = sum(judge_scores) / len(judge_scores)
        mean_m = sum(mc_scores) / len(mc_scores)
        
        num = sum((j - mean_j) * (m - mean_m) for j, m in zip(judge_scores, mc_scores))
        den_j = sum((j - mean_j) ** 2 for j in judge_scores) ** 0.5
        den_m = sum((m - mean_m) ** 2 for m in mc_scores) ** 0.5
        
        if den_j > 0 and den_m > 0:
            corr = num / (den_j * den_m)
            print(f"\nPearson correlation (judge vs MC): {corr:.3f}")
        else:
            print("\nCannot compute correlation (no variance in one metric)")

print("\nDone.")