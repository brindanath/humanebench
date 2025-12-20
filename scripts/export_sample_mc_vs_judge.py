#!/usr/bin/env python3
"""
Export per-sample Meaningful Choices metric (deterministic) alongside judge score
from HumaneBench .eval logs, for scatter/quadrant analysis.

This version scans *.eval files directly under --logs-dir (no persona/model subfolders required).
Writes: sample_mc_vs_judge.csv
"""

import argparse
import csv
import sys
from pathlib import Path
from typing import Any, Optional, Tuple

# Ensure project root import works when running as a script
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from inspect_ai.log import read_eval_log
from humanebench.metrics.meaningful_choices import meaningful_choices_score

PRINCIPLE_ID = "enable-meaningful-choices"


def _first_present(obj: Any, keys: list[str]) -> Optional[Any]:
    for k in keys:
        if hasattr(obj, k):
            v = getattr(obj, k)
            if v is not None:
                return v
    if isinstance(obj, dict):
        for k in keys:
            if k in obj and obj[k] is not None:
                return obj[k]
    return None


def _coerce_text(x: Any) -> str:
    if x is None:
        return ""
    if isinstance(x, str):
        return x
    t = _first_present(x, ["text", "content", "value"])
    if isinstance(t, str):
        return t
    return str(x)


def extract_prompt_response(sample: Any) -> Tuple[str, str]:
    # Prefer structured input/output
    prompt_text = _extract_prompt_from_input(getattr(sample, "input", None)) or ""
    response_text = _get_first_choice_content(getattr(sample, "output", None)) or ""

    # Fallback to older shapes
    if not prompt_text:
        prompt = _first_present(sample, ["prompt", "question", "user", "task", "query"])
        prompt_text = _coerce_text(prompt).strip()

    if not response_text:
        response = _first_present(sample, ["response", "completion", "answer", "assistant"])
        response_text = _coerce_text(response).strip()

    # Fallback: if sample stores messages list
    if not prompt_text or not response_text:
        msgs = _first_present(sample, ["messages"])
        if isinstance(msgs, list) and msgs:
            user_msg = ""
            asst_msg = ""
            for m in msgs:
                role = _first_present(m, ["role"])
                content = _coerce_text(_first_present(m, ["content", "text", "message"]))
                if role == "user":
                    user_msg = content
                elif role == "assistant":
                    asst_msg = content
            if not prompt_text:
                prompt_text = (user_msg or "").strip()
            if not response_text:
                response_text = (asst_msg or "").strip()

    return prompt_text, response_text


def extract_judge_score(sample: Any, principle_id: str = PRINCIPLE_ID) -> Optional[float]:
    scores = getattr(sample, "scores", None)
    if not isinstance(scores, dict) or "overseer" not in scores:
        return None

    ov = scores["overseer"]

    # In your logs, overseer is a single Score with:
    #   value: float severity
    #   answer: principle id string
    ans = getattr(ov, "answer", None)
    val = getattr(ov, "value", None)

    if ans == principle_id and isinstance(val, (int, float)):
        return float(val)

    return None


def infer_persona_from_filename(name: str) -> str:
    n = name.lower()
    if "good-persona" in n or "good_persona" in n:
        return "good_persona"
    if "bad-persona" in n or "bad_persona" in n:
        return "bad_persona"
    return "baseline"


def find_eval_files_flat(logs_dir: Path) -> list[Path]:
    return sorted(logs_dir.rglob("*.eval"))

def _get_first_choice_content(output: Any) -> Optional[str]:
    """
    Try to pull assistant message content from model output objects like:
      output.choices[0].message.content
    Handles dict-like variants too.
    """
    if output is None:
        return None

    # attr-style
    choices = _first_present(output, ["choices"])
    if isinstance(choices, list) and choices:
        c0 = choices[0]
        msg = _first_present(c0, ["message"])
        if msg is not None:
            content = _first_present(msg, ["content", "text"])
            if isinstance(content, str) and content.strip():
                return content.strip()
        # sometimes choice itself may have "text"
        txt = _first_present(c0, ["text", "content"])
        if isinstance(txt, str) and txt.strip():
            return txt.strip()

    # dict-style fallback
    if isinstance(output, dict):
        choices = output.get("choices")
        if isinstance(choices, list) and choices:
            c0 = choices[0]
            if isinstance(c0, dict):
                msg = c0.get("message", {})
                if isinstance(msg, dict):
                    content = msg.get("content") or msg.get("text")
                    if isinstance(content, str) and content.strip():
                        return content.strip()
                txt = c0.get("text") or c0.get("content")
                if isinstance(txt, str) and txt.strip():
                    return txt.strip()

    return None


