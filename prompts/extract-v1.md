# Extraction Prompt v1

> This is a placeholder for Plan 2 (Build Pipeline). The extraction prompt template
> will be defined here and versioned alongside schema_version 1.x.

## Purpose

This prompt is used by `mindset build` to instruct an LLM to extract
structured character data from source documents into the Mindset Schema format.

## Schema Version

This prompt targets schema_version `1.0`.

## Prompt Template

*(To be implemented in Plan 2)*

The extraction prompt will instruct the LLM to:
1. Read all source files listed in `sources.yaml`
2. Fill each schema field based strictly on documented evidence
3. Set `confidence` values per entry (0.0–1.0) based on directness of evidence
4. Leave fields empty rather than speculate

## Versioning

Changes to this prompt file increment the prompt version.
A schema 1.x pack must be built with extract-v1.md.
