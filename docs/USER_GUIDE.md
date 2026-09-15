# HomeGuard user guide

## Start here

HomeGuard is a homeowners underwriting proof of concept. It helps collect an application, recommend a route, identify the evidence needed for review, and record an underwriter’s work. It does not quote premiums, bind coverage, issue policies, or send notices.

1. Open **New application**. For a first walkthrough, expand **Start from a synthetic example** and choose **B · missing evidence**.
2. Review all five questionnaire sections. Asterisks mark information needed for a complete evaluation. Leave unknown facts unknown.
3. Choose **Save draft** to retain entered values in this browser session. Use **Analyze & submit application** to save a durable record. The identifying fields and valid formats are required; incomplete underwriting information can be submitted for B review.
4. Keep **Save as a demo application** selected for exercises. Synthetic examples include clearly marked fictional evidence; they are not real verification results.
5. Open **Underwriting workbench** and sign in. The default demonstration login is `admin` / `admin123` unless the administrator has configured different credentials.
6. Review the recommendation, model support, evidence gaps, findings, and next actions. No insurance decision has been communicated to the insured.

A saved draft is session-only and should not be relied on after closing the browser. Press **Save draft** before navigating away; unsubmitted changes inside the form are not sent to the server. Submitted applications and review actions persist in the configured workspace data directory.

## Work through a B case

**B means underwriter review.** It may represent missing evidence, an unusual property exposure, inconsistent data, low model support, or a disagreement between the model and reference checks. Completing evidence only resolves the relevant hold; it does not erase a material risk finding.

For the missing-evidence demo:

1. Submit the **B · missing evidence** example and open it in the workbench.
2. Select **Update evidence & reassess**, then **Evidence & consent**.
3. The synthetic hazard report is initially **Not checked**, with no report reference. In this exercise, set it to **Verified** and enter `DEMO-ONLY/hazard-reviewed` as the reference. Keep the synthetic reviewer/date intact. For actual work, record only evidence that a staff reviewer has checked.
4. Select **Save evidence & reassess**. The new facts and assessment are saved together. This example should move to A if the configured support threshold is met.
5. Check **B → A after updates**. It counts saved records initially assessed B that now meet engine A readiness without a staff disposition.

Use the findings table’s next actions to resolve other cases: obtain the missing record, reconcile conflicting facts, document completed repairs, or refer a product or risk question to the underwriter. Entering a source reference alone does not constitute independent verification; no external provider is connected.

Every saved application update retires the prior staff disposition so it cannot silently apply to changed facts. The audit history retains the earlier decision and records the update. If another session has edited the application, refresh and review the new version before saving.

## Recommendations and staff decisions

| Route | Meaning | Next step |
|---|---|---|
| A · STP ready | The model, input/evidence checks, and reference policy support the next pricing step | Continue through an approved pricing and issuance workflow outside this POC |
| B · Underwriter review | Information or risk questions need attention | Resolve the listed tasks and reassess, or record a reasoned staff disposition |
| F · Recommended for rejection | The current POC recommendation is rejection | An underwriter reviews and documents the decision; no automatic denial is issued |

The model produces a class and class support. Missing/invalid information, incomplete verification, model support below the configured threshold, or a model/reference disagreement hold the route in B. Model probabilities are not calibrated estimates of real underwriting outcomes.

To document a human assessment, open **Record staff decision**, choose the disposition, enter the reviewing underwriter and supporting rationale, and select **Record decision**. These fields are required. The staff disposition becomes the portfolio’s current outcome but remains separate from the engine recommendation.

The insured update button downloads a text draft. It does not send email. F is always labeled a recommendation for rejection; communications and any final coverage decision remain outside the app.

## Page reference

| Page | What you can do |
|---|---|
| Overview | Understand the workflow and jump to intake or the workbench |
| New application | Capture a detailed homeowners application, save a session draft, load synthetic examples, and submit a durable record |
| Underwriting workbench | Filter sources/dates, review a home, resolve evidence, reassess, record decisions, inspect history, and export records |
| Industry background | Read dated homeowners statistics, coverage concepts, and the reason for collecting supporting evidence |
| User guide | Follow the walkthrough and look up terminology and limitations |
| Model lab | Inspect the actual training/test split, synthetic results, feature use, and model metadata; download the training/test dataset |
| Settings | Save the demonstration options, applicant result visibility, workbench authentication, and model support threshold |

