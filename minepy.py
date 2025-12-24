import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading, subprocess, os, psutil
from minecraft_launcher_lib import install, utils, command

# ---------------- CONFIG ----------------
PROFILES = ["Standard", "FPS Boost", "Ultra Optimized"]
MINECRAFT_DIR = os.path.join(os.getcwd(), "minecraft")
os.makedirs(MINECRAFT_DIR, exist_ok=True)

total_files = 0
pause_download = False
download_thread = None

# ---------------- CALLBACK ----------------
def callback_set_status(status: str):
    log_text.configure(state='normal')
    log_text.insert(tk.END, f"{status}\n")
    log_text.see(tk.END)
    log_text.configure(state='disabled')

def callback_set_max(max_val: int):
    global total_files
    total_files = max_val
    progress_var.set(0)
    progress_label.config(text=f"0 / {max_val}")

def callback_set_progress(progress: int):
    global pause_download
    while pause_download:
        root.update()
    if total_files > 0:
        percent = int((progress / total_files) * 100)
        progress_var.set(percent)
        progress_label.config(text=f"{progress} / {total_files} ({percent}%)")
    root.update()

# ---------------- INSTALLAZIONE ----------------
def install_minecraft_version(version):
    global pause_download
    pause_download = False
    callback_set_status(f"Installazione {version} in corso...")
    version_dir = os.path.join(MINECRAFT_DIR, "versions", version)
    if os.path.exists(version_dir):
        callback_set_status(f"{version} già installata ✔")
        return
    callbacks = {
        "setStatus": callback_set_status,
        "setProgress": callback_set_progress,
        "setMax": callback_set_max
    }
    try:
        install.install_minecraft_version(version, MINECRAFT_DIR, callback=callbacks)
        callback_set_status(f"{version} installata ✔")
        messagebox.showinfo("Successo", f"Versione {version} installata!")
    except Exception as e:
        callback_set_status("Errore ❌")
        messagebox.showerror("Errore", str(e))

def install_thread():
    version = version_var.get()
    global download_thread
    download_thread = threading.Thread(target=lambda: install_minecraft_version(version), daemon=True)
    download_thread.start()

# ---------------- PAUSA / RIPRESA ----------------
def toggle_pause():
    global pause_download
    pause_download = not pause_download
    pause_button.config(text="Riprendi" if pause_download else "Pausa")
    status_var.set("Download in pausa ⏸️" if pause_download else "Download ripreso ▶️")

# ---------------- ULTRA OPTIMIZATION ----------------
def get_jvm_args(profile):
    if profile == "Standard":
        return ["-Xmx2G","-Xms1G"]
    elif profile == "FPS Boost":
        return ["-Xmx4G","-Xms2G","-XX:+UseG1GC","-XX:+OptimizeStringConcat"]
    elif profile == "Ultra Optimized":
        ram_available = psutil.virtual_memory().available // (1024*1024*1024)
        max_ram = min(6, ram_available-1)
        return [f"-Xmx{max_ram}G", f"-Xms{max_ram//2}G", "-XX:+UseG1GC", "-XX:+UseStringDeduplication","-XX:+OptimizeStringConcat","-XX:+UnlockExperimentalVMOptions","-XX:ParallelGCThreads=4","-Dfml.ignoreInvalidMinecraftCertificates=true","-Dfml.ignorePatchDiscrepancies=true","-Djava.net.preferIPv4Stack=true"]

# ---------------- AVVIO ----------------
def launch_minecraft():
    username = username_entry.get().strip() or "OfflinePlayer"
    version = version_var.get()
    profile = profile_var.get()
    options = {
        "username": username,
        "uuid": "00000000000000000000000000000000",
        "token": "",
        "jvmArguments": get_jvm_args(profile),
        "fullscreen": True,
        "width": 1280,
        "height": 720,
        "customResolution": True,
        "maxFPS": 300
    }
    try:
        mc_cmd = command.get_minecraft_command(version, MINECRAFT_DIR, options)
        subprocess.Popen(mc_cmd)
        status_var.set(f"Minecraft {version} avviato con {profile} 🎮")
    except Exception as e:
        messagebox.showerror("Errore", str(e))

# ---------------- APRI CARTELLA ----------------
def open_minecraft_folder():
    if os.path.exists(MINECRAFT_DIR):
        os.startfile(MINECRAFT_DIR)
    else:
        messagebox.showwarning("Attenzione", "La cartella Minecraft non esiste ancora!")

# ---------------- UI MODERNA ----------------
root = tk.Tk()
root.title("MinePy Launcher 🌟")
root.geometry("760x720")
root.resizable(False, False)
root.configure(bg="#1e1e2f")

# Titolo
tk.Label(root, text="MinePy Launcher", font=("Montserrat", 24, "bold"), fg="#ffd700", bg="#1e1e2f").pack(pady=15)

# Username
tk.Label(root, text="Username", font=("Montserrat", 12), fg="#ffffff", bg="#1e1e2f").pack()
username_entry = tk.Entry(root, width=30, font=("Montserrat", 12), bg="#2e2e4d", fg="#ffffff", insertbackground="white")
username_entry.pack(pady=5)

# Versioni dinamiche
all_versions = [v['id'] for v in utils.get_available_versions(MINECRAFT_DIR)]
tk.Label(root, text="Seleziona Versione", font=("Montserrat", 12), fg="#ffffff", bg="#1e1e2f").pack()
version_var = tk.StringVar()
version_dropdown = ttk.Combobox(root, textvariable=version_var, values=all_versions, state="readonly", font=("Montserrat", 12))
version_dropdown.pack(pady=5)
version_var.set(all_versions[-1])  # default ultima versione

# Profilo prestazioni
tk.Label(root, text="Profilo Prestazioni", font=("Montserrat", 12), fg="#ffffff", bg="#1e1e2f").pack()
profile_var = tk.StringVar(value=PROFILES[0])
profile_dropdown = ttk.Combobox(root, textvariable=profile_var, values=PROFILES, state="readonly", font=("Montserrat", 12))
profile_dropdown.pack(pady=5)

# Pulsanti
btn_style = {"font": ("Montserrat", 12, "bold"), "width": 30, "bg": "#ff6f61", "fg": "#ffffff", "activebackground": "#ff856f", "activeforeground": "#ffffff", "relief":"flat"}
tk.Button(root, text="Installa Versione", command=install_thread, **btn_style).pack(pady=5)
tk.Button(root, text="Gioca", command=launch_minecraft, **btn_style).pack(pady=5)
pause_button = tk.Button(root, text="Pausa", command=toggle_pause, **btn_style)
pause_button.pack(pady=5)
tk.Button(root, text="Apri cartella Minecraft", command=open_minecraft_folder, **btn_style).pack(pady=5)

# Status
status_var = tk.StringVar(value="Pronto")
tk.Label(root, textvariable=status_var, fg="#00ff00", bg="#1e1e2f", font=("Montserrat", 12, "bold")).pack(pady=5)

# Barra avanzamento
progress_var = tk.IntVar()
progress_label = tk.Label(root, text="0 / 0 (0%)", fg="#ffffff", bg="#1e1e2f", font=("Montserrat", 11))
progress_label.pack()
progress_bar = ttk.Progressbar(root, orient="horizontal", length=550, mode="determinate", variable=progress_var)
progress_bar.pack(pady=5)

# Log
log_text = scrolledtext.ScrolledText(root, width=90, height=15, state='disabled', bg="#2e2e4d", fg="#ffffff", font=("Courier", 10), insertbackground="white")
log_text.pack(pady=10)

root.mainloop()
