# Implementation notes

## Product scope

This update implements the requested homeowners language, industry background and guide, professional visual redesign, expanded questionnaire, and dummy predictive model. The unspecified later task remains future work. The initial code review covered all repository source, sample data, setup, and rule documents before changes.

The application now has seven navigable pages. The questionnaire is a shared declarative schema, so intake, review editing, field dictionaries, validation, and exports use the same questions. It covers 121 fields, with 68 required for complete evaluation. Unknown information is explicit. All 50 states and DC are available; the synthetic portfolio is not population-weighted or geographically realistic.

## Architecture

`streamlit_app.py` owns page navigation and the common visual shell. Pages call independent domain modules:

- `schema.py`: field labels, types, accepted values, and question roles.
- `validation.py`: input quality, evidence completeness, derived values, and the transparent reference policy.
- `model.py`: deterministic data split, fitted preprocessing/forest, integrity checks, and batch predictions.
- `prediction.py`: model result plus evidence, quality, confidence, and disagreement holds.
- `storage.py`: transactional applications, case revisions, staff dispositions, settings, and events.
- `portfolio.py`: source loading, unique-ID overlays, date filters, effective outcomes, and STP-readiness metrics.
- `synthetic.py`: complete fictional application scenarios.
- `industry.py`: dated educational statistics with primary attribution.

The retained generator/submission-manager module names are compatibility adapters to the new functionality. They no longer contain separate contradictory rule logic, global sample counters, automatic CSV archiving, or CSV appends. The historical reference CSVs are not executable policy inputs; their old legal or appetite statements have not been certified.

## Material defects addressed

| Original issue | Result |
|---|---|
| Form omitted the derived claims ratio | Recomputed from paid claims and replacement cost on every assessment |
| Entirely absent required fields could escape checking | Schema-based missing, format, consistency, and range checks hold B |
| Synthetic examples changed on reruns/submission | Examples load only on an explicit button click and populate a stable draft |
| Draft/settings values disappeared across navigation | Draft snapshots are separate from widget state; settings are stored durably |
| Decisions were session-only and portfolio metrics stayed stale | Decisions persist, overlay current outcomes, and remain separate from automated STP |
| CSV append could lose concurrent submissions; IDs could collide | SQLite transactions, UUID-based IDs, and optimistic case revisions |
| Filters could append duplicate dates or disappear when empty | Source-first loading, ID deduplication, UTC date filtering, persistent controls |
| ZIP columns lost leading zeroes | CSV imports preserve strings; UI uses text; storage retains the value |
| Email button implied successful delivery without sending | Downloadable insured-update draft, explicitly labeled unsent |
| Audit helper did not represent persistent review history | Saved changes, assessments, decisions, and settings produce database events |
| Rule/legal claims and code did not match | Versioned reference specification with POC thresholds and human-owned F recommendation |
| Setup referenced uv project files that did not exist | Python 3.12, pinned requirements, working pip setup, and CI |

## Review and automation behavior

Engine status and staff disposition are separate fields. A case's current effective outcome uses a valid staff disposition when present. STP readiness includes only engine-A records without any staff disposition. Initially B records only count as recovered after a saved revision has moved the engine to A without a staff disposition. These metrics are not end-to-end policy issuance statistics.

Application updates invalidate a prior staff disposition while retaining its audit event. Application edits and decisions both increment case revisions; stale sessions cannot silently overwrite either. First edits to a bundled or legacy record create a durable overlay with the source ID. Legacy data are not destructively migrated.

Input/evidence holds take precedence over F risk recommendations. A case with severe reference findings and missing facts therefore remains B pending review; its severe findings remain visible. Staff can record a reasoned disposition, but the software does not automatically issue an adverse action or customer notice.

Unauthenticated non-demo intake cannot self-attest that staff verification is complete. The saved verification fields are reset to Not checked; staff must review them. The default POC sign-in and optional unauthenticated demo workbench are for synthetic use, not a production access-control design.

## Sources and interpretation

The Industry background page links each statistic to its reporting period and source. Claims frequency is per 100 house-years, severity excludes loss-adjustment expenses, and loss-cause shares are shares of losses rather than claim counts. Sample portfolio metrics and synthetic class proportions are not presented as industry benchmarks. The questionnaire is an original design informed by public homeowners coverage concepts; it is not a licensed ACORD form or carrier-approved application.

Sources: [Triple-I homeowners statistics](https://www.iii.org/fact-statistic/facts-statistics-homeowners-and-renters-insurance), [NAIC's 2022 report announcement](https://content.naic.org/article/naic-releases-homeowners-insurance-report-2022), [Travelers coverage guide](https://www.travelers.com/home-insurance/coverage), [scikit-learn forests](https://scikit-learn.org/stable/modules/ensemble.html#forest), [scikit-learn evaluation](https://scikit-learn.org/stable/modules/model_evaluation.html). Checked September 15, 2026.

## Known limits and next development

This version records manual verification with references. It does not retrieve reports, inspect uploaded documents, verify addresses, or perform image analysis. Some fields are contextual rather than model features. Hazard scales and reference thresholds are artificial. Training labels come from the reference policy, so this model demonstrates the engineering workflow rather than discovering real loss outcomes.

The SQLite design assumes a persistent single-instance workspace. A later project should define a real prediction target, build authorized provider adapters, use managed identity and a durable multi-user database, introduce evidence extraction with source traceability, and validate independent historical outcomes. Real performance and applicable carrier/jurisdiction requirements remain to be established.
