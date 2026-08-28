# Contributing to 0xPDFForge

Thanks for your interest!

## Ground Rules

- Keep analysis **deterministic and evidence-based**. No hallucination.
- Every new detector must have a confidence level (`confirmed`/`detected`/`inferred`).
- Never print secrets verbatim — always redact with `***`.
- Graceful degradation: one analyzer failing must not crash the pipeline.

## Adding a Language / Framework Detector

1. Add entry to `analyzer/config.py` (`EXT_LANG`) or `analyzer/detectors/framework.py` (`RULES`).
2. Provide evidence strings — e.g., `config:vite.config.js`, `dependency:react@^18`, `import:from ["']react["']`.
3. Add tests in `tests/test_detectors.py`.
4. Run `pytest` and ensure the new detection does not produce false positives on `examples/sample-project`.

## Adding a Template

1. Edit `templates/definitions.py` — add a new dict with unique `id`, `name`, `category`, `colors`, `fonts`, `spacing`, `cover_style`, `header_style`.
2. If you introduce a new `cover_style` or `header_style`, add a branch in `pdf/engine.py` `_cover_elements` and `_section_title` / `_header_footer`.
3. Verify `test_template_count` and that `generate_pdf` works for the new template on all project fixtures.

## Development

```bash
pip install -r requirements.txt
python -m uvicorn backend.app:app --reload  # http://127.0.0.1:8000
pytest -v
```

## Security

If you find a bypass in ZIP validation (traversal, bomb, symlink, etc.), please open a private security advisory instead of a public issue.

## Code Style

- Keep functions small and typed where practical.
- Avoid mixing analysis logic into `pdf/engine.py` — keep `analyzer/` and `pdf/` separated.
- Frontend: vanilla JS, no build step; keep accessibility (focus-visible, keyboard navigation) intact.
