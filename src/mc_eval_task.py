import sys
from pathlib import Path

# Add project root so `import humanebench` works under `inspect eval`
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from inspect_ai import Task, task
from inspect_ai.dataset import json_dataset, FieldSpec
from inspect_ai.solver import generate
from humanebench.scorer import overseer
from humanebench.metrics.meaningful_choices import meaningful_choices_scorer

@task
def mc_eval():
    return Task(
        dataset=json_dataset(
            "../data/humane_bench_mc_200.jsonl",
            sample_fields=FieldSpec(
                input="input",
                target="target",
                id="id",
                metadata=["metadata"]
            )
        ),
        solver=[generate()],
        scorer=[
            overseer(
                humane_patterns=["enable-meaningful-choices"],
                model=[
                    "openrouter/anthropic/claude-4.5-sonnet",
                    "openrouter/openai/gpt-5.1",
                    "openrouter/google/gemini-2.5-pro",
                ],
                temperature=0.0,
                score_attempts=3
            ),
            meaningful_choices_scorer(),
        ]
    )
