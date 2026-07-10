# InsureAI Identifier Conventions

**Document Version:** 1.0.0  
**Status:** Frozen (V1 Standard)  
**Knowledge Standard Version:** 1.0.0  
**Project:** InsureAI  
**Owner:** Knowledge Engineering Team  
**Created On:** July 2026  
**Last Updated:** July 2026

---

# 1. Purpose

This document defines the identifier standards used throughout the InsureAI Knowledge Repository.

Identifiers uniquely distinguish repository artifacts and business objects while ensuring consistency, traceability, and long-term maintainability.

These conventions apply to every business domain and shared artifact.

---

# 2. Design Principles

Identifiers must be:

- Unique.
- Stable.
- Immutable.
- Human-readable.
- Technology-independent.
- Never reused.
- Never reassigned.

Identifiers are repository metadata and must not encode business logic.

---

# 3. General Identifier Format

Repository identifiers follow the format:

PREFIX-DOMAIN-NUMERIC_ID

Examples:

```
GLOSS-CUST-000001
ENT-VEH-000014
SCH-INS-000023
```

Numeric identifiers are zero-padded to six digits.

---

# 4. Identifier Prefixes

| Prefix | Artifact |
|---------|----------|
| DOM | Business Domain |
| GLOSS | Business Concept |
| ENT | Business Entity |
| SCH | Canonical Schema |
| TAX | Taxonomy |
| ONT | Ontology |
| RULE | Business Rule |
| REL | Ontology Relationship |
| REF | Reference Data |
| DOC | Documentation Artifact |

Future prefixes may be added in later versions without changing existing identifiers.

---

# 5. Domain Codes

Each business domain owns a unique domain code.

| Domain | Code |
|---------|------|
| Customer | CUST |
| Driver | DRVR |
| Vehicle | VEH |
| Insurance | INS |
| Coverage | COV |
| Claims | CLM |
| Repair | REP |
| Geography | GEO |
| Regulatory | REG |
| Documents | DOC |
| Reference Data | REF |
| Intelligence | INT |
| Platform | PLT |

Domain codes are immutable.

---

# 6. Identifier Allocation

Identifiers are allocated sequentially within each artifact type.

Example:

```
GLOSS-CUST-000001
GLOSS-CUST-000002
GLOSS-CUST-000003
```

Deleted identifiers are never reused.

---

# 7. Business Identifiers

Business identifiers (such as Customer Identifier or Vehicle Identifier) are business attributes defined within canonical schemas.

Repository identifiers and business identifiers serve different purposes.

Example:

Repository Identifier

```
ENT-CUST-000001
```

Business Identifier

```
CUS-102483
```

---

# 8. Identifier Lifecycle

Identifiers remain unchanged throughout the lifecycle of an artifact.

Updating definitions, descriptions, or metadata must not change the identifier.

Only deletion of the artifact retires an identifier.

Retired identifiers are never reassigned.

---

# 9. Cross References

Artifacts reference each other using identifiers.

Examples:

Glossary → Entity

```
GLOSS-CUST-000001
```

Entity → Canonical Schema

```
ENT-CUST-000001
```

Business Rules → Concepts

```
RULE-INS-000001
```

Cross-references must always use canonical identifiers.

---

# 10. Reserved Identifier Ranges

Version 1 reserves the following ranges.

000001 – 099999 : Standard repository artifacts

100000 – 199999 : Future expansion

200000 – 299999 : Generated artifacts

Additional ranges may be reserved in future versions.

---

# 11. Governance Rules

- Never modify an existing identifier.
- Never recycle deleted identifiers.
- Never encode business meaning into numeric identifiers.
- Never use database primary keys as repository identifiers.
- Never use UUIDs inside repository artifacts.

---

# 12. Revision History

| Version | Date | Author | Description |
|---------|------|--------|-------------|
| 1.0.0 | July 2026 | InsureAI Core Team | Initial identifier convention standard. |
