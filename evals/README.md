# Evaluation Framework

This directory contains the evaluation framework for the Production GenAI MLOps Platform.

## Purpose

The evaluation suite verifies LLM response quality before production deployment.

## Evaluation Categories

- General conversation
- Coding
- Azure
- Reasoning
- Edge cases
- Safety

## Goal

Eventually, GitHub Actions will run these evaluations automatically after deploying to staging. If the quality score falls below the configured threshold, the production deployment will be blocked.

This evaluation framework is designed to demonstrate production-oriented GenAI MLOps practices.