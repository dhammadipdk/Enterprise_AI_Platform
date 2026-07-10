# Enterprise Reference Data

**Version:** 1.0.0  
**Status:** Active Development  
**Project:** InsureAI  
**Scope:** Indian Motor Insurance  
**Owner:** Shared Knowledge Standards

---

# 1. Purpose

The Reference Data repository contains canonical business master datasets used across every knowledge domain within InsureAI.

Reference data represents relatively stable business concepts whose values are reused by multiple domains. These datasets establish a single source of truth for identifiers, codes, names, and hierarchical relationships.

Unlike operational business entities, reference data changes infrequently and is intended to maximize consistency, interoperability, explainability, and data quality.

---

# 2. Scope

Version 1 focuses exclusively on Indian private motor insurance.

The repository contains reference datasets for:

- Indian geography
- Customer demographics
- Vehicle classification
- Insurance products
- Claims
- Repair
- Documents
- Regulatory authorities

---

# 3. Design Principles

Every reference dataset must satisfy the following principles.

- Canonical representation
- Stable identifiers
- Human-readable business names
- Machine-readable business codes
- Traceable provenance
- Effective dating
- Enterprise reuse
- Domain independence

---

# 4. Master Dataset Types

Reference datasets are categorized into three canonical templates.

## Code Masters

Simple enumerations.

Examples:

- Fuel Types
- Claim Types
- Policy Types
- Coverage Types
- Document Types

---

## Hierarchical Masters

Hierarchical business data.

Examples:

- States
- Districts
- Cities
- RTO Regions

---

## Organization Masters

Business organizations.

Examples:

- Insurance Companies
- Manufacturers
- Regulatory Authorities

---

# 5. Repository Structure

```
reference_data/

india/
customer/
vehicle/
insurance/
claims/
repair/
documents/
regulatory/

templates/
```

---

# 6. Source of Truth

Wherever possible, datasets should originate from official authorities.

Examples include:

- Government of India
- IRDAI
- Ministry of Road Transport & Highways
- India Post
- GST Council
- Vehicle manufacturers

---

# 7. Versioning

Reference datasets are version-controlled.

Every record supports:

- Effective date
- Expiry date
- Source authority
- Status

allowing future updates without breaking downstream systems.

---

# 8. Future Evolution

Future versions may include automated synchronization with official public datasets, validation pipelines, and change detection.

Version 1 intentionally provides canonical enterprise master datasets.
