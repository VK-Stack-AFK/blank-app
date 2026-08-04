# HomeGuard UW Validator

**HomeGuard UW Validator** is a Streamlit proof-of-concept dashboard for **personal homeowners insurance pre-pricing underwriting validation**.

The app is intentionally scoped to everything **before pricing**:

- application completeness validation
- property record matching
- roof/condition flagging
- claims history summarization
- hazard exposure checks
- factor permission checks
- state-level AI/regulatory guardrails
- straight-through-processing readiness routing
- human review queue
- audit logging

It does **not** set premiums, bind coverage, or automatically deny homeowners insurance.

## Why this exists

The project demonstrates how a homeowners insurer could use automation and AI assistance to reduce manual pre-pricing underwriting friction while maintaining human governance over regulated decisions.

## Dashboard pages

1. **Executive Overview** — KPIs, STP-ready rate, compliance holds, referral rate, portfolio charts.
2. **Application Validator** — one-file validation with reason codes and next actions.
3. **Verification Tools** — what should be AI-driven vs. human-governed.
4. **Rules & Regulation Matrix** — starter legal/factor rules and mock carrier appetite rules.
5. **Human Review Queue** — files that should not proceed STP.
6. **Audit Log** — data sources, tools used, model/rule versions, and routing explanations.
7. **Data / GitHub Notes** — upload schema and setup instructions.

## Folder structure

```text
homeguard_uw_validator/
  app.py
  requirements.txt
  README.md
  .gitignore
  data/
    applications.csv
    state_ai_rules.csv
    factor_permissions.csv
    carrier_appetite_rules.csv
  homeguard/
    __init__.py
    config.py
    validation.py
```

## How to run locally

### 1. Install Python

Use Python 3.10+.

### 2. Open terminal in this folder

```bash
cd homeguard_uw_validator
```

### 3. Create a virtual environment

Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

Mac/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Run Streamlit

```bash
streamlit run app.py
```

Streamlit should open a browser window automatically. If not, copy the local URL printed in terminal.

## How to put this on GitHub

### Option A: easiest GitHub web upload

1. Go to GitHub.com.
2. Create a new repository named `homeguard-uw-validator`.
3. Upload all files/folders from this project folder.
4. Commit the upload.

### Option B: command-line Git

```bash
git init
git add .
git commit -m "Initial HomeGuard UW Validator POC"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/homeguard-uw-validator.git
git push -u origin main
```

## Streamlit Community Cloud deployment

1. Push the project to GitHub.
2. Go to Streamlit Community Cloud.
3. Create a new app.
4. Pick your GitHub repo.
5. Set main file path to `app.py`.
6. Deploy.

## Important design decision

This POC uses a **fictional homeowners carrier appetite rule set** in `data/carrier_appetite_rules.csv`.

Do not claim these are Aetna's rules. Aetna is primarily a health insurer, not a personal homeowners carrier. If a real homeowners carrier provides underwriting validation rules, replace the CSV with those approved rules after legal/compliance review.

## Legal/compliance note

This is not legal advice. Any real use with consumer insurance data should be reviewed by counsel, compliance, actuarial, and underwriting leadership. Real deployment would require controls around FCRA, GLBA/privacy, state unfair discrimination laws, state insurance department guidance, AI model governance, data retention, and adverse-action notices where applicable.
