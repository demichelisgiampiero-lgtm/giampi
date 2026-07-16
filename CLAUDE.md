# CLAUDE.md

Guidance for Claude Code (and other AI assistants) working in this repository.

## Overview

This repository is configured for use with [Claude Code](https://claude.com/claude-code).
It currently serves as a Claude Code workspace rather than a conventional
application codebase.

## Claude Code Configuration

Project-level configuration lives in `.claude/`:

- `.claude/settings.json` — registers the `thedotmack/claude-mem` marketplace
  and enables the [`claude-mem`](https://github.com/thedotmack/claude-mem)
  plugin at project scope. This plugin provides persistent session memory
  across Claude Code sessions.

## Conventions

- Keep Claude Code configuration under `.claude/`.
- Document any new tooling, scripts, or project structure in this file as the
  repository grows, so future sessions have accurate context.
- Prefer small, well-described commits.
