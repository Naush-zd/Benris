# Contributing to Benris

First off — thank you for taking the time to contribute! 🎙️🧠
Benris is a community-friendly project and every bug report, idea, and pull
request is genuinely appreciated.

## Ways to contribute

- 🐛 **Report bugs** — open an [issue](https://github.com/Naush-zd/Benris/issues) with steps to reproduce.
- 💡 **Suggest features** — describe the use case, not just the solution.
- 📖 **Improve docs** — typos, clarifications, and examples are all welcome.
- 🔧 **Send code** — fix a bug or build a feature (see below).

## Development setup

> Requirements: macOS, [`uv`](https://github.com/astral-sh/uv), Python 3.13+.
> Node 20+ is needed for the web dashboard in `web/`.

```sh
git clone https://github.com/Naush-zd/Benris.git
cd Benris
uv sync                     # install dependencies
cp .env.example .env        # add your keys
uv run python jarvis.py     # run the desktop app
uv run agentctl start       # run the control plane
uv run pytest               # run the test suite
```

Working on the web dashboard:

```sh
cd web
npm install
npm run dev                 # http://localhost:3000
npm run lint
```

## Pull request workflow

1. **Fork** the repo and create a branch off `main`:
   `git checkout -b feat/short-description`
2. Make focused changes — keep each PR to one logical concern.
3. **Validate** before pushing:
   - Python: `uv run pytest`, and make sure the app still starts.
   - Web: `cd web && npm run lint` passes.
4. Write a clear commit message and PR description — what changed and *why*.
5. Open the PR against `main` and link any related issue.

## Coding guidelines

- **Match the surrounding style** — naming, structure, and comment density.
- **Python**: type hints, small focused functions, no secrets in code.
- **Web (`web/`)**: Next.js + TypeScript; keep components focused and typed.
- **Keep secrets out of git** — anything sensitive goes in `.env` (git-ignored).
- Prefer the smallest change that correctly solves the problem.

## Reporting security issues

Please do **not** open a public issue for security vulnerabilities.
See [SECURITY.md](SECURITY.md) for responsible disclosure.

## Code of Conduct

By participating, you agree to uphold our
[Code of Conduct](CODE_OF_CONDUCT.md).

---

Happy hacking! If anything here is unclear, open an issue and we'll improve it.
