# InsureAI Naming Conventions

**Document Version:** 1.0.0  
**Status:** Frozen (V1 Standard)  
**Knowledge Standard Version:** 1.0.0  
**Project:** InsureAI  
**Owner:** Knowledge Engineering Team  
**Created On:** July 2026  
**Last Updated:** July 2026

---

# 1. Purpose

This document defines the repository-wide naming conventions used throughout the InsureAI Knowledge Repository.

Consistent naming improves readability, discoverability, interoperability, maintainability, and automated processing.

These conventions apply to every knowledge artifact unless explicitly documented otherwise.

---

# 2. General Principles

Naming should follow these principles:

- Be business-oriented.
- Be descriptive.
- Be unambiguous.
- Be consistent.
- Prefer complete words over abbreviations.
- Avoid implementation-specific terminology.
- Avoid unnecessary prefixes and suffixes.

---

# 3. Repository Names

Repository names use:

- lowercase
- words separated by hyphens

Example:

```text
insure-ai
```

---

# 4. Directory Names

Directory names use:

- lowercase
- words separated by underscores

Examples:

```text
reference_data
business_rules
shared
customer
vehicle
driver
```

---

# 5. Markdown Files

Markdown files use:

- lowercase
- words separated by underscores

Examples:

```text
README.md
knowledge_architecture.md
system_context.md
business_process_model.md
insurance_domain_blueprint_v1.md
```

README.md is the only uppercase filename used in the repository.

---

# 6. CSV Files

CSV filenames use:

- lowercase
- words separated by underscores

Examples:

```text
glossary.csv
entity_catalog.csv
canonical_schema.csv
entity_types.csv
privacy_classes.csv
reference_catalogs.csv
```

---

# 7. Business Domains

Business domain names use:

- Singular nouns
- Title Case

Examples:

Customer

Driver

Vehicle

Insurance

Coverage

Claims

Repair

Geography

Regulatory

Documents

Reference Data

Platform

---

# 8. Business Concepts

Business concepts use:

- Title Case
- Singular form
- Natural business terminology

Examples:

Customer

Vehicle Registration

Driving Licence

Fuel Type

Insurance Policy

Preferred Insurer

Avoid:

Customers

Vehicle Registrations

Fuel Types

---

# 9. Business Entities

Business entities use:

- Title Case
- Singular nouns

Examples:

Customer

Vehicle

Driver

Vehicle Registration

Insurance Policy

Avoid technical names such as:

tbl_customer

vehicle_master

policy_table

---

# 10. Canonical Schema Attributes

Canonical schema attribute names use:

- lowercase
- snake_case

Examples:

customer_identifier

full_name

date_of_birth

vehicle_identification_number

fuel_type

registration_date

Do not use:

camelCase

PascalCase

kebab-case

---

# 11. Controlled Vocabulary Values

Controlled vocabulary values use:

- Title Case
- Human-readable names

Examples:

Aggregate Root

Reference Entity

Sensitive Personal

AI Generated

Reference

Derived

Avoid internal codes as displayed values.

---

# 12. Enumerations

Enumeration values should be:

- Singular
- Human-readable
- Business-oriented

Examples:

Male

Female

Other

Petrol

Diesel

Electric

Automatic

Manual

Do not abbreviate unless the abbreviation is the accepted business term.

Examples:

ABS

ADAS

GST

VIN

---

# 13. Abbreviations

Use abbreviations only when they are industry-standard.

Examples:

VIN

IDV

ABS

ADAS

GST

IRDAI

Avoid creating repository-specific abbreviations.

---

# 14. Reserved Words

The following names have reserved meanings within the repository:

Customer

Driver

Vehicle

Policy

Coverage

Claim

Repair

Reference Data

Ontology

Taxonomy

Knowledge Graph

Business Rules

These names should not be reused with different meanings.

---

# 15. Naming Checklist

Before introducing a new name, verify:

- Is the name business-friendly?
- Is it singular?
- Is it unambiguous?
- Does another concept already use this name?
- Does it follow the repository naming rules?
- Will it remain meaningful in future versions?

---

# 16. Revision History

| Version | Date | Author | Description |
|---------|------|--------|-------------|
| 1.0.0 | July 2026 | InsureAI Core Team | Initial repository naming standard. |
