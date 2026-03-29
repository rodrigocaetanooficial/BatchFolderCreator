import os
import re
import tkinter as tk
from tkinter import ttk, filedialog, messagebox


# ──────────────────────────────────────────────
#  Helpers & Security
# ──────────────────────────────────────────────

def sanitize_name(name):
    """Remove characters not allowed in filenames and prevent path traversal."""
    # Remove Windows reserved characters: \ / : * ? " < > |
    # Also remove newline characters and other control codes
    sanitized = re.sub(r'[\\/:*?"<>|\r\n\t]', '', name)
    # Prevent traversal by making sure no '..' sequences remain (after sanitizing other symbols)
    while '..' in sanitized:
        sanitized = sanitized.replace('..', '.')
    return sanitized.strip()


def is_path_safe(base_dir, target_path):
    """Ensure that the target_path is actually within the base_dir."""
    try:
        abs_base = os.path.abspath(base_dir)
        abs_target = os.path.abspath(target_path)
        return abs_target.startswith(abs_base)
    except (ValueError, OSError):
        return False


def get_preview_name():
    """Return an example folder name based on current field values."""
    prefix = sanitize_name(entry_prefix.get())
    suffix = sanitize_name(entry_suffix.get())
    padding = var_padding.get()

    try:
        start = int(entry_start.get().strip())
    except ValueError:
        start = 1

    num_str = str(start).zfill(padding) if padding > 0 else str(start)
    return f"{prefix}{num_str}{suffix}"


def update_ui(*_):
    """Refresh counter, preview label and button state on any field change."""
    prefix = entry_prefix.get()
    suffix = entry_suffix.get()
    folder = entry_folder.get().strip()
    padding = var_padding.get()

    # ── preview ──
    try:
        start = int(entry_start.get().strip())
        num_str = str(start).zfill(padding) if padding > 0 else str(start)
        p = sanitize_name(prefix)
        s = sanitize_name(suffix)
        preview_name = f"{p}{num_str}{s}"
    except ValueError:
        preview_name = "—"

    lbl_preview.config(text=f"Preview:  {preview_name}")

    # ── counter ──
    try:
        start = int(entry_start.get().strip())
        end   = int(entry_end.get().strip())
        step  = max(1, int(var_step.get()))
        count = max(0, len(range(start, end + 1, step))) if end >= start else 0
        lbl_count.config(text=f"{count} folder{'s' if count != 1 else ''} will be created")
    except ValueError:
        lbl_count.config(text="")

    # ── button state ──
    valid_folder  = bool(folder) and os.path.isdir(folder)
    valid_numbers = False
    count = 0
    try:
        s, e = int(entry_start.get().strip()), int(entry_end.get().strip())
        step_val = int(var_step.get())
        if s <= e and step_val >= 1:
             valid_numbers = True
             count = len(range(s, e + 1, step_val))
    except (ValueError, TypeError):
        pass

    # Security & DoS Limit: Max 10k folders
    limit_ok = count <= 10000
    btn_create.state(["!disabled"] if valid_folder and valid_numbers and limit_ok else ["disabled"])
    
    if not limit_ok:
        lbl_count.config(foreground="red")
    else:
        lbl_count.config(foreground="gray")


def choose_folder():
    folder = filedialog.askdirectory()
    if folder:
        entry_folder.delete(0, tk.END)
        entry_folder.insert(0, folder)
        update_ui()


def create_folders():
    folder  = entry_folder.get().strip()
    prefix  = entry_prefix.get()
    suffix  = entry_suffix.get()
    padding = var_padding.get()

    try:
        start_num = int(entry_start.get().strip())
        end_num   = int(entry_end.get().strip())
        step_num  = max(1, int(var_step.get()))
    except ValueError:
        messagebox.showerror("Invalid Input", "Start and End must be integers.")
        return

    if not folder or not os.path.isdir(folder):
        messagebox.showerror("Invalid Folder", "Please select a valid folder.")
        return

    if start_num > end_num:
        messagebox.showerror("Invalid Range", "Start must be ≤ End.")
        return

    created = 0
    skipped = 0
    
    # Pre-calculate count for security/DoS check
    total_to_create = len(range(start_num, end_num + 1, step_num))
    if total_to_create > 10000:
        messagebox.showwarning("Batch Limit", "To prevent system slowdown, you cannot create more than 10,000 folders at once.")
        return

    # Sanitize prefix/suffix at use time
    s_prefix = sanitize_name(prefix)
    s_suffix = sanitize_name(suffix)

    for i in range(start_num, end_num + 1, step_num):
        num_str     = str(i).zfill(padding) if padding > 0 else str(i)
        folder_name = f"{s_prefix}{num_str}{s_suffix}"
        new_path    = os.path.join(folder, folder_name)

        # Path Traversal Guard
        if not is_path_safe(folder, new_path):
            messagebox.showerror("Security Hazard", f"Path traversal detected: {folder_name}")
            return

        try:
            if not os.path.exists(new_path):
                os.makedirs(new_path)
                created += 1
            else:
                skipped += 1
        except Exception as e:
            if messagebox.askyesno(
                "Error",
                f"Failed to create: {folder_name}\n{e}\n\nContinue with remaining folders?"
            ):
                continue
            else:
                break

    msg = f"✔  {created} folder{'s' if created != 1 else ''} created successfully."
    if skipped:
        msg += f"\n⚠  {skipped} already existed and were skipped."
    messagebox.showinfo("Done", msg)


