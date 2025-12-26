# Deterministic Metrics for HumaneBench

## Mission Statement

These deterministic metrics exist to **operationalize humane technology principles** — transforming ethical frameworks into measurable, reproducible signals that can be tracked over time, integrated into development workflows, and used to detect drift in both AI systems and evaluation methods.

I believe that **philosophy and measurement are partners, not competitors**. Ethical frameworks define *what we should care about*. Metrics tell us *whether we're achieving it*. Neither is sufficient alone.

---

## The Problem I'm Addressing

HumaneBench evaluates AI systems against 8 humane technology principles using LLM judge panels. This approach provides rich, nuanced assessments that capture subtle ethical dimensions. However, LLM-based evaluation alone faces practical challenges:

| Challenge | Impact |
|-----------|--------|
| **Cost** | Judge panels are expensive at scale; limits evaluation frequency |
| **Speed** | Too slow for CI/CD integration; can't block deploys on ethical regression |
| **Reproducibility** | Judge models update; same response may score differently over time |
| **Drift blindness** | If judges drift, there's no stable reference to detect it |
| **Opacity** | "Score: 0.4" doesn't tell you *why* or *what to fix* |

These aren't criticisms of LLM judging — they're inherent tradeoffs of the approach. Deterministic metrics address these gaps while preserving the ethical foundations that LLM judges embody.

---

## My Approach: Validated Complementarity

I don't build metrics to *replace* LLM judges. I build metrics *validated against* LLM judges, creating a measurement system with known properties.

```
┌─────────────────────────────────────────────────────────────────┐
│                    HUMANEBENCH EVALUATION                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ┌───────────────────┐         ┌───────────────────┐           │
│   │  Ethical Framework│         │  LLM Judge Panel  │           │
│   │   (Philosophy)    │────────▶│   (Rich Signal)   │           │
│   │                   │ informs │                   │           │
│   └───────────────────┘         └─────────┬─────────┘           │
│                                           │                     │
│                                           │ validates           │
│                                           ▼                     │
│                                 ┌───────────────────┐           │
│                                 │   Deterministic   │           │
│                                 │      Metrics      │           │
│                                 │ (Stable Signal)   │           │
│                                 └───────────────────┘           │
│                                           │                     │
│                        ┌──────────────────┼──────────────────┐  │
│                        ▼                  ▼                  ▼  │
│                   ┌─────────┐      ┌─────────────┐    ┌──────┐  │
│                   │ CI/CD   │      │    Drift    │    │Debug │  │
│                   │ Gating  │      │  Detection  │    │Tools │  │
│                   └─────────┘      └─────────────┘    └──────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**The validation relationship is key**: When I report "83.8% agreement with judge panel," I'm not claiming the metric is 83.8% as good. I'm establishing *construct validity* — evidence that the metric measures what it intends to measure. The 16.2% disagreement is equally informative; it reveals where deterministic patterns diverge from holistic judgment, often surfacing genuine philosophical tensions (e.g., "Is Socratic questioning equivalent to explicit option presentation?").

---

## What Deterministic Metrics Enable

### 1. Reproducibility Across Time

A metric that scores a response 0.72 today will score the identical response 0.72 in six months. This seems obvious, but it's not true of LLM judges — model updates, prompt changes, and stochastic sampling all introduce variance.

This stability enables **longitudinal analysis**: Is Model X getting better at enabling meaningful choices? You can only answer this if your measurement instrument is stable.

### 2. Drift Detection

When deterministic metrics and LLM judges agree consistently, then suddenly diverge, something changed. The metric provides a stable reference frame to detect:

- **Model drift**: The evaluated AI changed behavior
- **Judge drift**: The evaluation criteria shifted
- **Concept drift**: The underlying principle is being interpreted differently

Without a stable anchor, drift is invisible.

### 3. Interpretable Debugging

LLM judges output a score. Deterministic metrics output a *decomposition*:

```
Meaningful Choices Score: 0.52
├── m_opt (options presented): 0.0    ← No explicit options detected
├── m_dist (distinctness): 0.0        ← N/A (no options)
├── m_trade (tradeoffs): 1.0          ✓ Tradeoff language present
├── m_ctrl (user control): 1.0        ✓ Returns decision to user
├── m_consider (Socratic): 0.7        ✓ Consideration framing
├── steering_detected: false          ✓ No directive language
└── gate: 1.0                         Decision-type prompt
```

This tells engineers *exactly* what to fix: add explicit option enumeration. That's actionable in a way "Score: 0.52" never can be.

### 4. CI/CD Integration

Deterministic metrics run in milliseconds and cost nothing. This enables:

```yaml
# In deployment pipeline
- name: Ethical Regression Check
  run: |
    score=$(humanebench-metrics evaluate --principle meaningful_choices)
    if (( $(echo "$score < 0.6" | bc -l) )); then
      echo "Meaningful Choices regression detected: $score"
      exit 1
    fi
