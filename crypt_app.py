"""
SecureChat Pro - Encryption GUI
Tkinter desktop app for manual encrypt/decrypt workflow.
"""

import time
import tkinter as tk
from tkinter import messagebox, ttk

from crypto_core import CryptoError, decrypt_details, encrypt, token_fingerprint


BG = "#0f172a"
PANEL = "#111827"
FG = "#e5e7eb"
MUTED = "#94a3b8"
ACCENT = "#38bdf8"
GREEN = "#22c55e"
PURPLE = "#a78bfa"
GRAY = "#64748b"


class App(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("SecureChat Pro")
        self.geometry("800x860")
        self.minsize(720, 780)
        self.configure(bg=BG)

        self.base_font = ("Segoe UI", 11)
        self.bold_font = ("Segoe UI", 11, "bold")
        self.button_font = ("Segoe UI", 10, "bold")
        self.small_font = ("Segoe UI", 9)

        self.show_password = False
        self.decrypted_fps = set()

        self._build()

    def label(self, parent, text, color=FG, bold=False):
        return tk.Label(
            parent,
            text=text,
            bg=BG,
            fg=color,
            anchor="e",
            justify="right",
            font=self.bold_font if bold else self.base_font,
        )

    def text_box(self, parent, height):
        box = tk.Text(
            parent,
            height=height,
            bg=PANEL,
            fg=FG,
            insertbackground=FG,
            relief="flat",
            font=self.base_font,
            wrap="word",
            padx=10,
            pady=10,
        )
        box.tag_configure("rtl", justify="right")
        return box

    def button(self, parent, text, command, color=ACCENT):
        return tk.Button(
            parent,
            text=text,
            command=command,
            bg=color,
            fg="#0b1120",
            activebackground=color,
            activeforeground="#0b1120",
            relief="flat",
            font=self.button_font,
            padx=14,
            pady=6,
            cursor="hand2",
        )

    def _build(self):
        pad = {"padx": 18, "pady": (8, 2), "fill": "x"}

        self.label(self, "Shared Password", ACCENT, True).pack(**pad)

        pw_row = tk.Frame(self, bg=BG)
        pw_row.pack(padx=18, pady=(0, 10), fill="x")

        self.pw = tk.Entry(
            pw_row,
            show="\u2022",
            bg=PANEL,
            fg=FG,
            insertbackground=FG,
            relief="flat",
            font=self.base_font,
            justify="right",
        )
        self.pw.pack(side="right", fill="x", expand=True, ipady=6)

        self.eye_btn = self.button(pw_row, "Show", self.toggle_password, GRAY)
        self.eye_btn.pack(side="right", padx=(0, 8))

        # ----- Sending section -----
        self.label(self, "Outgoing Message", GREEN, True).pack(**pad)

        self.msg_in = self.text_box(self, 4)
        self.msg_in.pack(padx=18, fill="x")

        row1 = tk.Frame(self, bg=BG)
        row1.pack(padx=18, pady=6, fill="x")

        self.button(row1, "Encrypt", self.do_encrypt, GREEN).pack(side="right")
        self.button(row1, "Copy Token", self.copy_out, ACCENT).pack(side="right", padx=6)
        self.button(row1, "Clear", lambda: self.clear(self.msg_in, self.msg_out), GRAY).pack(side="right", padx=6)

        self.label(self, "Encrypted Token - paste into chat.py", FG, False).pack(**pad)

        self.msg_out = self.text_box(self, 5)
        self.msg_out.pack(padx=18, fill="x")

        ttk.Separator(self).pack(fill="x", padx=18, pady=14)

        # ----- Receiving section -----
        self.label(self, "Incoming Encrypted Token", PURPLE, True).pack(**pad)

        self.rcv_in = self.text_box(self, 5)
        self.rcv_in.pack(padx=18, fill="x")

        row2 = tk.Frame(self, bg=BG)
        row2.pack(padx=18, pady=6, fill="x")

        self.button(row2, "Decrypt", self.do_decrypt, ACCENT).pack(side="right")
        self.button(row2, "Paste & Decrypt", self.paste_and_decrypt, PURPLE).pack(side="right", padx=6)
        self.button(row2, "Clear", lambda: self.clear(self.rcv_in, self.rcv_out), GRAY).pack(side="right", padx=6)

        self.label(self, "Decrypted Message", GREEN, False).pack(**pad)

        self.rcv_out = self.text_box(self, 4)
        self.rcv_out.pack(padx=18, fill="x")

        self.info = tk.Label(
            self,
            text="",
            bg=BG,
            fg=MUTED,
            font=self.small_font,
            anchor="e",
            justify="right",
        )
        self.info.pack(fill="x", padx=18, pady=(8, 0))

        self.status = tk.Label(
            self,
            text="Ready",
            bg=BG,
            fg=MUTED,
            font=self.small_font,
            anchor="e",
            justify="right",
        )
        self.status.pack(fill="x", padx=18, pady=10)

    def toggle_password(self):
        self.show_password = not self.show_password
        self.pw.config(show="" if self.show_password else "\u2022")
        self.eye_btn.config(text="Hide" if self.show_password else "Show")

    def set_text(self, widget, text):
        widget.delete("1.0", "end")
        text = text or ""
        if text:
            widget.insert("1.0", text)
            widget.tag_add("rtl", "1.0", "end")

    def get_text(self, widget):
        return widget.get("1.0", "end").strip()

    def clear(self, *widgets):
        for widget in widgets:
            self.set_text(widget, "")
        self.info.config(text="")
        self.status.config(text="Cleared")

    def password(self):
        p = self.pw.get()
        if not p:
            messagebox.showwarning("Warning", "Enter the shared password first")
            self.pw.focus_set()
            return None
        return p

    def do_encrypt(self):
        p = self.password()
        if not p:
            return

        text = self.get_text(self.msg_in)
        if not text:
            messagebox.showwarning("Warning", "Write a message first")
            return

        try:
            token = encrypt(p, text)
            self.set_text(self.msg_out, token)

            fp = token_fingerprint(token)
            self.info.config(text=f"Size: {len(token)} chars | Fingerprint: {fp}")
            self.status.config(text="Encrypted successfully. Copy the token and send it in chat.py.")

        except CryptoError as exc:
            messagebox.showerror("Encryption Error", str(exc))
        except Exception as exc:
            messagebox.showerror("Unexpected Error", str(exc))

    def do_decrypt(self):
        p = self.password()
        if not p:
            return

        token = self.get_text(self.rcv_in)
        if not token:
            messagebox.showwarning("Warning", "Paste the encrypted token first")
            return

        try:
            details = decrypt_details(p, token)
            message = details["message"]

            self.set_text(self.rcv_out, message)

            fp = token_fingerprint(token)

            warning = ""
            if fp in self.decrypted_fps:
                warning = " Warning: this encrypted token was decrypted before. Possible replay."
            else:
                self.decrypted_fps.add(fp)

            parts = [f"Fingerprint: {fp}"]

            issued_at = details.get("issued_at")
            if issued_at:
                try:
                    issued_str = time.strftime(
                        "%Y-%m-%d %H:%M:%S",
                        time.localtime(int(issued_at)),
                    )
                    parts.append(f"Issued: {issued_str}")
                except Exception:
                    pass

            expires_at = details.get("expires_at")
            if expires_at:
                try:
                    expires_str = time.strftime(
                        "%Y-%m-%d %H:%M:%S",
                        time.localtime(int(expires_at)),
                    )
                    parts.append(f"Expires: {expires_str}")
                except Exception:
                    pass

            self.info.config(text=" | ".join(parts))

            if warning:
                self.status.config(text="Decrypted successfully." + warning)
            else:
                self.status.config(text="Decrypted successfully. Message is authentic and untampered.")

        except CryptoError as exc:
            self.set_text(self.rcv_out, "")
            self.info.config(text="Decryption failed")
            self.status.config(text="Message could not be verified")
            messagebox.showerror("Decryption Failed", str(exc))
        except Exception as exc:
            self.set_text(self.rcv_out, "")
            self.info.config(text="Unexpected error")
            self.status.config(text="Error")
            messagebox.showerror("Error", str(exc))

    def copy_out(self):
        text = self.get_text(self.msg_out)
        if not text:
            messagebox.showwarning("Warning", "No encrypted token to copy")
            return

        self.clipboard_clear()
        self.clipboard_append(text)
        self.status.config(text="Encrypted token copied")

    def paste_and_decrypt(self):
        try:
            clip = self.clipboard_get()
        except tk.TclError:
            messagebox.showwarning("No Text", "Clipboard is empty")
            return

        self.set_text(self.rcv_in, clip.strip())
        self.do_decrypt()


if __name__ == "__main__":
    App().mainloop()
