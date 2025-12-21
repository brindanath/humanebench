# Meaningful Choices Metric Changelog

## v0.4.1 (2025-12-20)
- Added context-aware steering detection
  - Steering only penalizes when autonomy support is weak (m_ctrl=0, minimal tradeoffs)
  - Three-tier multipliers: 1.0 (no steering), 0.85 (mitigated), 0.65 (unmitigated)
- Added refusal detection (caps score at 0.0)
- New output fields: score_pre_steering, steering_multiplier, steering_detected
- Agreement with judge panel: 83.8% (up from 75.8%)

## v0.4.0 (2025-12-20)
- Added steering.py module for detecting directive language
- Integrated Inspect AI scorer (meaningful_choices_scorer)
- Initial steering penalty implementation

## v0.3 (2025-12-19)
- Added micro-choice extraction for non-listed alternatives
- Added procedure list detection to avoid false positives
- Improved option distinctness scoring

## v0.2 (2025-12-18)
- Added user control detection (m_ctrl)
- Added tradeoff marker detection (m_trade)
- Added choices-needed gate based on prompt analysis

## v0.1 (2025-12-17)
- Initial implementation with option extraction and distinctness scoring
