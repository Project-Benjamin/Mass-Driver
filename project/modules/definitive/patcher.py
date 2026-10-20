"""Local Windows patcher for the independently registered retail campaign."""
from dataclasses import asdict
from datetime import datetime
import json
import hashlib
import os
from pathlib import Path
import queue
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from shared.project_registry import load_registry
from modules.definitive.build import RETAIL_SHA256, digest
from modules.definitive.options import Options

ROOT = Path(__file__).resolve().parents[2]
OPTIONS = ROOT / "modules/definitive/content/options.json"


def save_selection(options, root=ROOT):
    """Content-addressed selections cannot be replaced by another patcher window."""
    options.validate()
    payload = (json.dumps(asdict(options), sort_keys=True, indent=2) + "\n").encode("utf-8")
    directory = root / "modules/definitive/content/selections"
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / (hashlib.sha256(payload).hexdigest() + ".json")
    try:
        with path.open("xb") as stream:
            stream.write(payload)
    except FileExistsError:
        if path.read_bytes() != payload:
            raise ValueError("Existing selection file does not match its identity")
    return path.relative_to(root).as_posix()


def save_disc_paths(paths):
    """Accept only the audited base, retaining every unrelated local setting."""
    for disc, path in paths.items():
        if digest(path) != RETAIL_SHA256[disc]:
            raise ValueError(f"Disc {disc} is not the supported USA retail BIN")
    path = ROOT / "project.local.json"
    document = json.loads(path.read_text(encoding="utf-8-sig")) if path.exists() else {}
    for disc, source in paths.items():
        document.setdefault("sources", {})[f"retail_disc{disc}"] = {
            "path": str(source.resolve()), "sha256": RETAIL_SHA256[disc]}
    temporary = path.with_name(".definitive-local.tmp")
    with temporary.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(document, indent=2) + "\n")
    temporary.replace(path)


