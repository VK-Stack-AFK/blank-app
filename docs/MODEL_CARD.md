# HomeGuard synthetic model card

Version: homeguard-rf-demo-1.0 · Reference policy: homeowners-reference-2.0

## Intended use

Demonstrate homeowners application triage and evidence-led review using fictional records. The target is the reference-policy class A/B/F, not claim probability, premium, expected loss, or a real underwriting outcome. Recommendations do not bind coverage; F means recommended for rejection with human ownership of the decision.

## Data and fitting

Exactly 10,000 synthetic records, fixed scenario date 2026-09-15, seed 42. Class counts: {'A': 6500, 'B': 2500, 'F': 1000}. Synthetic names use example.com contacts and fictional addresses. Geography cycles through 50 states and DC; it does not represent exposure concentration. A cases include benign losses and protected pools; B cases cover 31 referral scenarios; F covers five families of severe reference findings. The separate 1,000-home demo portfolio uses seed 2026 and includes missing-evidence holds.

The stratified split has 8,000 training rows and 2,000 held-out rows. Median imputation and one-hot encoding fit only on training rows. The random forest uses 160 trees, unrestricted depth, minimum leaf size 2, max_features=0.75, balanced class weights, and random_state=42. Hyperparameters are also stored in metadata. No reference label, split label, or identity field enters the feature matrix.

## Measured synthetic evaluation

- Held-out agreement with synthetic reference labels: 99.90%.
- Macro F1: 0.9991.
- Confusion matrix and per-class precision/recall: `models/metadata.json` and Model Lab.

These measurements demonstrate replication of an artificial policy. They do not establish real-world accuracy, fairness, calibrated confidence, expected claims, savings, or improved STP. The test distribution follows the same generator and rule policy as training; external validity is unmeasured.

## Inputs and explanations

The model uses 43 explicit fields from the 121-question schema, including computed claims/replacement-cost and coverage/replacement-cost ratios. Names, emails, phones, street addresses, ZIP codes, state, IDs, reference labels, split labels, and verification status are excluded. Other fields remain useful for evidence, contextual review, and governance. Excluding specific fields does not eliminate proxy effects or prove nondiscrimination.

Global impurity importance is descriptive of the fitted forest and has known feature-selection biases. It is not a local causal explanation. Per-case findings are transparent reference/evidence checks, shown alongside the actual model recommendation and probabilities. Model/reference disagreement, incomplete evidence, invalid inputs, or support below the threshold holds B.

## Reproducibility and integrity

Run `python -m homeguard.model` with pinned requirements. The compressed CSV has a deterministic gzip timestamp; metadata hashes the uncompressed CSV. The model is loaded only from a fixed trusted repository path, after an artifact hash and exact scikit-learn version check. Pickle/joblib is not a format for untrusted uploads; the app provides no model-upload control. Training time metadata can vary across runs.

Model hash: `de094daeba0763a7c0a1b829d542a14dbb7938a7cfd2f55b0e05243c0197b75e`.
Dataset SHA-256 (uncompressed): `9fab6bb9376e826efee631a9a19ab0d1208de0b331e8df47ff4941090a5f27df`.
scikit-learn version: `1.8.0`.

## Future real-data model

Define a target with the underwriting team, such as a reviewed disposition or a time-bounded loss outcome. Obtain authorized, representative historical data with decision-time snapshots, review protected/proxy inputs and permissible uses, split chronologically and by property/household, evaluate against a documented baseline, calibrate if probability estimates are required, and measure errors, subgroup outcomes, referral burden, and actual business effects. Monitor drift and retain model/evidence versions with each decision. Thresholds and operational deployment need the applicable carrier, product, and jurisdiction review.