def _extract_prompt_from_input(inp: Any) -> Optional[str]:
    """
    Try to pull user prompt from sample.input.
    Often it's already a string, or it's a messages-like structure.
    """
    if inp is None:
        return None
    if isinstance(inp, str) and inp.strip():
        return inp.strip()

    # common fields
    t = _first_present(inp, ["prompt", "text", "content", "value", "question", "query"])
    if isinstance(t, str) and t.strip():
        return t.strip()

    # messages-style
    msgs = _first_present(inp, ["messages"])
    if isinstance(msgs, list) and msgs:
        user_msg = ""
        for m in msgs:
            role = _first_present(m, ["role"])
            content = _coerce_text(_first_present(m, ["content", "text", "message"]))
            if role == "user":
                user_msg = content
        if user_msg.strip():
            return user_msg.strip()

    return None


def main():
    parser = argparse.ArgumentParser(description="Export per-sample MC metric vs judge score")
    parser.add_argument("--logs-dir", type=Path, default=project_root / "logs")
    parser.add_argument("--output", type=Path, default=project_root / "sample_mc_vs_judge.csv")
    parser.add_argument("--limit-per-eval", type=int, default=0, help="0 = no cap")
    args = parser.parse_args()

    logs_dir = args.logs_dir.expanduser().resolve()
    out_path = args.output.expanduser().resolve()

    if not logs_dir.exists():
        raise FileNotFoundError(f"Logs directory not found: {logs_dir}")

    eval_files = find_eval_files_flat(logs_dir)
    print(f"Found {len(eval_files)} eval files under {logs_dir}")

    fieldnames = [
        
        "persona", "model", "principle", "eval_file", "sample_idx",
        "judge_score",
        "mc_score", "mc_score_raw", "mc_gate",
        "mc_m_opt", "mc_m_dist", "mc_m_trade", "mc_m_ctrl", "mc_option_count",
        "prompt", "response",
        "overseer_principle", "overseer_value",
    ]

    rows_written = 0

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for eval_path in eval_files:
            log = read_eval_log(str(eval_path))

            model = getattr(getattr(log, "eval", None), "model", None) or "unknown_model"
            persona = infer_persona_from_filename(eval_path.name)
            

            samples = getattr(log, "samples", []) or []
            if not samples:
                continue

            n = 0
            for idx, sample in enumerate(samples):
                if args.limit_per_eval and n >= args.limit_per_eval:
                    break

                prompt, response = extract_prompt_response(sample)
                if not prompt or not response:
                    continue

                mc = meaningful_choices_score(prompt, response)

                ov = getattr(sample, "scores", {}).get("overseer", None)
                if ov is None:
                    continue
                overseer_principle = getattr(ov, "answer", None)
                overseer_value = getattr(ov, "value", None)

                # keep both: (a) always-available overseer score, (b) MC-only judge_score
                principle = overseer_principle
                judge = float(overseer_value) if (overseer_principle == PRINCIPLE_ID and isinstance(overseer_value, (int, float))) else None

                




                writer.writerow({
                    "persona": persona,
                    "model": model,
                    "principle": principle,   
                    "eval_file": str(eval_path),
                    "sample_idx": idx,
                    "judge_score": judge,
                    "mc_score": mc.score,
                    "mc_score_raw": mc.score_raw,
                    "mc_gate": mc.gate,
                    "mc_m_opt": mc.m_opt,
                    "mc_m_dist": mc.m_dist,
                    "mc_m_trade": mc.m_trade,
                    "mc_m_ctrl": mc.m_ctrl,
                    "mc_option_count": mc.option_count,
                    "prompt": prompt,
                    "response": response,
                    "overseer_principle": overseer_principle,
                    "overseer_value": overseer_value,
                })
                rows_written += 1
                n += 1

    print(f"Wrote {rows_written} rows to {out_path}")
    print("Done.")


if __name__ == "__main__":
    main()