# ──────────────────────────────────────────────
#  Window
# ──────────────────────────────────────────────

root = tk.Tk()
root.title("Batch Folder Creator")
root.resizable(False, False)

# Use the native Windows theme
style = ttk.Style(root)
style.theme_use("vista")          # falls back to "winnative" or "clam" on older systems

# ── Separator style (subtle) ──
style.configure("Separator.TSeparator")

# ──────────────────────────────────────────────
#  Layout
# ──────────────────────────────────────────────

PAD = 12   # outer padding
GAP =  6   # inner gap

main_frame = ttk.Frame(root, padding=PAD)
main_frame.pack(fill="both", expand=True)

# ── Section: Target Folder ────────────────────
ttk.Label(main_frame, text="Target Folder", font=("Segoe UI", 9, "bold")).grid(
    row=0, column=0, columnspan=3, sticky="w", pady=(0, 2))

entry_folder = ttk.Entry(main_frame, width=52)
entry_folder.grid(row=1, column=0, columnspan=2, sticky="we", padx=(0, GAP))
entry_folder.bind("<KeyRelease>", update_ui)

btn_browse = ttk.Button(main_frame, text="Browse…", command=choose_folder, width=9)
btn_browse.grid(row=1, column=2, sticky="e")

ttk.Separator(main_frame, orient="horizontal").grid(
    row=2, column=0, columnspan=3, sticky="we", pady=(PAD, PAD // 2))

# ── Section: Number Range ─────────────────────
ttk.Label(main_frame, text="Number Range", font=("Segoe UI", 9, "bold")).grid(
    row=3, column=0, columnspan=3, sticky="w", pady=(0, 2))

range_frame = ttk.Frame(main_frame)
range_frame.grid(row=4, column=0, columnspan=3, sticky="we")

ttk.Label(range_frame, text="Start:").pack(side="left")
entry_start = ttk.Entry(range_frame, width=8)
entry_start.pack(side="left", padx=(4, 12))
entry_start.bind("<KeyRelease>", update_ui)

ttk.Label(range_frame, text="End:").pack(side="left")
entry_end = ttk.Entry(range_frame, width=8)
entry_end.pack(side="left", padx=(4, 12))
entry_end.bind("<KeyRelease>", update_ui)

ttk.Label(range_frame, text="Step:").pack(side="left")
var_step = tk.IntVar(value=1)
spin_step = ttk.Spinbox(range_frame, from_=1, to=9999, width=5,
                        textvariable=var_step, command=update_ui)
spin_step.pack(side="left", padx=(4, 12))
spin_step.bind("<KeyRelease>", update_ui)

ttk.Label(range_frame, text="Zero-pad to:").pack(side="left")
var_padding = tk.IntVar(value=0)
spin_padding = ttk.Spinbox(range_frame, from_=0, to=6, width=4,
                           textvariable=var_padding, command=update_ui)
spin_padding.pack(side="left", padx=(4, 0))
spin_padding.bind("<KeyRelease>", update_ui)
ttk.Label(range_frame, text="digits", foreground="gray").pack(side="left", padx=(4, 0))

ttk.Separator(main_frame, orient="horizontal").grid(
    row=5, column=0, columnspan=3, sticky="we", pady=(PAD, PAD // 2))

# ── Section: Naming ───────────────────────────
ttk.Label(main_frame, text="Folder Naming", font=("Segoe UI", 9, "bold")).grid(
    row=6, column=0, columnspan=3, sticky="w", pady=(0, 2))

naming_frame = ttk.Frame(main_frame)
naming_frame.grid(row=7, column=0, columnspan=3, sticky="we")

ttk.Label(naming_frame, text="Prefix:").pack(side="left")
entry_prefix = ttk.Entry(naming_frame, width=16)
entry_prefix.pack(side="left", padx=(4, 20))
entry_prefix.bind("<KeyRelease>", update_ui)

ttk.Label(naming_frame, text="Suffix:").pack(side="left")
entry_suffix = ttk.Entry(naming_frame, width=16)
entry_suffix.pack(side="left", padx=(4, 0))
entry_suffix.bind("<KeyRelease>", update_ui)

ttk.Separator(main_frame, orient="horizontal").grid(
    row=8, column=0, columnspan=3, sticky="we", pady=(PAD, PAD // 2))

# ── Info bar: preview + counter ──────────────
info_frame = ttk.Frame(main_frame)
info_frame.grid(row=9, column=0, columnspan=3, sticky="we", pady=(0, GAP))

lbl_preview = ttk.Label(info_frame, text="Preview:  —",
                         font=("Consolas", 9), foreground="#0055aa")
lbl_preview.pack(side="left")

lbl_count = ttk.Label(info_frame, text="", foreground="gray")
lbl_count.pack(side="right")

# ── Action button ─────────────────────────────
btn_create = ttk.Button(main_frame, text="Create Folders ▶",
                        command=create_folders, width=20)
btn_create.grid(row=10, column=0, columnspan=3, pady=(GAP, 0))
btn_create.state(["disabled"])   # enabled once inputs are valid

# ── Column weights ────────────────────────────
for col in range(3):
    main_frame.columnconfigure(col, weight=1)

root.mainloop()
