# Regulatory References & Industry Context

> **Portfolio boundary:** This repository is a **learning and portfolio prototype** using synthetic data only. It is **not** validated software, does not claim compliance with any regulation, and must not be used for regulated decisions. The references below exist so that design choices (audit trail, attribution, contemporaneous timestamps, explainable scoring) can be understood in the same language used by industry and inspectors.

This document maps major regulations and guidance that shape how **information systems** are expected to behave in GxP environments — pharmaceuticals, biologics, medical devices, and related regulated supply chains.

---

## 1. United States — FDA

### 1.1 21 CFR Part 11 — Electronic Records; Electronic Signatures

| Item | Detail |
|------|--------|
| **What it is** | Criteria under which FDA considers electronic records and electronic signatures trustworthy, reliable, and generally equivalent to paper records and handwritten signatures |
| **Authority** | 21 CFR Part 11 (final rule 1997) |
| **Official text** | [eCFR — 21 CFR Part 11](https://www.ecfr.gov/current/title-21/chapter-I/subchapter-A/part-11/) |
| **Key controls (closed systems, § 11.10)** | Validation; accurate/complete copies; protection of records; limited access; **secure, computer-generated, time-stamped audit trails**; operational system checks; authority checks; device checks; education/training; written policies; controls over documentation; controls over systems documentation |
| **Audit trail language (§ 11.10(e))** | Record changes shall not obscure previously recorded information |

**Related guidance (scope & application):**  
[Part 11, Electronic Records; Electronic Signatures — Scope and Application](https://www.fda.gov/regulatory-information/search-fda-guidance-documents/part-11-electronic-records-electronic-signatures-scope-and-application)  
FDA describes a risk-based approach and enforcement discretion in certain areas while predicate rules (e.g., CGMP) still require trustworthy records.

**How this prototype relates (illustratively only):**  
Append-only `audit_log`, server-generated UTC timestamps, actor attribution via header, and immutable review actions are **design patterns** that echo Part 11 themes — not a claim of Part 11 validation.

---

### 1.2 Data Integrity & CGMP (Drugs)

| Item | Detail |
|------|--------|
| **Guidance** | *Data Integrity and Compliance With Drug CGMP — Questions and Answers* (FDA, Dec 2018) |
| **Core definition** | Data integrity = completeness, consistency, and accuracy of data |
| **ALCOA** | Complete, consistent, and accurate data should be **Attributable, Legible, Contemporaneously recorded, Original (or a true copy), and Accurate** |
| **Lifecycle** | Creation, modification, processing, maintenance, archival, retrieval, transmission, disposition |
| **Predicate examples** | 21 CFR Parts 211 and 212 (among others) for finished pharmaceuticals and PET drugs |

**Official FDA guidance page:** search “Data Integrity and Compliance With Drug CGMP” on [fda.gov guidance documents](https://www.fda.gov/regulatory-information/search-fda-guidance-documents).

**ALCOA → design intent in this repo (educational mapping):**

| Attribute | Regulatory idea | Prototype illustration |
|-----------|-----------------|------------------------|
| **Attributable** | Who performed the action | `actor` / `X-Actor` on review and middleware events |
| **Legible** | Readable, permanent meaning | Structured JSON/API responses + human-readable `contributing_reasons[]` |
| **Contemporaneous** | Recorded at the time of the activity | Server-side UTC `created_at`, not client-supplied |
| **Original / true copy** | First capture or verified copy | Append-only log; no update/delete of audit rows |
| **Accurate** | Correct and valid | Pydantic validation, explainable rule-based scores |

ALCOA+ (widely used industry extension) typically adds **Complete, Consistent, Enduring, Available** — emphasized in MHRA and PIC/S materials (see below).

---

### 1.3 Computer Software Assurance (CSA) — Medical Devices / QMS Software

| Item | Detail |
|------|--------|
| **Guidance** | *Computer Software Assurance for Production and Quality Management System Software* (FDA final guidance; updates through 2025–2026) |
| **Focus** | Risk-based assurance for computers and automated data processing systems used in **production or quality management systems** (not SaMD/SiMD product software itself) |
| **Regulatory anchor** | Supports confidence relative to quality system obligations, including concepts historically tied to 21 CFR Part 820 (and QMSR evolution) |
| **Official page** | [FDA — Computer Software Assurance…](https://www.fda.gov/regulatory-information/search-fda-guidance-documents/computer-software-assurance-production-and-quality-management-system-software) |

**Takeaway for engineers:** assurance effort should scale with **risk to product quality/safety and record integrity**, not with “validate everything the same way.”

**Related classic guidance:** *General Principles of Software Validation* (FDA) — still foundational; CSA guidance updates how industry thinks about production/QMS software assurance.

---

### 1.4 Other FDA-relevant system contexts

| Area | Why information systems matter |
|------|--------------------------------|
| **21 CFR Part 211** | CGMP for finished pharmaceuticals — production records, lab records, equipment, backup of data (§ 211.68), record retention |
| **21 CFR Part 820 / QMSR** | Quality system for medical devices — design controls, production & process controls, document controls, software used in QMS/production |
| **Clinical investigations** | Electronic systems and Part 11 expectations for records used in FDA-regulated clinical research (see FDA electronic systems / clinical investigation guidance Q&As) |
| **Biologics / blood / PET** | Parallel predicate rules; same integrity expectations for electronic records supporting CGMP decisions |

---

## 2. United Kingdom — MHRA

| Document | Role |
|----------|------|
| **‘GXP’ Data Integrity Guidance and Definitions** (MHRA, Revision 1, March 2018) | Definitions and expectations across GxP (GMP, GDP, GLP, GCP, GPvP) |
| **ALCOA** | Attributable, Legible, Contemporaneous, Original, Accurate |
| **ALCOA+ emphasis** | Complete, Consistent, Enduring, Available throughout the data lifecycle |
| **Source** | [GOV.UK / MHRA publications](https://www.gov.uk/) — search “GxP data integrity” |

MHRA materials are widely cited internationally and align closely with PIC/S thinking.

---

## 3. PIC/S — International inspectorates

| Document | Role |
|----------|------|
| **PIC/S PI 041-1** — *Good Practices for Data Management and Integrity in Regulated GMP/GDP Environments* (effective 1 July 2021) | Detailed expectations for paper, electronic, and hybrid systems; audit trails; data review; outsourcing |
| **Official site** | [picscheme.org](https://picscheme.org/) |

PIC/S guidance is used by many inspectorates worldwide and is a practical bridge between regional rules and day-to-day data governance.

---

## 4. European Union

| Instrument | Focus |
|------------|--------|
| **EU GMP Annex 11** — Computerised Systems | Risk-based validation, suppliers, audit trails, security, data migration, business continuity |
| **EU GMP Chapter 4** — Documentation | Documentation principles that underpin data integrity for paper and electronic records |
| **EMA / European Commission** | Evolving revisions of Chapter 4 and Annex 11 (monitor official EMA/EC publications) |

Annex 11 remains a primary reference for computerized systems in EU GMP environments and is frequently cited alongside Part 11 in global programs.

---

## 5. WHO & other global references

| Document | Notes |
|----------|--------|
| **WHO** technical reports on good data and record management / data integrity | ALCOA(+) framing for medicines regulation in many jurisdictions |
| **OECD** GLP documents | Data integrity expectations in non-clinical studies |
| **ISPE GAMP 5** (industry guide, not law) | Risk-based approach to compliant GxP computerized systems; widely used by industry for CSV / CSA-style programs |

GAMP 5 is **not** a regulation; it is a widely adopted industry framework for scaling validation/assurance effort to system risk and novelty.

---

## 6. Industries where information-system controls are heavily regulated

| Industry / domain | Typical drivers |
|-------------------|-----------------|
| **Pharmaceutical manufacturing (human/veterinary)** | CGMP, Part 11, data integrity guidance, Annex 11, PIC/S |
| **Biologics & vaccines** | CGMP + product-specific expectations; electronic batch records |
| **Medical devices** | QMS (Part 820 / QMSR), CSA guidance for production/QMS software |
| **Clinical research / GCP** | Trial master file, eSource, Part 11 for records submitted to or inspected by FDA |
| **Laboratories (QC / GLP)** | Lab systems, raw data, audit trails, contemporaneous recording |
| **Distribution (GDP)** | Traceability, temperature data, integrity of supply-chain records |
| **Pharmacovigilance** | Case data integrity, auditability of safety databases |
| **Blood / tissue / advanced therapies** | Strict identity, chain of custody, electronic record controls |
| **Food (where applicable)** | FSMA and related systems; different statute but similar integrity themes for electronic records |
| **Cannabis (US state / some markets)** | Track-and-trace systems; varying electronic record rules |

Cross-cutting theme: **if a decision about product quality, patient safety, or regulatory submission depends on data, the system that holds that data is in scope for integrity and (often) validation/assurance.**

---

## 7. What “good” looks like in system design (inspector-friendly themes)

These themes appear repeatedly across FDA, MHRA, PIC/S, and EU materials:

1. **Unique attribution** — no shared accounts for GxP actions  
2. **Audit trails** that are enabled, protected, and **reviewed** (not only stored)  
3. **Contemporaneous capture** — trusted time, no routine backdating  
4. **Original data / true copies** — retain source; control transcription  
5. **Access control & segregation of duties**  
6. **Validated / assured** systems scaled to risk (CSV / CSA mindset)  
7. **Backup & enduring availability** for the retention period  
8. **Hybrid paper–electronic** processes under explicit control  
9. **Supplier / cloud** oversight when GxP data lives outside the company  
10. **Data lifecycle** thinking — create → use → archive → dispose

---

## 8. How to read this repo against the references

| Theme | In this prototype |
|-------|-------------------|
| Audit trail | Append-only SQLite `audit_log` + middleware on mutating requests |
| Attribution | Required actor on review actions |
| Contemporaneous time | Server UTC timestamps |
| Explainability | Rule-based risk score + `contributing_reasons[]` |
| Testing culture | Automated tests + CI (engineering discipline that supports future validation evidence) |
| Transparency | OpenAPI docs, architecture notes, known limitations |

**Explicit non-claims:** no electronic signatures per § 11.50–11.70, no full RBAC, no IQ/OQ/PQ protocols, no change control board, no production data, no regulatory filing use.

---

## 9. Suggested further reading (primary sources first)

1. [21 CFR Part 11 (eCFR)](https://www.ecfr.gov/current/title-21/chapter-I/subchapter-A/part-11/)  
2. FDA — *Part 11 Scope and Application* guidance  
3. FDA — *Data Integrity and Compliance With Drug CGMP* (Q&A)  
4. FDA — *Computer Software Assurance for Production and Quality Management System Software*  
5. FDA — *General Principles of Software Validation*  
6. MHRA — *GxP Data Integrity Guidance and Definitions* (2018)  
7. PIC/S PI 041-1 — Data management and integrity  
8. EU GMP Annex 11 & Chapter 4  
9. ISPE GAMP 5 (industry practice guide)

Always prefer the **official regulator site** (fda.gov, gov.uk, picscheme.org, ema.europa.eu) over secondary blogs when building SOPs or validation strategies.

---

**Maintainer note:** Update this file when major guidance is revised (CSA, Annex 11 drafts, Part 11 reexamination). Keep the portfolio-safety disclaimer intact.

*Last updated: 2026-08-17*
