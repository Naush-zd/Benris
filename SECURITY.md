# Security Policy

## Supported Versions

Benris is in active early development. Security fixes are applied to the
`main` branch.

| Version | Supported          |
| ------- | ------------------ |
| `main`  | :white_check_mark: |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, report them privately via one of:

- GitHub's [private vulnerability reporting](https://github.com/Naush-zd/Benris/security/advisories/new)
- A direct message to the maintainer

Please include:

- A description of the vulnerability and its impact
- Steps to reproduce (proof of concept if possible)
- Any suggested remediation

You can expect an initial response within a few days. We'll keep you updated on
the fix and coordinate disclosure once a patch is available.

## Scope & handling of secrets

Benris talks to third-party model providers (Groq, Anthropic) using API keys
loaded from a git-ignored `.env` file. If you discover a path where a key,
token, or other secret could leak into logs, the event stream, or the UI,
please treat it as a security report and disclose it privately.

Thank you for helping keep Benris and its users safe.