class Patcher:
    def __init__(self, window):
        self.window = window
        self.events = queue.Queue()
        self.busy = False
        self.controls = []
        self.log_lines = []
        self.details_window = None
        self.log = None
        self.output = None
        self.scale = max(1.0, float(window.tk.call("tk", "scaling")) / (96 / 72))
        self.colors = {"paper": "#F5F4F0", "ink": "#252C28", "muted": "#666D67",
                       "line": "#DADDD5", "accent": "#344C40", "hover": "#263C31",
                       "error": "#9C3832", "white": "#FFFFFF"}
        window.title("Xenogears — Definitive patcher")
        window.configure(background=self.colors["paper"])
        self.configure_styles()

        # One ordinary frame: every patch control is on the page at all times.
        self.page = ttk.Frame(window, padding=(self.px(24), self.px(18)))
        self.page.pack(fill="both", expand=True)
        header = ttk.Frame(self.page)
        header.pack(fill="x", pady=(0, self.px(14)))
        ttk.Label(header, text="Xenogears Definitive", style="Title.TLabel").pack(side="left")
        ttk.Button(header, text="Patch notes", style="Link.TButton",
                   command=lambda: self.open_path(ROOT / "docs/definitive/status.md")).pack(side="right")

        registry = load_registry(ROOT)
        self.paths = {}
        self.path_entries = {}
        for disc in (1, 2):
            row = ttk.Frame(self.page)
            row.pack(fill="x", pady=(0, self.px(8) if disc == 1 else 0))
            row.columnconfigure(1, weight=1)
            ttk.Label(row, text=f"Disc {disc}", width=6).grid(row=0, column=0, sticky="w")
            variable = tk.StringVar(value=registry["sources"][f"retail_disc{disc}"]["path"])
            self.paths[disc] = variable
            entry = ttk.Entry(row, textvariable=variable, width=12)
            entry.grid(row=0, column=1, sticky="ew", padx=(0, self.px(8)))
            entry.xview_moveto(1)
            self.path_entries[disc] = entry
            browse = ttk.Button(row, text="Browse…", command=lambda d=disc: self.browse(d))
            browse.grid(row=0, column=2)
            self.controls.extend((entry, browse))
            variable.trace_add("write", self.selection_changed)

        self.divider(self.page)
        options = ttk.Frame(self.page)
        options.pack(fill="x")
        options.columnconfigure((0, 1), weight=1, uniform="patch")
        defaults = asdict(Options.load(OPTIONS))
        self.flags = {}
        for index, (key, label) in enumerate((
            ("bug_fixes", "Bug fixes"),
            ("yellow_names", "Yellow names (partial)"),
            ("double_xp", "Double XP"),
        )):
            variable = tk.BooleanVar(value=defaults[key])
            self.flags[key] = variable
            check = ttk.Checkbutton(options, text=label, variable=variable, command=self.selection_changed)
            check.grid(row=index // 2, column=index % 2, sticky="w", pady=self.px(4))
            self.controls.append(check)
        self.encounters = tk.StringVar(value=defaults["encounters"])
        encounter = ttk.Checkbutton(options, text="No random encounters", variable=self.encounters,
                                    onvalue="none", offvalue="normal", command=self.selection_changed)
        encounter.grid(row=1, column=1, sticky="w", pady=self.px(4))
        self.controls.append(encounter)

        self.divider(self.page)
        self.create_footer()
        self.append("Choose USA retail BIN images and the patches to apply. Original images are kept.\n"
                    "HD export creates a separate emulator pack; it does not install it.\n"
                    "Patch notes list the available fixes, coverage and unfinished features.\n")
        self.poll_id = window.after(100, self.poll)
        window.protocol("WM_DELETE_WINDOW", self.close)

        # Use the actual requested height, including Windows text/DPI scaling.
        # The page cannot be shortened until its controls are clipped.
        window.update_idletasks()
        width = max(self.px(620), window.winfo_reqwidth())
        height = window.winfo_reqheight()
        window.geometry(f"{width}x{height}")
        window.minsize(width, height)
        window.resizable(True, False)

    def px(self, value):
        return round(value * self.scale)

    def configure_styles(self):
        style = ttk.Style(self.window)
        style.theme_use("clam")
        c = self.colors
        style.configure(".", background=c["paper"], foreground=c["ink"], font=("Segoe UI", 10))
        style.configure("TFrame", background=c["paper"])
        style.configure("TLabel", background=c["paper"])
        style.configure("Title.TLabel", font=("Segoe UI", 18), foreground=c["ink"])
        style.configure("Section.TLabel", font=("Segoe UI", 10, "bold"))
        style.configure("Muted.TLabel", foreground=c["muted"], font=("Segoe UI", 9))
        style.configure("Status.TLabel", foreground=c["ink"], font=("Segoe UI", 9))
        style.configure("Error.TLabel", foreground=c["error"], font=("Segoe UI", 9))
        style.configure("TSeparator", background=c["line"])
        style.configure("TButton", padding=(self.px(12), self.px(7)), relief="flat",
                        borderwidth=1, bordercolor=c["line"], lightcolor=c["line"],
                        darkcolor=c["line"], background=c["paper"], focuscolor=c["accent"])
        style.map("TButton", background=[("pressed", "#E2E5DD"), ("active", "#EBEDE6")],
                  foreground=[("disabled", "#81867F")],
                  bordercolor=[("focus", c["accent"])])
        style.configure("Primary.TButton", background=c["accent"], foreground=c["white"],
                        bordercolor=c["accent"], lightcolor=c["accent"], darkcolor=c["accent"],
                        font=("Segoe UI", 10, "bold"), padding=(self.px(14), self.px(8)),
                        focuscolor=c["white"])
        style.map("Primary.TButton", background=[("disabled", "#DADDD5"), ("pressed", c["hover"]),
                                                 ("active", c["hover"])],
                  foreground=[("disabled", "#656B65")],
                  bordercolor=[("disabled", "#DADDD5"), ("focus", c["hover"])])
        style.configure("Link.TButton", padding=(self.px(2), self.px(3)), borderwidth=0,
                        font=("Segoe UI", 9), foreground=c["muted"], focuscolor=c["accent"])
        style.map("Link.TButton", background=[("active", c["paper"])],
                  foreground=[("active", c["ink"]), ("focus", c["ink"])])
        style.configure("TEntry", padding=self.px(6), fieldbackground=c["white"],
                        bordercolor=c["line"], lightcolor=c["line"], darkcolor=c["line"],
                        insertcolor=c["ink"], selectbackground=c["accent"], selectforeground=c["white"])
        style.map("TEntry", bordercolor=[("focus", c["accent"])],
                  fieldbackground=[("disabled", "#ECEDE7")])
        for control in ("TCheckbutton", "TRadiobutton"):
            style.configure(control, background=c["paper"], focuscolor=c["accent"],
                            indicatorbackground=c["white"], indicatorforeground=c["accent"],
                            indicatormargin=(0, self.px(2), self.px(8), self.px(2)))
            style.map(control, background=[("active", c["paper"])],
                      foreground=[("disabled", "#81867F")])
        if "vista" in style.theme_names():
            # Retain familiar Windows check/radio marks inside the otherwise flat theme.
            for name in ("Checkbutton", "Radiobutton"):
                element = f"Native.{name}.indicator"
                style.element_create(element, "from", "vista", f"{name}.indicator")
                style.layout(f"T{name}", [(f"{name}.padding", {"sticky": "nswe", "children": [
                    (element, {"side": "left", "sticky": ""}),
                    (f"{name}.focus", {"side": "left", "sticky": "w", "children": [
                        (f"{name}.label", {"sticky": "nswe"})]})]})])
        style.configure("Horizontal.TProgressbar", background=c["accent"],
                        troughcolor=c["paper"], borderwidth=0, thickness=self.px(2))

    def divider(self, parent):
        ttk.Separator(parent).pack(fill="x", pady=self.px(12))

    def create_footer(self):
        self.status = tk.StringVar(value="Ready")
        self.status_label = ttk.Label(self.page, textvariable=self.status, style="Status.TLabel")
        self.status_label.pack(anchor="w", pady=(0, self.px(8)))
        self.progress_track = ttk.Frame(self.page, height=self.px(3))
        self.progress_track.pack(fill="x", pady=(0, self.px(8)))
        self.progress = ttk.Progressbar(self.progress_track, mode="indeterminate")
        actions = ttk.Frame(self.page)
        actions.pack(fill="x")
        self.export_button = ttk.Button(actions, text="Export HD pack…", command=self.start_portraits)
        self.export_button.pack(side="left")
        self.controls.append(self.export_button)
        ttk.Button(actions, text="Log", style="Link.TButton", command=self.show_details).pack(side="left", padx=self.px(12))
        self.output_button = ttk.Button(actions, text="Output folder", style="Link.TButton", command=self.open_output)
        self.build_button = ttk.Button(actions, text="Create patched discs", style="Primary.TButton", command=self.start)
        self.build_button.pack(side="right")
        ttk.Label(self.page, text="Development build · Gameplay testing pending", style="Muted.TLabel").pack(
            anchor="w", pady=(self.px(10), 0))

    def selection_changed(self, *_):
        if not self.busy:
            self.status.set("Ready")
            self.status_label.configure(style="Status.TLabel")

    def browse(self, disc):
        if self.busy:
            return
        current = Path(self.paths[disc].get())
        path = filedialog.askopenfilename(parent=self.window, title=f"Select Disc {disc}",
                                          initialdir=str(current.parent) if current.parent.is_dir() else str(ROOT),
                                          filetypes=[("BIN disc images", "*.bin")])
        if path:
            self.paths[disc].set(path)
            self.path_entries[disc].xview_moveto(1)

    def append(self, text):
        self.log_lines.append(text)
        if self.log is not None:
            self.log.configure(state="normal")
            self.log.insert("end", text)
            self.log.see("end")
            self.log.configure(state="disabled")

    def show_details(self):
        if self.details_window is None or not self.details_window.winfo_exists():
            details = tk.Toplevel(self.window)
            details.title("Xenogears — Build log")
            details.geometry(f"{self.px(760)}x{self.px(440)}")
            details.minsize(self.px(460), self.px(240))
            details.transient(self.window)
            details.configure(background=self.colors["paper"])
            self.details_window = details
            frame = ttk.Frame(details, padding=self.px(20))
            frame.pack(fill="both", expand=True)
            ttk.Label(frame, text="Build log", style="Section.TLabel").pack(anchor="w", pady=(0, self.px(12)))
            area = ttk.Frame(frame)
            area.pack(fill="both", expand=True)
            self.log = tk.Text(area, wrap="word", font=("Consolas", 9), background=self.colors["white"],
                               foreground=self.colors["ink"], relief="flat", padx=self.px(12), pady=self.px(10),
                               highlightthickness=1, highlightbackground=self.colors["line"],
                               highlightcolor=self.colors["accent"], selectbackground=self.colors["accent"],
                               selectforeground=self.colors["white"])
            scroll = ttk.Scrollbar(area, command=self.log.yview)
            scroll.pack(side="right", fill="y")
            self.log.configure(yscrollcommand=scroll.set)
            self.log.pack(fill="both", expand=True)
            self.log.insert("end", "".join(self.log_lines))
            self.log.configure(state="disabled")
            self.log.bind("<Control-a>", lambda _: self.select_log())
            details.protocol("WM_DELETE_WINDOW", self.hide_details)
            details.bind("<Escape>", lambda _: self.hide_details())
        self.details_window.deiconify()
        self.details_window.lift()
        self.log.focus_set()

    def select_log(self):
        self.log.tag_add("sel", "1.0", "end-1c")
        return "break"

    def hide_details(self):
        self.details_window.withdraw()
        self.build_button.focus_set()

    def open_path(self, path):
        try:
            os.startfile(path)
        except OSError as exc:
            self.status.set("Could not open the file. See the log for details.")
            self.status_label.configure(style="Error.TLabel")
            self.append(f"Could not open {path}: {exc}\n")

    def open_output(self):
        if self.output is not None:
            self.open_path(self.output)

    def selected_paths(self, discs):
        paths = {}
        for disc in discs:
            path = Path(self.paths[disc].get().strip()).expanduser()
            if not path.is_file() or path.suffix.lower() != ".bin":
                self.status.set(f"Choose a BIN image for Disc {disc}.")
                self.status_label.configure(style="Error.TLabel")
                self.path_entries[disc].focus_set()
                return None
            paths[disc] = path
        return paths

    def begin(self, status):
        self.busy = True
        self.output = None
        self.output_button.pack_forget()
        self.status.set(status)
        self.status_label.configure(style="Status.TLabel")
        for control in (*self.controls, self.build_button):
            control.state(["disabled"])
        self.build_button.configure(text="Working…")
        self.progress.place(x=0, y=0, relwidth=1, height=self.px(3))
        self.progress.start(15)
        self.append("\n" + status + "\n")

    def start(self):
        if self.busy:
            return
        paths = self.selected_paths((1, 2))
        if paths is None:
            return
        options = Options(**{key: value.get() for key, value in self.flags.items()},
                          encounters=self.encounters.get()).validate()
        self.begin("Checking disc images…")
        threading.Thread(target=self.worker, args=(paths, options), daemon=True).start()

    def worker(self, paths, options):
        try:
            save_disc_paths(paths)
            selection = save_selection(options)
            release = "patcher-" + datetime.now().strftime("%Y%m%d-%H%M%S-%f")
            commands = [
                ("Running checks…", [sys.executable, "project.py", "test", "definitive"]),
                ("Creating patched discs…", [sys.executable, "project.py", "build", "definitive", "--release", release,
                 "--patch-options", selection, "--activate", "--label", "Definitive development candidate", "--runtime-status", "untested"]),
            ]
            for stage, command in commands:
                self.events.put(("stage", stage))
                self.events.put(("log", "Running: " + subprocess.list2cmdline(command) + "\n"))
                with subprocess.Popen(command, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                      text=True, encoding="utf-8", errors="replace",
                                      creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)) as process:
                    for line in process.stdout:
                        self.events.put(("log", line))
                    if process.wait():
                        raise ValueError("A build check failed. Open the log for details.")
            self.events.put(("log", f"Finished: builds/definitive/{release}\nGameplay remains untested.\n"))
            self.events.put(("success", ("Patched discs created.", ROOT / "builds/definitive" / release)))
        except Exception as exc:
            self.events.put(("log", f"ERROR: {exc}\n"))
            self.events.put(("error", "Could not create patched discs. See the log."))
        finally:
            self.events.put(("done", ""))

    def start_portraits(self):
        if self.busy:
            return
        paths = self.selected_paths((1,))
        if paths is None:
            return
        self.begin("Checking Disc 1 for portrait export…")
        threading.Thread(target=self.portrait_worker, args=(paths[1],), daemon=True).start()

    def portrait_worker(self, path):
        try:
            from modules.definitive.build import RetailDisc
            from modules.definitive.portrait_pack import DEFAULT_PACK, export_pack
            if digest(path) != RETAIL_SHA256[1]:
                raise ValueError("Disc 1 is not the audited USA retail image")
            self.events.put(("stage", "Exporting HD portraits…"))
            destination = ROOT / "builds/definitive-hd" / datetime.now().strftime("%Y%m%d-%H%M%S-%f")
            report = export_pack(DEFAULT_PACK, destination, RetailDisc(path, 1).read)
            self.events.put(("log", f"Exported {report['native_assets_verified']} HD portraits: {destination}\n"
                             "Standalone candidate only; no emulator settings changed. See its README.\n"))
            self.events.put(("success", ("Portraits exported. See the included setup notes.", destination)))
        except Exception as exc:
            self.events.put(("log", f"ERROR: {exc}\n"))
            self.events.put(("error", "Could not export portraits. See the log."))
        finally:
            self.events.put(("done", ""))

    def poll(self):
        try:
            # Batch large build logs so output cannot starve window input and painting.
            lines = []
            for _ in range(200):
                kind, value = self.events.get_nowait()
                if kind == "done":
                    self.busy = False
                    self.progress.stop()
                    self.progress.configure(value=0)
                    self.progress.place_forget()
                    for control in (*self.controls, self.build_button):
                        control.state(["!disabled"])
                    self.build_button.configure(text="Create patched discs")
                elif kind == "stage":
                    self.status.set(value)
                elif kind == "success":
                    status, self.output = value
                    self.status.set(status)
                    self.output_button.pack(side="left", padx=(self.px(16), 0))
                elif kind == "error":
                    self.status.set(value)
                    self.status_label.configure(style="Error.TLabel")
                    self.show_details()
                elif kind == "log":
                    lines.append(value)
        except queue.Empty:
            pass
        if lines:
            self.append("".join(lines))
        self.poll_id = self.window.after(100, self.poll)

    def close(self):
        if self.busy:
            messagebox.showinfo("Work in progress", "Keep this window open until the current operation finishes.", parent=self.window)
        else:
            self.window.after_cancel(self.poll_id)
            self.window.destroy()


def main():
    window = tk.Tk()
    Patcher(window)
    window.mainloop()


if __name__ == "__main__":
    main()