```

LLM judges are too slow and expensive for this. Deterministic metrics make continuous ethical monitoring practical.

### 5. Capability Decomposition

Rather than "Model A is more ethical than Model B," metrics reveal *profiles*:

| Model | Options | Tradeoffs | User Control | Socratic |
|-------|---------|-----------|--------------|----------|
| GPT-4o | 0.94 | 0.87 | 0.62 | 0.31 |
| Claude-3.5 | 0.41 | 0.78 | 0.73 | 0.82 |
| Gemini-2.5 | 0.91 | 0.84 | 0.58 | 0.29 |

Claude is more Socratic; GPT-4o presents more explicit options. Neither is "better" — they're different approaches to enabling user autonomy. This nuance is lost in a single score.

---

## Relationship to Ethical Frameworks

Deterministic metrics are **implementations of ethical principles**, not replacements for them.

Consider the Meaningful Choices principle: *"AI should present users with genuine alternatives and the information needed to choose between them, rather than steering toward predetermined outcomes."*

This is a philosophical statement. It doesn't tell you:
- What counts as "genuine alternatives"?
- How do you detect "steering"?
- Is Socratic questioning equivalent to explicit enumeration?

The metric makes *operational decisions* about these questions — decisions that can be debated, refined, and versioned. The metric's design document becomes a *record of how we've chosen to interpret the principle*, subject to revision as our understanding evolves.

**This is a feature, not a bug.** Ethical principles are necessarily abstract. Metrics force us to be concrete about what we actually mean. The process of building metrics *advances* ethical thinking by surfacing edge cases and tensions that abstract principles gloss over.

---

## What Deterministic Metrics Are Not

**Not a replacement for ethical reasoning.** Metrics operationalize principles; they don't generate them. The hard work of defining what "humane technology" means remains philosophical.

**Not a replacement for LLM judges.** Judge panels catch nuance that deterministic patterns miss. A response might technically present options while being condescending in tone — judges catch this, regex doesn't.

**Not infallible.** Metrics have false positives (flagging good responses) and false negatives (missing bad ones). The agreement rate with judges quantifies this. Metrics should be used with awareness of their limitations.

**Not static.** As our understanding of humane technology evolves, metrics should too. Version numbers exist for a reason. The goal is *improving* operationalization over time, not achieving perfection.

---

## The Synthesis

I advocate for a **layered evaluation architecture**:

| Layer | Method | Frequency | Purpose |
|-------|--------|-----------|---------|
| Continuous | Deterministic Metrics | Every commit | Regression detection, fast feedback |
| Periodic | LLM Judge Panel | Weekly/Monthly | Rich assessment, metric validation |
| Strategic | Human Expert Review | Quarterly | Framework evolution, edge case analysis |

Each layer informs the others:
- Human review refines the ethical framework
- The framework guides LLM judge prompt design
- Judge disagreements surface metric blind spots
- Metric drift triggers judge re-evaluation

This is how mature measurement systems work in other domains — multiple instruments with different properties, cross-validated against each other, with known error characteristics.

---

## Current Metrics

| Metric | Principle | Status | Judge Agreement |
|--------|-----------|--------|-----------------|
| Meaningful Choices (MC) | Enable Meaningful Choices | v0.4.2 | 83.8% (Claude), 97-100% (others) |
| *Additional metrics in development* |

---

## Contributing

I welcome contributions that:
- Improve existing metric accuracy (reduce false positives/negatives)
- Add new metrics for unmeasured principles
- Provide validation data (responses with expert labels)
- Document edge cases and failure modes

I especially value contributions that **surface tensions** between deterministic measurement and ethical intuition — these tensions drive both better metrics and clearer ethical thinking.

---

## Philosophy

> "Not everything that counts can be counted, and not everything that can be counted counts." — *Attributed to Einstein*

I take this seriously. Some aspects of humane technology resist quantification, and I don't pretend otherwise. But the inverse is also true: some things that *can* be counted *should* be counted, because measurement enables accountability, improvement, and scale.

The goal isn't to reduce ethics to numbers. The goal is to build measurement instruments that help us know whether we're living up to our principles — instruments with known properties, documented limitations, and the humility to acknowledge what they can't capture.

Deterministic metrics are one such instrument. LLM judges are another. Human judgment is a third. Used together, with awareness of their respective strengths and limitations, they form a more complete picture than any alone.

---

## Project Vision

When complete, this project aims to deliver:

- A complete measurement suite covering all 8 humane technology principles
- Multi-model validation data across frontier models (GPT-4o, Claude, Gemini, Llama, and others)
- Documented agreement rates with LLM judge panels for each metric
- Component-level analysis revealing model behavioral "fingerprints"
- Real-world case studies demonstrating practical impact
- A methodology template that others could apply to different ethical frameworks

### Novel Contributions

This work explores several claims I believe are underappreciated in the eval literature:

1. **High agreement is achievable.** Deterministic metrics can reach 80-100% agreement with LLM judge panels on well-defined constructs — with documented failure modes that reveal the boundaries of each approach.

2. **Disagreement is signal, not noise.** When metrics and judges diverge, the patterns often surface genuine philosophical tensions (e.g., "Is Socratic questioning equivalent to explicit option presentation?") rather than mere measurement error.

3. **The combination unlocks new capabilities.** Neither approach alone enables drift detection, capability decomposition, and CI/CD integration. Together, they do.

4. **Behavioral fingerprints emerge.** Component-level scores create model signatures that enable behavioral taxonomy — understanding *how* models differ, not just *that* they differ.

---

## About This Work

This is independent research exploring how deterministic metrics can complement HumaneBench's LLM-based evaluation framework. The work is open source and intended to demonstrate the value of reproducible, interpretable measurement for AI ethics evaluation.

For questions or collaboration: dan@atroposhealth.com

---

*Operationalizing humane technology, one measurable signal at a time.*
