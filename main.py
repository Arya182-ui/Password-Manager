import tkinter as tk
from tkinter import messagebox, ttk
import sqlite3
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import base64
from hashlib import sha256


class AESCipher:
    def __init__(self, key):
        self.key = sha256(key.encode('utf-8')).digest()

    def encrypt(self, plaintext):
        cipher = AES.new(self.key, AES.MODE_CBC)
        iv = cipher.iv
        ciphertext = cipher.encrypt(pad(plaintext.encode('utf-8'), AES.block_size))
        return base64.b64encode(iv + ciphertext).decode('utf-8')

    def decrypt(self, encrypted_text):
        try:
            data = base64.b64decode(encrypted_text)
            iv = data[:16]
            ciphertext = data[16:]
            cipher = AES.new(self.key, AES.MODE_CBC, iv)
            return unpad(cipher.decrypt(ciphertext), AES.block_size).decode('utf-8')
        except Exception:
            raise ValueError("Decryption failed. Incorrect master password or corrupted data.")


def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS passwords (
        id INTEGER PRIMARY KEY,
        site TEXT NOT NULL,
        username TEXT NOT NULL,
        password TEXT NOT NULL
    )''')
    conn.commit()
    conn.close()


def save_password(site, username, password):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO passwords (site, username, password) VALUES (?, ?, ?)', (site, username, password))
    conn.commit()
    conn.close()


def update_password(site, username, password, record_id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE passwords SET site = ?, username = ?, password = ? WHERE id = ?', (site, username, password, record_id))
    conn.commit()
    conn.close()


def delete_password(record_id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM passwords WHERE id = ?', (record_id,))
    conn.commit()
    conn.close()


def get_passwords():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, site, username, password FROM passwords')
    rows = cursor.fetchall()
    conn.close()
    return rows


class PasswordManagerApp:
    def __init__(self, root):
        self.cipher = None
        self.root = root
        self.root.title("Password Manager")
        self.root.geometry("610x220")
        self.root.configure(bg="#16a085")
        self.init_ui()

    def init_ui(self):
        # Master Password Section
        frame = tk.Frame(self.root, bg="#16a085")
        frame.pack(pady=10, padx=10, fill=tk.X)

        tk.Label(frame, text="Master Password:", font=("Arial", 12), bg="#f39c12").grid(row=0, column=0, padx=10, sticky="w")
        self.master_password_entry = ttk.Entry(frame, show="*", font=("Arial", 12))
        self.master_password_entry.grid(row=0, column=1, padx=10, sticky="w")

        self.toggle_master_password = ttk.Button(frame, text="Show", command=lambda: self.toggle_password_visibility(self.master_password_entry))
        self.toggle_master_password.grid(row=0, column=2, padx=10)

        ttk.Button(frame, text="Set Master Password", command=self.set_master_password).grid(row=0, column=3, padx=10)

        # Input Section
        form_frame = tk.Frame(self.root, bg="#16a085")
        form_frame.pack(pady=10, padx=10, fill=tk.X)

        tk.Label(form_frame, text="Site:", font=("Arial", 12), bg="#f39c12").grid(row=0, column=0, pady=5, padx=10, sticky="w")
        self.site_entry = ttk.Entry(form_frame, font=("Arial", 12))
        self.site_entry.grid(row=0, column=1, pady=5, padx=10, sticky="w")

        tk.Label(form_frame, text="Username:", font=("Arial", 12), bg="#f39c12").grid(row=1, column=0, pady=5, padx=10, sticky="w")
        self.username_entry = ttk.Entry(form_frame, font=("Arial", 12))
        self.username_entry.grid(row=1, column=1, pady=5, padx=10, sticky="w")

        tk.Label(form_frame, text="Password:", font=("Arial", 12), bg="#f39c12").grid(row=2, column=0, pady=5, padx=10, sticky="w")
        self.password_entry = ttk.Entry(form_frame, show="*", font=("Arial", 12))
        self.password_entry.grid(row=2, column=1, pady=5, padx=10, sticky="w")

        self.toggle_password = ttk.Button(form_frame, text="Show", command=lambda: self.toggle_password_visibility(self.password_entry))
        self.toggle_password.grid(row=2, column=2, pady=5, padx=10)

        # Buttons Section
        button_frame = tk.Frame(self.root, bg="#16a085")
        button_frame.pack(pady=10, padx=10, fill=tk.X)

        ttk.Button(button_frame, text="Save Password", command=self.save_password).grid(row=0, column=0, padx=10)
        ttk.Button(button_frame, text="View Passwords", command=self.view_passwords).grid(row=0, column=1, padx=10)

    def toggle_password_visibility(self, entry):
        if entry.cget("show") == "*":
            entry.config(show="")
        else:
            entry.config(show="*")

    def set_master_password(self):
        key = self.master_password_entry.get()
        if not key:
            messagebox.showerror("Error", "Master password cannot be empty!")
            return
        self.cipher = AESCipher(key)
        messagebox.showinfo("Success", "Master password set!")

    def save_password(self):
        if not self.cipher:
            messagebox.showerror("Error", "Set the master password first!")
            return
        site = self.site_entry.get()
        username = self.username_entry.get()
        password = self.password_entry.get()
        if not site or not username or not password:
            messagebox.showerror("Error", "All fields are required!")
            return
        
        encrypted_password = self.cipher.encrypt(password)
        save_password(site, username, encrypted_password)
        messagebox.showinfo("Success", "Password saved successfully!")

        # Clear fields after saving password
        self.site_entry.delete(0, tk.END)
        self.username_entry.delete(0, tk.END)
        self.password_entry.delete(0, tk.END)

    def view_passwords(self):
        if not self.cipher:
            messagebox.showerror("Error", "Set the master password first!")
            return

        view_window = tk.Toplevel(self.root)
        view_window.title("Saved Passwords")
        view_window.geometry("800x500")
        view_window.configure(bg="#16a085")

        tree = ttk.Treeview(view_window, columns=("ID", "Site", "Username", "Password"), show="headings", height=10)
        tree.heading("ID", text="ID")
        tree.heading("Site", text="Site")
        tree.heading("Username", text="Username")
        tree.heading("Password", text="Password")
        tree.column("ID", width=40)
        tree.column("Site", width=200)
        tree.column("Username", width=200)
        tree.column("Password", width=200)
        tree.tag_configure("odd", background="#ecf0f1")  
        tree.tag_configure("even", background="#bdc3c7")
        tree.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(view_window, orient="vertical", command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        passwords = get_passwords()
              
        for record_id, site, username, encrypted_password in passwords:
            try:
                decrypted_password = self.cipher.decrypt(encrypted_password)
                tree.insert("", tk.END, values=(record_id, site, username, decrypted_password))
            except ValueError:
                tree.insert("", tk.END, values=(record_id, site, username, "Incorrect Master Password"))

        def modify_selected():
            selected_item = tree.selection()
            if selected_item:
                record = tree.item(selected_item)["values"]
                record_id = record[0]
                site = record[1]
                username = record[2]
                password = record[3]

                def save_modifications():
                    new_site = modify_site_entry.get()
                    new_username = modify_username_entry.get()
                    new_password = modify_password_entry.get()

                    if not new_site or not new_username or not new_password:
                        messagebox.showerror("Error", "All fields are required!")
                        return

                    encrypted_password = self.cipher.encrypt(new_password)
                    update_password(new_site, new_username, encrypted_password, record_id)
                    messagebox.showinfo("Success", "Password modified successfully!")
                    modify_window.destroy()
                    view_window.destroy()
                    self.view_passwords()

                modify_window = tk.Toplevel(view_window)
                modify_window.title("Modify Password")
                modify_window.geometry("400x300")
                modify_window.configure(bg="#16a085")

                tk.Label(modify_window, text="Site:").pack(pady=5)
                modify_site_entry = ttk.Entry(modify_window)
                modify_site_entry.insert(0, site)
                modify_site_entry.pack(pady=5)

                tk.Label(modify_window, text="Username:").pack(pady=5)
                modify_username_entry = ttk.Entry(modify_window)
                modify_username_entry.insert(0, username)
                modify_username_entry.pack(pady=5)

                tk.Label(modify_window, text="Password:").pack(pady=5)
                modify_password_entry = ttk.Entry(modify_window, show="*")
                modify_password_entry.insert(0, password)
                modify_password_entry.pack(pady=5)

                tk.Button(modify_window, text="Save", command=save_modifications).pack(pady=10)

        def delete_selected():
            selected_item = tree.selection()
            if selected_item:
                record = tree.item(selected_item)["values"]
                record_id = record[0]
                confirm = messagebox.askyesno("Delete", "Are you sure you want to delete this password?")
                if confirm:
                    delete_password(record_id)
                    tree.delete(selected_item)

        tree.bind("<Button-3>", lambda event: context_menu(event, tree))

        def context_menu(event, tree):
            menu = tk.Menu(view_window, tearoff=0)
            menu.add_command(label="Modify", command=modify_selected)
            menu.add_command(label="Delete", command=delete_selected)
            menu.tk_popup(event.x_root, event.y_root)


if __name__ == "__main__":
    init_db()
    root = tk.Tk()
    app = PasswordManagerApp(root)
    root.mainloop()
