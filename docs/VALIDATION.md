# Validation record

Validated September 15, 2026 with Python 3.12.14, Streamlit 1.63.0, pandas 2.2.3, NumPy 2.3.5, scikit-learn 1.8.0, joblib 1.5.3, Plotly 7.0.0, and pytest 9.1.1.

## Automated checks

Command: `python -m pytest -q`

**Result: 114 passed in 19.17 seconds.**

The suite verifies:

- Every one of the 68 required fields prevents STP when absent, plus invalid formats, non-finite numbers, ranges, dates, and claims-ratio boundaries.
- Recomputed claims/replacement-cost ratios, independent rule overrides, complete evidence references, model disagreement/low-support holds, and safe model-unavailable routing.
- Exactly 10,000 unique synthetic applications, 8,000/2,000 split, checksums, deterministic generation, all states/DC, identity/label feature exclusion, and recomputed held-out metrics matching the committed metadata.
- Unique submission IDs, ZIP preservation, durable settings/decisions/history, concurrent submission writes, optimistic case revisions, and rejection of stale edits/decisions.
- Source filtering, UTC date filtering, duplicate-ID overlays, empty-source recovery, and distinct automated versus staff-cleared STP metrics.
- All seven Streamlit pages render without exceptions under AppTest.
- A complete form workflow across multiple tabs, draft navigation, submission, B evidence review, reassessment to A, metric updates, a staff disposition, and persistence in a new simulated browser session.
- Default staff access guard and prevention of public non-demo intake establishing staff verification.

The multipage tests use AppTest's explicit `switch_page(...).run()` API after checking the in-app navigation action. AppTest retains its own next-run page selection rather than tracking the browser's navigation state. Test databases are isolated and do not alter the application's default settings or bundled data.

## Model and sample verification

The fitted random forest has **99.90% agreement** with synthetic reference labels on the held-out 2,000 rows; macro F1 is **0.9991**. These are synthetic-policy replication metrics, not real underwriting, pricing, loss, fairness, or STP validation. The complete confusion matrix and per-class results are in `models/metadata.json` and Model Lab.

The independent 1,000-row demo portfolio initially routes 586 A, 322 B, and 92 F at the default threshold. Its class mix is synthetic. The missing-hazard-evidence example has model A support and remains B until the reference and verified status are recorded; then it routes A at the default threshold.

## Visual verification limitation

The local Streamlit server started successfully. The Browser service blocked the local preview URL with `net::ERR_BLOCKED_BY_CLIENT`. No alternative browser control or public deployment was used to work around that restriction. Therefore, desktop screenshots and mobile visual inspection are not verified in this environment. Layout, navigation, theme configuration, and page elements were checked through source inspection and Streamlit's app-testing runtime.

## Delivery and remote state

GitHub allowed repository reads but rejected remote branch creation with HTTP 403 (`Resource not accessible by integration`). The requested changes are committed on the local upgrade branch and preserved in the delivery Git bundle. The original remote branch was not changed. The backup branch points to the exact original commit, and the archive includes a before-change source snapshot.

The delivery bundle is verified with Git, and restoring it to a separate local checkout is checked against the upgrade and baseline commit IDs before packaging. Runtime application databases remain separate from source rollback.
