import tkinter as tk
from tkinter import ttk, messagebox
from config_manager import INIFileManager
from registery_manger import RegistryManager
import os
import subprocess
import datetime

class MainWindow(tk.Tk):
    def __init__(self, ini_file):
        super().__init__()
        self.title("Patch Manager")
        self.geometry("800x600")

        # Gestionnaire de fichier INI
        self.ini_manager = INIFileManager(ini_file)

        # Frame pour les environnements
        env_frame = ttk.LabelFrame(self, text="Environments")
        env_frame.pack(pady=10, padx=10, fill="both", expand=True)

        # Liste déroulante pour les environnements (remplacée par une ListBox)
        self.env_listbox = tk.Listbox(env_frame, selectmode=tk.MULTIPLE)
        self.env_listbox.pack(pady=10, padx=10, fill="both", expand=True)

        # Charger les environnements disponibles
        self.load_environments()

        # Frame pour les informations utilisateur
        user_frame = ttk.LabelFrame(self, text="User Information")
        user_frame.pack(pady=10, padx=10, fill="x")

        # Champ pour le nom d'utilisateur
        self.username_label = ttk.Label(user_frame, text="Username:")
        self.username_label.grid(row=0, column=0, padx=5, pady=5)
        self.username_entry = ttk.Entry(user_frame)
        self.username_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        # Champ pour le mot de passe
        self.password_label = ttk.Label(user_frame, text="Password:")
        self.password_label.grid(row=1, column=0, padx=5, pady=5)
        self.password_entry = ttk.Entry(user_frame, show="*")  # Masquer les caractères
        self.password_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        # Bouton OK
        self.ok_button = ttk.Button(self, text="OK", command=self.on_ok_click)
        self.ok_button.pack(pady=20)

        # Variables pour la planification
        self.schedule_date = None  # Date de planification (si définie)

    def load_environments(self):
        """Charge les environnements disponibles dans la ListBox."""
        environments = self.ini_manager.get_environments()
        if environments:
            for env in environments:
                self.env_listbox.insert(tk.END, env)
        else:
            messagebox.showwarning("Warning", "No environments found in the INI file.")

    def on_ok_click(self):
        """Gère le clic sur le bouton OK."""
        # Récupérer les environnements sélectionnés
        selected_envs = [self.env_listbox.get(i) for i in self.env_listbox.curselection()]
        if not selected_envs:
            messagebox.showwarning("Warning", "Please select at least one environment.")
            return

        # Récupérer le nom d'utilisateur et le mot de passe
        username = self.username_entry.get()
        password = self.password_entry.get()

        if not username or not password:
            messagebox.showwarning("Warning", "Please enter your username and password.")
            return

        # Vérifier si une date de planification est définie
        if self.schedule_date and self.schedule_date > datetime.datetime.now():
            self.write_param_file(selected_envs, username, password)
            self.schedule_task()
        else:
            self.run_patch(selected_envs, username, password)

    def write_param_file(self, environments, username, password):
        """Écrit les paramètres dans un fichier pour une exécution planifiée."""
        param_file = os.path.join(os.getcwd(), "params.txt")
        with open(param_file, "w") as f:
            f.write(f"USERNAME={username}\n")
            f.write(f"PASSWORD={password}\n")
            for env in environments:
                f.write(f"ENVIRONMENT={env}\n")
        print(f"Paramètres écrits dans {param_file}")

    def schedule_task(self):
        """Planifie l'exécution du patch."""
        try:
            task_name = "PatchManagerTask"
            task_time = self.schedule_date.strftime("%H:%M")
            task_date = self.schedule_date.strftime("%d/%m/%Y")
            command = f'schtasks /create /tn "{task_name}" /tr "{os.path.join(os.getcwd(), "run_patch.bat")}" /sc once /st {task_time} /sd {task_date}'
            subprocess.run(command, shell=True, check=True)
            messagebox.showinfo("Info", "Tâche planifiée avec succès.")
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Error", f"Erreur lors de la planification de la tâche : {e}")

    def run_patch(self, environments, username, password):
        """Exécute le patch immédiatement."""
        try:
            # Exécuter les scripts SQL pour chaque environnement
            for env in environments:
                self.execute_sql_script(env, username, password)

            # Valider les objets de la base de données
            self.validate_database_objects(environments)

            # Copier les fichiers web
            self.copy_web_files(environments)

            self.copy_crystal_files(environments)

            # Notifier le serveur web
            self.notify_web_server(environments, username)

            messagebox.showinfo("Info", "Patch appliqué avec succès.")
        except Exception as e:
            messagebox.showerror("Error", f"Erreur lors de l'application du patch : {e}")

    def execute_sql_script(self, environment, username, password):
        """Execute a SQL script for a given environment, similar to the VB code."""
        script_path = os.path.join(os.getcwd(), "MainSQL.sql")
        log_path = os.path.join(os.getcwd(), "SQL.log")
        if not os.path.exists(script_path):
            print(f"Script file not found: {script_path}")
            return

        # Execute SQL*Plus with the script and input text
        try:
            connectionString = self.ini_manager.read_key(environment, "CONNECTSTRING", "not set")
            if connectionString == "not set":
                raise Exception("Connection string not found in INI file.")
            host = connectionString.split(";")[3].split("=")[1]
            print(f"Executing SQL script for {environment} on {host}...")
            # Prepare the input text for SQL*Plus
            input_text = f"{host}\n{username}\n"
            # Use subprocess.Popen to handle input and output streams
            process = subprocess.Popen(
                ["sqlplus.exe", "/nolog", f"@{script_path}"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                shell=True
            )

            # Write the input text to SQL*Plus
            stdout, stderr = process.communicate(input=input_text)

            # Log the output to a file
            with open(log_path, "w") as log_file:
                log_file.write(stdout)

            # Check for errors in the output
            if "SP2-" in stdout or "ORA-" in stdout:
                print("SQL*Plus encountered errors. Check the log file for details.")
                return False

            print(f"SQL script executed successfully for {environment}")
            return True

        except subprocess.CalledProcessError as e:
            print(f"Error executing SQL*Plus: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error: {e}")
            return False

    def validate_database_objects(self, environments):
        """Valide les objets de la base de données."""
        for env in environments:
            print(f"Validation des objets de la base de données pour {env}...")
            # Logique de validation (à implémenter)

    def copy_web_files(self, environments):
        """Copie les fichiers web pour chaque environnement."""
        for env in environments:
            web_source = os.path.join(os.getcwd(), "Web")
            web_dest = self.ini_manager.read_key(env, "WEB_PATH", "not set")
            if web_dest != "not set":
                command = f'xcopy "{web_source}" "{web_dest}" /s /y /r'
                subprocess.run(command, shell=True, check=True)
                print(f"Fichiers web copiés pour {env}")

    def copy_crystal_files(self, environments):
        """Copie les fichiers web pour chaque environnement."""
        for env in environments:
            web_source = os.path.join(os.getcwd(), "Crystal")
            web_dest = self.ini_manager.read_key(env, "WEB_PATH", "not set")
            if web_dest != "not set":
                full_dest_path = os.path.join(web_dest, "Crystal")
            
                # Créer le dossier s'il n'existe pas
                os.makedirs(full_dest_path, exist_ok=True)
                
                command = f'xcopy "{web_source}" "{full_dest_path}" /s /y /r'
                subprocess.run(command, shell=True, check=True)
                print(f"Fichiers web copiés pour {env}")


    def notify_web_server(self, environments, username):
        """Notifie le serveur web que le patch a été appliqué."""
        for env in environments:
            print(f"Notification du serveur web pour {env} en tant que {username}...")
            # Logique de notification (à implémenter)