**Questionnaire sections:** Insured & dwelling covers named insureds, address, ownership, occupancy, construction, and use. Roof & systems covers age, materials, condition, electrical, plumbing, heating, and repairs. Protection & hazards covers protective devices, fire response, premises liability, and catastrophe indicators. Coverage & losses covers requested policy form, coverages A–F, deductibles, endorsements, prior insurance, and loss history. Evidence & consent links property, roof, claims, hazard, and replacement-cost checks to references, a reviewer, review date, and confirmations.

**Portfolio filters:** Demo portfolio is the bundled 1,000-record exercise set. Demo application contains synthetic submissions you save. Submission contains records saved with the demo checkbox off. Legacy submission exposes older CSV records without overwriting them. Older records may need additional information for the expanded questionnaire. An empty selection returns no records; the filters remain available. Date filters apply to every selected source and use the submission’s UTC date. Undated records are excluded when a date bound is set.

**Application register:** Download a compact register or the full questionnaire and assessment columns as CSV. ZIP text preserves leading zeroes in the file; import the ZIP column as text in spreadsheet software. Values that could be interpreted as spreadsheet formulas are escaped on export.

**History:** Case history includes all saved case events, with the latest 30 shown on screen. Portfolio history shows the latest 2,000 global events filtered to visible application IDs. Download full case history for a complete individual record. This POC history is a database log, not an immutable compliance archive.

**Settings:** Changes persist across pages and browser sessions. Settings always requires staff sign-in. Turning off workbench authentication is intended for isolated synthetic demonstrations. Applicant recommendations are hidden by default. Synthetic example buttons appear only while the demonstration option is enabled.

## Metrics and model limits

**STP readiness** = current engine-A records without a staff disposition ÷ all records in the selected portfolio view. It measures readiness for a next pricing step, not issued policies or end-to-end straight-through processing. Changing the source/date filters changes the denominator.

**B → A after updates** counts initially B records with a saved revision that now meet engine A readiness and have no staff disposition. **Staff-cleared** counts human A dispositions separately. A human override never increases the automated-readiness numerator. **Open B reviews** uses the current effective outcome; staff B remains an open review. Rejection recommendations count engine F cases awaiting a staff action.

The random forest uses 10,000 fictional applications: 8,000 training rows and 2,000 held-out test rows. Labels come from POC reference rules, not actual claims or historical underwriting outcomes. The test metrics measure how well the model reproduces that synthetic policy. They do not validate loss prediction, pricing, real-world STP improvement, fairness, or regulatory suitability.

The model uses selected property, claims, coverage, and exposure fields. Names, contacts, street addresses, ZIP codes, state, application IDs, reference labels, split labels, and evidence status are excluded from model features. Other questionnaire fields support evidence checks, referral logic, or underwriter context. Exclusion of these inputs alone does not establish fairness. Model Lab provides the exact feature list and a field dictionary.

Reference findings explain policy checks, not the causal workings of the forest. Global feature importance summarizes model-wide use and should not be presented as the reason for an individual insurance decision. The recorded model recommendation, reference recommendation, holds, and final route are all visible separately.

## Terms and future work

**Named insured:** the person or entity whose interest is being considered for coverage. **Replacement cost:** the estimate to rebuild the dwelling, distinct from purchase price. **Coverage A–F:** policy coverage categories; they are separate from HomeGuard’s A/B/F routing classes. **Evidence discrepancy:** a source and the recorded facts disagree. **Model support:** the model’s class-probability output, not a guarantee of correctness.

The legacy field called `loss_ratio` is five-year paid claims divided by dwelling replacement cost. In this app it is described as **claims / replacement cost**. It is not the insurance industry’s incurred-loss-to-earned-premium loss ratio. The 25%/75% and other reference thresholds are illustrative POC choices; they are not universal carrier standards.

Future integrations can verify property records, replacement cost, roof condition, loss history, and hazard reports; extract and explain document facts; connect pricing and policy administration; and produce controlled customer communications. Real-data model development needs a defined prediction target, authorized historical data, outcome labels, leakage controls, validation on later data, monitoring, and the applicable carrier/jurisdiction review. Those capabilities are not connected in this version.
