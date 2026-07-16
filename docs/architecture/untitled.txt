# Knowledge Engine Architecture

## Status

**Frozen Architecture**

Version: 1.0

---

# Purpose

The Knowledge Engine is responsible for transforming the repository stored under

knowledge/

into an executable runtime representation that can be consumed by every subsystem
inside the Enterprise AI Platform.

The Knowledge Engine is not responsible for reasoning, retrieval or graph
algorithms.

Its responsibility is to discover, validate, organize and expose knowledge.

---

# Design Principles

The Knowledge Engine is

- Repository Driven
- Metadata Aware
- Domain Oriented
- Hierarchical
- Immutable at Runtime
- Independent of Storage Format

The runtime never directly accesses CSV files.

Applications never directly access files.

Everything flows through the Knowledge Engine.

---

# High Level Architecture

Repository

↓

Knowledge Repository Loader

↓

Knowledge Repository

↓

Knowledge Registry

↓

Knowledge Service

↓

Applications

↓

Agents

↓

Workflow Engine

↓

Prompt Engine

↓

Knowledge Graph

---

# Repository Layout

knowledge/

contains multiple domains.

Example

knowledge/

policy/

customer/

vehicle/

claims/

platform/

Each directory is considered one knowledge domain.

A domain may contain subdomains.

---

# Runtime Model

KnowledgeRepository

contains

multiple KnowledgeDomain objects.

KnowledgeDomain

contains

subdomains

assets

KnowledgeAsset

represents one logical knowledge object.

The storage format is irrelevant.

---

# Runtime Object Model

KnowledgeRepository

domains

↓

KnowledgeDomain

name

subdomains

assets

↓

KnowledgeAsset

name

asset_type

path

metadata

---

# Asset Types

Examples include

schema

catalog

glossary

documentation

relationships

seed_data

ontology

workflow

prompt

graph

configuration

generic

The list may expand over time.

---

# Knowledge Repository

Responsibilities

Discover domains

Maintain hierarchy

Provide domain lookup

Provide asset lookup

Provide traversal

Never parse business logic.

---

# Knowledge Domain

Responsibilities

Represent one business domain

Maintain child domains

Maintain assets

Provide asset lookup

Provide traversal

---

# Knowledge Asset

Responsibilities

Represent one logical knowledge object.

It does not interpret the contents.

It only represents the existence of an asset.

---

# Loader Responsibilities

The Repository Loader

discovers

domains

subdomains

assets

constructs

KnowledgeRepository

No reasoning occurs during loading.

---

# Registry Responsibilities

The Knowledge Registry stores

KnowledgeRepository

instances.

It provides runtime lookup.

---

# Knowledge Service

The Knowledge Service is the public API exposed to the rest of the platform.

No application should communicate with the repository directly.

---

# Future Components

Graph Builder

Ontology Builder

Semantic Index

Hybrid Retrieval

Reasoning Engine

Agent Context Builder

Workflow Context Builder

Prompt Context Builder

These components consume the Knowledge Service.

They never access the repository directly.

---

# Design Rules

Repository is immutable after loading.

Knowledge objects are immutable.

Business logic belongs outside the Knowledge Engine.

Knowledge Engine never executes workflows.

Knowledge Engine never performs inference.

Knowledge Engine only models knowledge.

---

# Extension Points

Support additional storage formats

JSON

YAML

Parquet

DuckDB

SQL

Vector Databases

without changing the runtime API.

---

# Long Term Vision

The Knowledge Engine becomes the canonical source of knowledge for every subsystem
inside the Enterprise AI Platform.

Applications such as InsureAI interact only with the Knowledge Service and never
with the underlying repository.