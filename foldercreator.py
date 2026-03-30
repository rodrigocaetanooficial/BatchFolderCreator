import os
import re
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime

parsed_lines, last_created_folders = [], []

def sanitize_path(name):
    s = re.sub(r'[:*?"<>|\r\n\t]', '', name)
    while '..' in s: s = s.replace('..', '.')
    return s.strip()

def is_safe(base, tgt):
    try: return os.path.abspath(tgt).startswith(os.path.abspath(base))
    except Exception: return False

def rep_vars(t):
    n = datetime.now()
    for k, v in [('{YYYY}', '%Y'), ('{YY}', '%y'), ('{MM}', '%m'), ('{DD}', '%d'), ('{HH}', '%H'), ('{MIN}', '%M')]:
        t = t.replace(k, n.strftime(v))
    return t

def parse_import(fp):
    global parsed_lines
    parsed_lines = []
    try:
        with open(fp, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line: continue
                if fp.lower().endswith('.csv'):
                    parts = re.split(r'[,;]', line)
                    if parts: line = parts[0].strip()
                    else: continue
                if line: parsed_lines.append(line)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to read file:\n{e}")

def choose_file():
    fp = filedialog.askopenfilename(filetypes=[("Text & CSV", "*.txt *.csv"), ("All Files", "*.*")])
    if fp:
        file_path_var.set(os.path.basename(fp))
        parse_import(fp)
        update_ui()

def choose_folder():
    f = filedialog.askdirectory()
    if f:
        entry_folder.delete(0, tk.END)
        entry_folder.insert(0, f)
        update_ui()

def show_vars_help():
    msg = (
        "You can use dynamic tags to automatically inject the current date or time "
        "into your folder names:\n\n"
        "• {YYYY} - 4-digit Year (e.g., 2024)\n"
        "• {YY}   - 2-digit Year (e.g., 24)\n"
        "• {MM}   - Month (e.g., 03)\n"
        "• {DD}   - Day of the month (e.g., 29)\n"
        "• {HH}   - Hours\n"
        "• {MIN}  - Minutes\n\n"
        "Example: 'Project_{YYYY}-{MM}' becomes 'Project_2024-03'"
    )
    messagebox.showinfo("Dynamic Date/Time Variables", msg)

def update_ui(*_):
    folder = entry_folder.get().strip()
    try: mode = nb.index("current")
    except Exception: mode = 0
    count = 0
    preview = "—"

    if mode == 0:
        naming_frame.pack(fill="x", pady=(0, 15), before=info_frame)
        s_prefix = sanitize_path(rep_vars(entry_prefix.get()))
        s_suffix = sanitize_path(rep_vars(entry_suffix.get()))
        pad = var_padding.get()
        try:
            strt = int(entry_start.get().strip())
            end = int(entry_end.get().strip())
            step = max(1, int(var_step.get()))
            if strt <= end: count = len(range(strt, end + 1, step))
            preview = f"{s_prefix}{str(strt).zfill(pad) if pad>0 else str(strt)}{s_suffix}"
        except ValueError: pass
    else:
        naming_frame.pack_forget()
        count = len(parsed_lines)
        if count > 0: preview = sanitize_path(rep_vars(parsed_lines[0]))

    lbl_count.config(text=f"{count} folder{'s' if count!=1 else ''} will be created")
    lbl_count.config(foreground="#666666" if count <= 10000 else "#d9534f")
    lbl_preview.config(text=f"Preview: {preview}")

    valid = bool(folder) and os.path.isdir(folder) and count > 0 and count <= 10000
    btn_create.state(["!disabled"] if valid else ["disabled"])
    btn_undo.state(["!disabled"] if last_created_folders else ["disabled"])

def undo_last():
    global last_created_folders
    if not last_created_folders: return
    if not messagebox.askyesno("Undo", f"Undo the creation of the last {len(last_created_folders)} folder(s)?\n\nOnly empty folders will be deleted to prevent data loss."): return
        
    deleted, not_empty = 0, 0
    for p in sorted(last_created_folders, key=lambda x: x.count(os.sep), reverse=True):
        if os.path.exists(p):
            try:
                if not os.listdir(p):
                    os.rmdir(p)
                    deleted += 1
                else: not_empty += 1
            except Exception: pass
                
    m = f"✔ {deleted} empty folders removed."
    if not_empty > 0: m += f"\n⚠ {not_empty} folders kept (they already contain files/subfolders)."
    messagebox.showinfo("Undo Result", m)
    last_created_folders.clear()
    update_ui()

def create_folders():
    global last_created_folders
    folder = entry_folder.get().strip()
    mode = nb.index("current")
    paths = []

    if mode == 0:
        s_prefix = sanitize_path(rep_vars(entry_prefix.get()))
        s_suffix = sanitize_path(rep_vars(entry_suffix.get()))
        pad = var_padding.get()
        try:
            strt = int(entry_start.get().strip())
            end = int(entry_end.get().strip())
            step = max(1, int(var_step.get()))
            if strt > end: return messagebox.showerror("Error", "Start must be <= End.")
            for i in range(strt, end + 1, step):
                paths.append(f"{s_prefix}{str(i).zfill(pad) if pad>0 else str(i)}{s_suffix}")
        except ValueError: return messagebox.showerror("Error", "Invalid numbers.")
    else:
        if not parsed_lines: return messagebox.showerror("Error", "No file / empty file selected.")
        for line in parsed_lines: paths.append(sanitize_path(rep_vars(line)))

    if len(paths) > 10000: return messagebox.showwarning("Error", "Limit of 10,000 folders exceeded.")

    created, skipped, newly = 0, 0, []
    for rel in paths:
        rel = rel.replace('/', os.sep).replace('\\', os.sep)
        tgt = os.path.abspath(os.path.join(folder, rel))
        if not is_safe(folder, tgt): return messagebox.showerror("Error", f"Path traversal blocked: {rel}")
        try:
            if not os.path.exists(tgt):
                os.makedirs(tgt)
                newly.append(tgt)
                created += 1
            else: skipped += 1
        except Exception as e:
            if not messagebox.askyesno("Error", f"Failed: {rel}\n{e}\n\nContinue?"): break
                
    last_created_folders = newly
    m = f"✔ {created} folders created."
    if skipped: m += f"\n⚠ {skipped} skipped."
    messagebox.showinfo("Done", m)
    update_ui()

# UI Setup
root = tk.Tk()
root.title("Batch Folder Creator")
root.geometry("520x480")
root.resizable(False, False)

style = ttk.Style(root)
style.theme_use("vista" if "vista" in style.theme_names() else "clam")

style.configure("TButton", font=("Segoe UI", 9), padding=5)
style.configure("Header.TLabel", font=("Segoe UI", 16, "bold"), foreground="#2C3E50")
style.configure("Sub.TLabel", font=("Segoe UI", 9), foreground="#7F8C8D")
style.configure("Title.TLabel", font=("Segoe UI", 9, "bold"), foreground="#34495E")

main_frame = tk.Frame(root, bg="#F8F9FA", padx=20, pady=15)
main_frame.pack(fill="both", expand=True)

# Header
header_frame = tk.Frame(main_frame, bg="#F8F9FA")
header_frame.pack(fill="x", pady=(0, 15))
ttk.Label(header_frame, text="📁 Batch Folder Creator", style="Header.TLabel", background="#F8F9FA").pack(anchor="w")
ttk.Label(header_frame, text="Generate dozens of folders instantly and safely.", style="Sub.TLabel", background="#F8F9FA").pack(anchor="w")

# Target Folder
tf_frame = tk.Frame(main_frame, bg="#F8F9FA")
tf_frame.pack(fill="x", pady=(0, 15))
ttk.Label(tf_frame, text="Target Directory", style="Title.TLabel", background="#F8F9FA").pack(anchor="w", pady=(0, 5))
f_entry_frame = tk.Frame(tf_frame, bg="#F8F9FA")
f_entry_frame.pack(fill="x")
entry_folder = ttk.Entry(f_entry_frame)
entry_folder.pack(side="left", fill="x", expand=True, padx=(0, 10))
entry_folder.bind("<KeyRelease>", update_ui)
ttk.Button(f_entry_frame, text="📂 Browse...", command=choose_folder, width=12).pack(side="right")

# Notebook
nb = ttk.Notebook(main_frame)
nb.pack(fill="x", pady=(0, 15))
nb.bind("<<NotebookTabChanged>>", update_ui)

# -- Tab 1
tab_range = ttk.Frame(nb, padding=15)
nb.add(tab_range, text="🔢 Number Range")
ttk.Label(tab_range, text="Start:").grid(row=0, column=0, sticky="w")
entry_start = ttk.Entry(tab_range, width=8); entry_start.grid(row=0, column=1, padx=(5, 15))
entry_start.bind("<KeyRelease>", update_ui)
ttk.Label(tab_range, text="End:").grid(row=0, column=2, sticky="w")
entry_end = ttk.Entry(tab_range, width=8); entry_end.grid(row=0, column=3, padx=(5, 15))
entry_end.bind("<KeyRelease>", update_ui)
ttk.Label(tab_range, text="Step:").grid(row=1, column=0, sticky="w", pady=10)
var_step = tk.IntVar(value=1)
spin_step = ttk.Spinbox(tab_range, from_=1, to=9999, width=7, textvariable=var_step, command=update_ui)
spin_step.grid(row=1, column=1, padx=(5, 15))
spin_step.bind("<KeyRelease>", update_ui)
ttk.Label(tab_range, text="Zero-pad:").grid(row=1, column=2, sticky="w")
var_padding = tk.IntVar(value=0)
spin_padding = ttk.Spinbox(tab_range, from_=0, to=6, width=7, textvariable=var_padding, command=update_ui)
spin_padding.grid(row=1, column=3, padx=(5, 15))
spin_padding.bind("<KeyRelease>", update_ui)

# -- Tab 2
tab_file = ttk.Frame(nb, padding=15)
nb.add(tab_file, text="📄 Import File")
ttk.Label(tab_file, text="Create nested folders from a .txt or .csv file.").pack(anchor="w", pady=(0, 10))
btn_file = ttk.Button(tab_file, text="📄 Select File...", command=choose_file)
btn_file.pack(side="left", padx=(0, 15))
file_path_var = tk.StringVar(value="No file selected")
ttk.Label(tab_file, textvariable=file_path_var, font=("Segoe UI", 9, "italic")).pack(side="left")

# Naming Options (Toggleable)
naming_frame = tk.Frame(main_frame, bg="#F8F9FA")
naming_frame.pack(fill="x", pady=(0, 15))
ttk.Label(naming_frame, text="Folder Naming", style="Title.TLabel", background="#F8F9FA").grid(row=0, column=0, columnspan=5, sticky="w", pady=(0, 5))
ttk.Label(naming_frame, text="Prefix:", background="#F8F9FA").grid(row=1, column=0, sticky="w")
entry_prefix = ttk.Entry(naming_frame, width=15); entry_prefix.grid(row=1, column=1, padx=(5, 10))
entry_prefix.bind("<KeyRelease>", update_ui)
ttk.Label(naming_frame, text="Suffix:", background="#F8F9FA").grid(row=1, column=2, sticky="w")
entry_suffix = ttk.Entry(naming_frame, width=15); entry_suffix.grid(row=1, column=3, padx=(5, 0))
entry_suffix.bind("<KeyRelease>", update_ui)

btn_vars_help = ttk.Button(naming_frame, text="❓", width=3, command=show_vars_help)
btn_vars_help.grid(row=1, column=4, padx=(5, 0))

ttk.Label(naming_frame, text="💡 Tip: Click the [?] button for date variables", font=("Segoe UI", 8), foreground="#95A5A6", background="#F8F9FA").grid(row=2, column=0, columnspan=5, sticky="w", pady=(5, 0))


# Preview & Count
info_frame = tk.Frame(main_frame, bg="#E8ECEF", padx=10, pady=8, highlightbackground="#D5D8DC", highlightthickness=1)
info_frame.pack(fill="x", pady=(0, 15))
lbl_preview = tk.Label(info_frame, text="Preview: —", font=("Consolas", 9), fg="#2980B9", bg="#E8ECEF")
lbl_preview.pack(side="left")
lbl_count = tk.Label(info_frame, text="0 folders will be created", font=("Segoe UI", 9, "bold"), fg="#7F8C8D", bg="#E8ECEF")
lbl_count.pack(side="right")

# Actions
action_frame = tk.Frame(main_frame, bg="#F8F9FA")
action_frame.pack(fill="x", pady=(5, 0))
btn_create = ttk.Button(action_frame, text="▶ Create Folders", command=create_folders, width=20, style="TButton")
btn_create.pack(side="left", padx=(0, 10))
btn_create.state(["disabled"])
btn_undo = ttk.Button(action_frame, text="↩ Undo Last Batch", command=undo_last, width=20, style="TButton")
btn_undo.pack(side="right")
btn_undo.state(["disabled"])

root.mainloop()
