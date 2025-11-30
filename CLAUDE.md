# Project: photoroom-python

## Purpose
A modern, well-typed, dual sync/async **Python SDK** for the [PhotoRoom REST API](https://docs.photoroom.com), providing an ergonomic interface to:
- Remove backgrounds
- Edit and enhance images with AI-powered transformations
- Retrieve account details and quotas

The SDK should also serve as the foundation for a future command-line tool, **`photoroom-cli`**, enabling batch and interactive editing from the terminal.

---

## Stack & Environment
- **Language:** Python ≥3.9  
- **Dependencies:**
  - `httpx` — HTTP client (sync + async)
  - `python-dotenv` — optional env file loading
  - `pydantic` — for structured responses and type validation (optional)
  - `pytest` — testing framework
  - `black`, `isort`, `flake8` — formatting and linting
- **Packaging:** `pyproject.toml` (PEP 621, Poetry or setuptools)
- **License:** MIT (default unless overridden)

---

## Architecture Overview

photoroom/
  __init__.py
  client.py              # Unified entrypoint, manages auth, sync/async clients
  endpoints/
    __init__.py
    edit.py              # /v2/edit (Plus plan)
    remove_bg.py         # /v1/segment (Basic plan)
    account.py           # /v2/account
  exceptions.py          # Custom error classes
  utils.py               # Shared helpers
  types.py               # Typed response and request models (pydantic)
tests/
  test_client.py
  test_remove_bg.py
  test_edit.py
cli/
  __init__.py
  main.py                # photoroom-cli entrypoint (future milestone)

---

## Client Class Design

### `PhotoRoomClient`
Primary interface for all API operations.

client = PhotoRoomClient(api_key="...", async_mode=False)

# or via environment
# export PHOTOROOM_API_KEY=sk_live_...
client = PhotoRoomClient()

### Sync example
client.remove_background("photo.jpg", bg_color="white", output_file="out.png")
client.edit_image("photo.jpg", background_prompt="on a beach", export_format="png")
account = client.get_account()

### Async example
async with PhotoRoomClient(async_mode=True) as client:
    await client.remove_background("photo.jpg", output_file="async_out.png")

---

## Endpoints

### `/v1/segment` — Remove Background
**POST** `https://sdk.photoroom.com/v1/segment`
- Form fields:
  - `image_file` (binary, required)
  - `format` = png|jpg|webp (default png)
  - `channels` = rgba|alpha (default rgba)
  - `bg_color`, `size`, `crop`, `despill`
- Returns: binary PNG or JSON with base64 string.

### `/v2/edit` — Image Editing
**GET** (via `imageUrl`) and **POST** (via `imageFile`)
- Server: `https://image-api.photoroom.com`
- Parameters:
  - `removeBackground` (bool, default True)
  - `background.color`, `background.prompt`
  - `outputSize`, `padding`, `margin`, `scaling`
  - `export.format` (png, jpg, webp)
  - Optional: `templateId`, `beautify.mode`, `shadow.mode`, etc.
- Returns: binary image.

### `/v2/account` — Account Details
**GET** `https://image-api.photoroom.com/v2/account`
- Returns:
  { "plan": "Plus", "images": { "available": 87, "subscription": 100 } }

---

## Behavior & Features

- **Auth Handling:**
  - API key required
  - Use `PHOTOROOM_API_KEY` env fallback if not passed explicitly
  - Inject via header `X-Api-Key`

- **Dual sync/async design:**
  - Internal use of `httpx.Client` and `httpx.AsyncClient`
  - Common interface for all methods

- **Error Handling:**
  - Map common HTTP codes to specific exceptions:
    - `400 → PhotoRoomBadRequest`
    - `402 → PhotoRoomPaymentError`
    - `403 → PhotoRoomAuthError`
    - `500 → PhotoRoomServerError`
  - Provide helpful messages from JSON responses when available

- **Automatic Output Saving:**
  - If `output_file` is given, save binary result to disk
  - Else return raw bytes (or base64 str if JSON)

- **Extensible:**
  - Future support for:
    - `/v2/templates`
    - `/v2/render`
    - `/v2/batch` (if exposed)
    - CLI wrapper (`photoroom-cli`)

---

## Coding Practices & Style

- **Typing:** Use full Python type hints and PEP 561 compliance
- **Formatting:** `black`, `isort`, `flake8`
- **Testing:** Use `pytest`, with mocks for network calls (`respx`)
- **Docs:** Inline docstrings in Google style
- **Error resilience:** Handle both binary and JSON responses gracefully
- **Performance:** Use streaming for file uploads/downloads

---

## Example Usage

from photoroom import PhotoRoomClient

client = PhotoRoomClient()

# Remove background
client.remove_background(
    image_file="input.jpg",
    bg_color="white",
    output_file="output.png"
)

# Edit image
client.edit_image(
    image_file="input.jpg",
    background_prompt="on a minimalist white table",
    export_format="jpg",
    output_file="result.jpg"
)

# Get account info
print(client.get_account())

---

## CLI Preview (future milestone)
**Command name:** `photoroom-cli`

Example:
photoroom remove-bg input.jpg --bg-color white -o output.png
photoroom edit input.jpg --background-prompt "in a studio setting" -o out.webp
photoroom account

Uses `click` or `typer` for clean CLI UX. Wraps SDK methods.

---

## Definition of Done

A project version is considered **complete** when:

- ✅ `photoroom/` package includes:
  - `client.py` with dual sync/async support
  - Modular endpoint handlers
  - Exception hierarchy
  - Environment variable fallback for API key
- ✅ Tests for:
  - Background removal
  - Image editing
  - Auth + error handling
- ✅ Documentation includes examples for sync + async usage
- ✅ CLI spec stub present (`cli/main.py`)
- ✅ Code passes:
  - `black`, `isort`, `flake8`, `pytest`
  - 80%+ coverage

---

## Claude Code Deliverables

1. `/photoroom/__init__.py`  
2. `/photoroom/client.py`  
3. `/photoroom/endpoints/edit.py`  
4. `/photoroom/endpoints/remove_bg.py`  
5. `/photoroom/endpoints/account.py`  
6. `/photoroom/exceptions.py`  
7. `/photoroom/utils.py`  
8. `/tests/*.py`  
9. `/cli/main.py`  
10. `/pyproject.toml`, `/README.md`, `/LICENSE`

---

## Notes for Agent Builders

- Implement `/v2/edit` first as the primary endpoint.
- Include examples for GET (URL-based) and POST (file-based).
- Allow default output format `png`.
- Future-proof for new endpoints via clean modularization.
- Avoid writing to external dirs — output only under user-specified paths.
- Handle file saving with `pathlib.Path` and robust error checking.

---

**End of `CLAUDE.md`**
