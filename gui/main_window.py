import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from config_manager import INIFileManager
from registery_manger import RegistryManager
from patch_generator import generate_patch
from patch_deployer import deploy_patch_on_envs
import os
import subprocess

class MainWindow(tk.Tk):
    def __init__(self, ini_file):
        super().__init__()
        self.title("Patch Manager")
        self.geometry("800x600")

        # Load environment variables manually from .env file
        self.env_vars = self.load_env_file(".env")

        # Gestionnaire de fichier INI
        self.ini_manager = INIFileManager(ini_file)
        self.cyframe_directory = tk.StringVar()
        self.current_version = tk.StringVar()

        # Load saved directory from .env file if it exists
        saved_directory = self.env_vars.get("CYFRAME_DIRECTORY")
        if saved_directory:
            self.cyframe_directory.set(saved_directory)
            # If the repo in the saved directory is on main branch show error and exit
            if self.is_on_main_branch(saved_directory):
                messagebox.showerror("Error", "The repository is on the main branch. Please create a new branch and try again.")
                self.destroy()

        # Frame pour le répertoire de l'application
        directory_frame = ttk.LabelFrame(self, text="Cyframe Application Directory")
        directory_frame.pack(pady=10, padx=10, fill="both", expand=True)

        self.directory_label = ttk.Label(directory_frame, text="Directory:")
        self.directory_label.grid(row=0, column=0, padx=5, pady=5)
        self.directory_entry = ttk.Entry(directory_frame, textvariable=self.cyframe_directory, width=50)
        self.directory_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.directory_button = ttk.Button(directory_frame, text="Browse...", command=self.on_browse_click)
        self.directory_button.grid(row=0, column=2, padx=5, pady=5)

        version_frame = ttk.LabelFrame(self, text="Patch Version")
        version_frame.pack(pady=10, padx=10, fill="x")

        self.version_label = ttk.Label(version_frame, text="Current Version:")
        self.version_label.grid(row=0, column=0, padx=5, pady=5)

        self.version_entry = ttk.Entry(version_frame, textvariable=self.current_version, state='readonly', width=10)
        self.version_entry.grid(row=0, column=1, padx=5, pady=5)

        self.load_current_version()

        # self.keep_version_button = ttk.Button(version_frame, text="Keep Version", command=self.on_keep_version_click)
        # self.keep_version_button.grid(row=0, column=2, padx=5, pady=5)

        self.next_version_button = ttk.Button(version_frame, text="Next Version", command=self.on_next_version_click)
        self.next_version_button.grid(row=0, column=3, padx=5, pady=5)

        # Add a new large button below the other buttons
        self.create_patch_button = ttk.Button(version_frame, text="Create Patch", command=self.on_create_patch_click)
        self.create_patch_button.grid(row=1, column=0, columnspan=4, padx=5, pady=5, sticky="ew")

       
        # Frame pour les environnements
        env_frame = ttk.LabelFrame(self, text="Environments")
        env_frame.pack(pady=10, padx=10, fill="both", expand=True)

        self.env_listbox = tk.Listbox(env_frame, selectmode=tk.MULTIPLE)
        self.env_listbox.pack(pady=10, padx=10, fill="both", expand=True)
        self.load_environments()

        # Frame pour les informations utilisateur
        user_frame = ttk.LabelFrame(self, text="User Information")
        user_frame.pack(pady=10, padx=10, fill="x")

        self.username_label = ttk.Label(user_frame, text="Username:")
        self.username_label.grid(row=0, column=0, padx=5, pady=5)
        self.username_entry = ttk.Entry(user_frame)
        self.username_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        self.password_label = ttk.Label(user_frame, text="Password:")
        self.password_label.grid(row=1, column=0, padx=5, pady=5)
        self.password_entry = ttk.Entry(user_frame, show="*")
        self.password_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        self.ok_button = ttk.Button(self, text="Test Patch on envs", command=self.test_patch_on_envs)
        self.ok_button.pack(pady=20)

    def on_browse_click(self):
        directory = filedialog.askdirectory()
        if directory:
            self.cyframe_directory.set(directory)
            self.update_env_file(".env", "CYFRAME_DIRECTORY", directory)

    def load_current_version(self):
        version = self.get_latest_tag()
        if not version:
            version = "v1.0.0"
        self.current_version.set(version)

    # def on_keep_version_click(self):
    #     version = self.current_version.get()
    #     if version:
    #         self.update_env_file(".env", "CURRENT_VERSION", version)
    #         self.force_push_tag(version)
    #         messagebox.showinfo("Info", f"Version {version} kept and pushed as a tag.")
    #     else:
    #         messagebox.showwarning("Warning", "No version to keep.")

    def on_next_version_click(self):
        latest_tag = self.get_latest_tag()
        if latest_tag:
            version_parts = latest_tag[1:].split('.')  # Remove 'v' prefix
            major = int(version_parts[0])
            minor = int(version_parts[1]) if len(version_parts) > 1 else 0
            patch = int(version_parts[2]) + 1 if len(version_parts) > 2 else 0
            new_version = f"v{major}.{minor}.{patch}"
        else:
            new_version = "v1.0.0"
        self.current_version.set(new_version)

    def load_environments(self):
        environments = self.ini_manager.get_environments()
        if environments:
            for env in environments:
                self.env_listbox.insert(tk.END, env)
        else:
            messagebox.showwarning("Warning", "No environments found in the INI file.")

    def test_patch_on_envs(self):
        selected_envs = [self.env_listbox.get(i) for i in self.env_listbox.curselection()]
        if not selected_envs:
            messagebox.showwarning("Warning", "Please select at least one environment.")
            return
        
        # Check if version exist in CYFRAME_DIRECTORY/Patches
        version = self.current_version.get()
        if not version:
            messagebox.showwarning("Warning", "No version to test a patch for.")
            return
        
        directory = self.cyframe_directory.get()
        if not directory or not os.path.isdir(directory):
            messagebox.showwarning("Warning", "Invalid Cyframe directory.")
            return
        
        patch_directory = os.path.join(directory, "Patches", version)
        if not os.path.isdir(patch_directory):
            messagebox.showwarning("Warning", f"Patch for version {version} not found in Patches.")
            return

        username = self.username_entry.get()
        password = self.password_entry.get()
        if not username or not password:
            messagebox.showwarning("Warning", "Please enter your username and password.")
            return
        
        deploy_patch_on_envs(selected_envs, patch_directory, username, password, self.ini_manager)

    def load_env_file(self, filepath):
        env_vars = {}
        if os.path.exists(filepath):
            with open(filepath, "r") as file:
                for line in file:
                    line = line.strip()
                    if line and "=" in line:
                        key, value = line.split("=", 1)
                        env_vars[key.strip()] = value.strip()
        return env_vars

    def update_env_file(self, filepath, key, value):
        env_vars = self.load_env_file(filepath)
        env_vars[key] = value
        with open(filepath, "w") as file:
            for k, v in env_vars.items():
                file.write(f"{k}={v}\n")

    def get_latest_tag(self):
        directory = self.cyframe_directory.get()
        if directory and os.path.isdir(directory):
            try:
                # Fetch the latest tags from the remote repository
                subprocess.run(
                    ["git", "fetch", "--tags"],
                    cwd=directory,
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                # Now get the latest tag from the remote
                result = subprocess.run(
                    ["git", "describe", "--tags", "--abbrev=0"],
                    cwd=directory,
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    return result.stdout.strip()
            except subprocess.CalledProcessError as e:
                print(f"Error fetching latest tag: {e}")
            except Exception as e:
                print(f"Unexpected error: {e}")
        return None

    def force_push_tag(self, tag):
        directory = self.cyframe_directory.get()
        if directory and os.path.isdir(directory):
            try:
                subprocess.run(
                    ["git", "tag", "-f", tag],
                    cwd=directory,
                    check=True
                )
                subprocess.run(
                    ["git", "push", "-f", "origin", tag],
                    cwd=directory,
                    check=True
                )
            except Exception as e:
                messagebox.showerror("Error", f"Error pushing tag: {e}")

    def is_on_main_branch(self, directory):
        try:
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=directory,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                return result.stdout.strip() == "main"
        except Exception as e:
            print(f"Error checking current branch: {e}")
        return False
    
    def on_create_patch_click(self):
        version = self.current_version.get()
        if version:
            self.update_env_file(".env", "CURRENT_VERSION", version)
            self.force_push_tag(version)
            messagebox.showinfo("Info", f"Version {version} kept and pushed as a tag.")
        else:
            messagebox.showwarning("Warning", "No version to keep.")
            return

        # version = self.env_vars.get("CURRENT_VERSION")
        # if not version:
        #     messagebox.showwarning("Warning", "No version to create a patch for.")
        #     return
        
        # Check if the directory is valid
        directory = self.cyframe_directory.get()
        if not directory or not os.path.isdir(directory):
            messagebox.showwarning("Warning", "Invalid Cyframe directory.")
            return
        
        # Check if the repository is on the main branch
        if self.is_on_main_branch(directory):
            messagebox.showerror("Error", "The repository is on the main branch. Please create a new branch and try again.")
            return
        
        generate_patch(directory, version)