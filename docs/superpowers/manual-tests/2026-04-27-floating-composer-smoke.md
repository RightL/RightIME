# Floating Composer Manual Smoke Test

Date: 2026-04-27

## Setup

```bash
conda run -n part python -m pip install -e '.[desktop]'
export RIGHTIME_OPENAI_API_KEY='<key>'
export RIGHTIME_OPENAI_MODEL='<model>'
```

On macOS, grant Accessibility permission to the terminal or packaged app that runs `rightime-composer`.

## Run Without Global Hotkey

```bash
conda run -n part rightime-composer --no-hotkey
```

Expected:

- composer window opens
- typing pinyin in the input field works
- Return triggers conversion
- result preview shows one plain-text Chinese result
- Copy puts the result on the clipboard
- Accept copies the result and attempts paste
- paste failure remains visible and the result stays available

## Run With Global Hotkey

```bash
conda run -n part rightime-composer
```

Expected:

- app starts without showing the window
- pressing `<ctrl>+<alt>+space` opens the composer
- Escape hides the composer
