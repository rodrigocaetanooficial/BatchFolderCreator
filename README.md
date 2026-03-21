# 📁 Batch Folder Creator

A lightweight desktop utility built with Python and Tkinter that lets you create batches of numbered folders instantly — with support for custom prefix, suffix, step interval, and zero-padding.

---

## ✨ Features

- **Batch creation** — generate dozens or hundreds of folders in one click
- **Custom prefix & suffix** — e.g. `Aula_1_Intro`, `Week_05_Review`
- **Step interval** — create every Nth folder (e.g. 1, 3, 5, 7…)
- **Zero-padding** — keep folder names neatly aligned (e.g. `01`, `02`, `10`)
- **Live preview** — see exactly what the folder name will look like before creating
- **Folder counter** — shows how many folders will be created based on your settings
- **Smart validation** — the Create button stays disabled until all inputs are valid
- **Graceful error handling** — if a folder fails, you can choose to skip or stop

---

## 🖼️ Interface

| Section | Description |
|---|---|
| **Target Folder** | Browse or type the destination directory |
| **Number Range** | Set Start, End, Step and Zero-pad digits |
| **Folder Naming** | Optional Prefix and Suffix for folder names |
| **Preview bar** | Shows a real-time example of the folder name |

---

## 🚀 Getting Started

### Requirements

- Python 3.8 or higher
- `tkinter` (included with standard Python on Windows/macOS)

### Run

```bash
python foldercreator.py
```

No dependencies to install — it uses only the Python standard library.

---

## 📖 Usage Example

| Field | Value |
|---|---|
| Target Folder | `C:\Users\You\Documents` |
| Start | `1` |
| End | `10` |
| Step | `2` |
| Zero-pad | `2` digits |
| Prefix | `Aula_` |
| Suffix | _(empty)_ |

**Result:** Creates folders `Aula_01`, `Aula_03`, `Aula_05`, `Aula_07`, `Aula_09`

---

## 📄 License

MIT License — free to use, modify, and distribute.
