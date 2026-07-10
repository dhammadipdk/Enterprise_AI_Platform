# InsureAI Business Metadata Dictionary

**Document Version:** 1.0.0  
**Status:** Frozen (V1 Standard)  
**Knowledge Standard Version:** 1.0.0  
**Project:** InsureAI  
**Owner:** Knowledge Engineering Team  
**Created On:** July 2026  
**Last Updated:** July 2026

---

# 1. Purpose

The Business Metadata Dictionary defines the meaning, usage, ownership, and governance of every metadata field used throughout the InsureAI Knowledge Repository.

It provides a common understanding of repository metadata and ensures consistent interpretation across all business domains.

This document serves as the authoritative reference for contributors, developers, data engineers, AI systems, and domain experts.

---

# 2. Objectives

The metadata dictionary is designed to:

- Standardize metadata definitions.
- Eliminate ambiguity.
- Support automated validation.
- Improve interoperability.
- Enable future code generation.
- Support knowledge governance.

---

# 3. Repository Artifacts

The repository currently contains the following core artifacts:

| Artifact | Purpose |
|----------|---------|
| glossary.csv | Business vocabulary and concepts |
| entity_catalog.csv | Business entities |
| canonical_schema.csv | Entity attributes |

Future artifacts (taxonomy, ontology, rules, knowledge graph) will define their metadata independently while following the same principles.

---

# 4. Metadata Definition Standard

Every metadata field must define:

- Business purpose
- Data type
- Allowed values
- Whether the field is mandatory
- Validation requirements
- Examples
- Remarks

No metadata field may exist without documentation.

---

# 5. Definition Writing Guidelines

Business definitions must:

- Begin with a noun phrase.
- Describe business meaning rather than implementation.
- Avoid database terminology.
- Avoid software-specific language.
- Be concise but complete.
- Be understandable by both business and technical users.

Example:

✔ The official registration number assigned to a motor vehicle.

✘ Stores vehicle registration number.

✘ Registration number.

---

# 6. Shared Metadata Fields

The following metadata fields are standardized across repository artifacts.

## glossary.csv

- glossary_id
- canonical_term
- business_definition
- domain
- concept_category
- semantic_class
- lifecycle
- parent_concept
- derived_from
- aliases
- example
- source
- remarks

## entity_catalog.csv

- entity_id
- entity_name
- business_definition
- entity_type
- parent_entity
- glossary_reference
- business_identifier
- lifecycle
- owned_by_domain
- remarks

## canonical_schema.csv

- schema_id
- entity_id
- attribute_name
- business_definition
- data_type
- required
- derived
- derived_from
- default_value
- validation_rule
- reference_catalog
- collection_source
- privacy_class
- example_value
- ai_importance
- remarks

---

# 7. Controlled Vocabulary Usage

Metadata values must originate from approved controlled vocabularies where applicable.

Examples include:

- Entity Types
- Concept Categories
- Semantic Classes
- Lifecycle States
- Data Types
- Privacy Classes
- AI Importance Levels
- Collection Sources
- Reference Catalogs

Free-text values should be avoided whenever a controlled vocabulary exists.

---

# 8. Metadata Governance

Metadata fields are governed by the Shared Knowledge Standards.

Version 1 permits:

- Clarification of definitions.
- Documentation improvements.
- Additional examples.

Version 1 does not permit:

- Adding metadata fields.
- Removing metadata fields.
- Renaming metadata fields.
- Changing field semantics.

Structural changes require a future major version.

---

# 9. Relationship to Controlled Vocabularies

The Business Metadata Dictionary defines the purpose of metadata fields.

Controlled vocabulary CSVs define the allowed values for those fields.

Both components are required for a complete metadata standard.

---

# 10. Revision History

| Version | Date | Author | Description |
|---------|------|--------|-------------|
| 1.0.0 | July 2026 | InsureAI Core Team | Initial business metadata dictionary. |
