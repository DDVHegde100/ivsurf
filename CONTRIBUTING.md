# Contributing

Thanks for your interest in IVSURF. This project is a research platform — contributions should keep the codebase honest, testable, and focused on opening volatility + swing research.

## Getting Started

```bash
git clone https://github.com/DDVHegde100/ivsurf.git
cd ivsurf
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,api]"
pytest
```

## Development Workflow

1. Create a branch from `main`
2. Make focused changes — prefer small PRs over large refactors
3. Add or update tests for engine logic
4. Run `pytest` and `ruff check .` before opening a PR
5. Open a PR with a clear summary and test plan

## Code Organization

| Directory | Put code here when… |
|-----------|---------------------|
| `engine/` | Business logic, data fetching, signals, backtests |
| `app/` | Streamlit UI components and CSS only |
| `api/` | HTTP route handlers (thin wrappers over `engine/`) |
| `scripts/` | Entry points and legacy terminal shell |
| `tests/` | pytest unit and integration tests |

**Rule:** Do not add trading logic to Streamlit scripts. Call `engine/` instead.

## Testing

```bash
pytest                          # unit tests (default)
pytest -m integration           # live market data (needs network)
pytest tests/test_api.py        # API routes only
```

Mark network-dependent tests with `@pytest.mark.integration`.

## Style

- Match existing naming and import style in the file you edit
- Type hints on new public functions
- No new optional dependencies without updating `pyproject.toml` extras
- Comments only for non-obvious logic

## Pull Request Guidelines

- One logical change per PR when possible
- Include test plan in PR description
- Do not commit secrets, `.env`, or `data/` artifacts
- Update docs if you change architecture or deployment steps

## Reporting Issues

Include:

- Python version
- Steps to reproduce
- Expected vs actual behavior
- Relevant logs or screenshots

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
