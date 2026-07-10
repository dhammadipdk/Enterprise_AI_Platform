# Regulatory Domain

**Domain Version:** 1.0.0  
**Status:** Active Development  
**Knowledge Standard Version:** 1.0.0  
**Project:** InsureAI  
**Domain Owner:** Regulatory Domain  
**Created On:** July 2026  
**Last Updated:** July 2026

---

# 1. Purpose

The Regulatory domain represents the canonical knowledge base governing insurance regulations, statutory requirements, legal references, compliance obligations, and business rules applicable to the InsureAI platform.

Unlike transactional domains such as Policy or Claims, the Regulatory domain does not represent operational business events. Instead, it represents the authoritative knowledge that determines how insurance products, underwriting decisions, claims processing, repairs, customer interactions, and recommendations should behave.

The Regulatory domain provides a structured representation of regulations, circulars, legal provisions, compliance requirements, rule traceability, and policy interpretation.

---

# 2. Scope

Version 1 focuses on Indian motor insurance regulations.

The domain includes:

- Regulatory authorities
- Acts and statutes
- IRDAI regulations
- Circulars and notifications
- Business rules
- Eligibility rules
- Coverage rules
- Claim settlement rules
- Compliance requirements
- Regulatory interpretation

---

# 3. Business Objectives

The Regulatory domain aims to:

- Maintain a canonical regulatory knowledge base.
- Standardize insurance rules.
- Support explainable compliance.
- Enable rule-based reasoning.
- Support AI-assisted interpretation.
- Track regulation versions.
- Maintain regulatory traceability.
- Improve auditability.
- Reduce compliance risks.
- Support enterprise knowledge retrieval.

---

# 4. Business Responsibilities

The Regulatory domain is responsible for:

- Managing regulatory sources.
- Managing legal references.
- Managing regulations.
- Managing circulars.
- Managing business rules.
- Managing compliance requirements.
- Managing rule versions.
- Managing regulatory lifecycle.
- Supporting rule interpretation.
- Supporting AI-assisted regulatory reasoning.

The Regulatory domain does not own customers, policies, claims, repairs, or documents.

---

# 5. Domain Boundaries

## In Scope

The Regulatory domain owns:

- Regulatory Authority
- Regulation
- Legal Reference
- Circular
- Business Rule
- Compliance Requirement
- Rule Version
- Regulatory Lifecycle
- Rule Interpretation
- Regulatory Assessment

---

## Out of Scope

| Business Area | Owning Domain |
|---------------|---------------|
| Customer | Customer |
| Driver | Driver |
| Vehicle | Vehicle |
| Insurance Products | Insurance |
| Coverage | Coverage |
| Policy | Policy |
| Claims | Claims |
| Repair | Repair |
| Documents | Documents |

---

# 6. Core Business Concepts

The Regulatory domain contains concepts related to:

- Regulatory Authority
- Regulation
- Legal Reference
- Circular
- Business Rule
- Compliance
- Rule Version
- Lifecycle
- Interpretation
- Assessment

Formal definitions are maintained in **glossary.csv**.

---

# 7. Business Entities

Version 1 defines the following entities.

| Entity | Type |
|---------|------|
| Regulation | Aggregate Root |
| Regulatory Authority | Entity |
| Legal Reference | Entity |
| Circular | Entity |
| Business Rule | Entity |
| Compliance Requirement | Entity |
| Rule Version | Entity |
| Regulatory Lifecycle | Entity |
| Rule Interpretation | Entity |
| Regulatory Assessment | Entity |

Definitions are maintained in **entity_catalog.csv**.

---

# 8. Repository Artifacts

The Regulatory domain consists of:

| Artifact | Purpose |
|----------|---------|
| README.md | Domain specification |
| glossary.csv | Business vocabulary |
| entity_catalog.csv | Business entities |
| canonical_schema.csv | Canonical attributes |

---

# 9. Relationships with Other Domains

| Related Domain | Relationship |
|----------------|--------------|
| Insurance | Defines product and pricing regulations. |
| Coverage | Governs coverage eligibility and exclusions. |
| Policy | Governs issuance, endorsements, cancellations, and renewals. |
| Claims | Governs admissibility, settlement, documentation, and fraud procedures. |
| Repair | Governs approved repair practices and compliance. |
| Documents | Defines mandatory documentation and retention requirements. |
| Recommendation | Provides the regulatory foundation for AI reasoning and explanations. |

---

# 10. Dependencies

This domain follows all shared repository standards including:

- Modeling Guidelines
- Naming Conventions
- Identifier Conventions
- Business Metadata Dictionary
- Entity Types
- Concept Categories
- Semantic Classes
- Lifecycle States
- Data Types
- Privacy Classes
- Collection Sources
- Reference Catalogs
- Validation Patterns

---

# 11. Future Evolution

Future versions may include:

- Automated IRDAI circular ingestion
- Regulatory change detection
- Rule conflict analysis
- Temporal rule reasoning
- Cross-jurisdiction regulations
- LLM-assisted legal interpretation
- Regulatory knowledge graph
- Automated compliance validation
- Rule impact analysis
- AI-powered legal copilot

Version 1 intentionally focuses on canonical insurance regulatory knowledge.

---

# 12. Revision History

| Version | Date | Author | Description |
|---------|------|--------|-------------|
| 1.0.0 | July 2026 | InsureAI Core Team | Initial Regulatory domain specification. |
