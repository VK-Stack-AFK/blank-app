# HomeGuard · Homeowners underwriting

A Streamlit proof of concept for personal homeowners underwriting: detailed intake, a synthetic prediction model, evidence-led B-case review, and durable staff decisions. **F means recommended for rejection.** Nothing in this application quotes, binds, issues, or automatically denies coverage.

The upgrade adds 121 questionnaire fields across five sections, a plum/teal workbench, dated industry context, a full user guide, and a real fitted random forest trained on 10,000 fictional applications. The design uses original HomeGuard styling; it is not affiliated with or endorsed by another insurer.

## Run locally

Use Python 3.12. The committed model is tied to the pinned scikit-learn version.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run streamlit_app.py
```

On Windows, activate with `.venv\Scripts\activate`. Open the local URL printed by Streamlit. Codespaces/devcontainers install the same dependencies and start the same entry point.

Demo staff login: `admin` / `admin123`. For a private demonstration, set `HOMEGUARD_USERNAME` and `HOMEGUARD_PASSWORD` in the environment before starting. This shared POC login is not production identity or role management. Use synthetic examples in shared demonstrations.

## Try the complete workflow

1. Open **New application → Start from a synthetic example → B · missing evidence**.
2. Review the five sections and **Analyze & submit application**.
3. Open the workbench and sign in. The record should be B because its hazard evidence is incomplete.
4. Under **Update evidence & reassess → Evidence & consent**, change the synthetic hazard check to Verified and enter `DEMO-ONLY/hazard-reviewed` as the reference.
5. **Save evidence & reassess**. At the default threshold, this scenario becomes A and contributes to **B → A after updates**.
6. Record a separate staff disposition with a reviewer and rationale. It persists and is excluded from automated STP readiness.

See the complete [user guide](docs/USER_GUIDE.md) for all pages, filters, metrics, exports, settings, and limitations. It is also available inside the application.

## Prediction model

The model is an actual scikit-learn random forest with training-only preprocessing, not a hardcoded prediction function. It learns synthetic A/B/F labels derived from the project's reference rules. The 10,000 rows are split into 8,000 training and 2,000 held-out test rows using seed 42. Test scores measure agreement with the synthetic policy, not real underwriting or claims performance.

- `data/ml/homeowners_synthetic_10000.csv.gz`: complete dataset, labels, and split.
- `models/homeowners_demo.joblib`: fitted pipeline, loaded only from this fixed repository path.
- `models/metadata.json`: actual test results, hyperparameters, feature list, versions, and integrity checksums.
- [Model card](docs/MODEL_CARD.md): intended use, limitations, evaluation, and future real-data development.

Rebuild deliberately after model/data changes or a scikit-learn upgrade:

```bash
python -m homeguard.model
python -m homeguard.data_generator
```

The second command regenerates only the **bundled synthetic portfolio** (1,000 rows, separate seed 2026); it never rewrites saved submissions. Neither training nor generation runs automatically on submission or page refresh. Run training with the pinned dependencies for reproducibility. The scenarios use a fixed as-of date recorded in metadata; review age/date assumptions before reusing them in later years.

The prediction service holds incomplete evidence, invalid inputs, low model support, and model/reference disagreements in B. All three model probabilities, reference findings, and holds remain visible. Explanations identify reference/evidence findings; global importance is not a causal per-case explanation.

## Data and persistence

New applications, decisions, settings, and audit events use SQLite with transactions, WAL, UUID-based IDs, and optimistic case revisions. The default path is `data/runtime/homeguard.sqlite3`. Set `HOMEGUARD_DATA_DIR` to a durable private directory for another location. Back up that directory separately from source code; it is intentionally ignored by Git.

The bundled demo portfolio stays read-only unless you explicitly regenerate it. Saved edits overlay its application IDs in SQLite. Original submission CSVs remain readable as **Legacy submission** without conversion or deletion; missing expanded fields create review tasks. New writes never use the old CSV append path.

A Streamlit hosting environment may have ephemeral local storage. Use a persistent volume or a managed database adapter before relying on records across redeploys. The POC does not provide encryption-at-rest, immutable audit storage, document storage, managed identity, external verification, pricing, policy issuance, or notification delivery.

## Development and verification

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

Tests cover input/rule boundaries, missing fields, model artifact and held-out evaluation integrity, PII/label feature exclusion, concurrent edits, persistence, filtering, all seven Streamlit pages, and the B-to-A/staff-decision workflow. GitHub Actions runs the same checks on Python 3.12.

Review [implementation notes](docs/IMPLEMENTATION.md), [the reference policy](homeguard/VALIDATION_RULES.txt), and [validation results](docs/VALIDATION.md). The reference policy explicitly replaces unsupported legal/compliance claims from the original POC. Thresholds need carrier/product/jurisdiction approval before any real underwriting deployment.

## Branch and rollback

Baseline: `71f02b4a07f08e82868dde99b318f8fa1a7865e4`.

- Upgrade branch: `codex/homeowners-underwriting-workbench`
- Original state: `backup/before-homeowners-upgrade-2026-09-15`

Switch to the backup branch to run the original source. Preserve your runtime database separately before switching; the original application does not understand the new SQLite records.

```bash
git switch backup/before-homeowners-upgrade-2026-09-15
```

The delivery archive includes a complete Git bundle and before/after source snapshots. Follow its `START_HERE.md` to restore the repository or push the upgrade branch from your own GitHub-authorized environment. The connected GitHub integration rejected remote branch creation (403), so the delivered commits are local and the original remote branch was not changed.
