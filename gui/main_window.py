import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from config_manager import INIFileManager
from registery_manager import RegistryManager
from patch_generator import generate_patch
from patch_deployer import deploy_patch_on_envs
import os
import subprocess

class MainWindow(tk.Tk):
    def __init__(self, ini_file):
        super().__init__()
        self.title("Patch Manager")
        self.geometry("800x600")

        self.env_vars = self.load_env_file(".env")
        self.ini_manager = INIFileManager(ini_file)
        self.cyframe_directory = tk.StringVar()
        self.current_version = tk.StringVar()

        saved_directory = self.env_vars.get("CYFRAME_DIRECTORY")
        if saved_directory:
            self.cyframe_directory.set(saved_directory)
            if self.is_on_main_branch(saved_directory):
                messagebox.showerror("Error", "The repository is on the main branch. Please create a new branch and try again.")
                self.destroy()

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

        self.next_version_button = ttk.Button(version_frame, text="Next Version", command=self.on_next_version_click)
        self.next_version_button.grid(row=0, column=3, padx=5, pady=5)

        self.create_patch_button = ttk.Button(version_frame, text="Create Patch", command=self.on_create_patch_click)
        self.create_patch_button.grid(row=1, column=0, columnspan=4, padx=5, pady=5, sticky="ew")

        env_frame = ttk.LabelFrame(self, text="Environments")
        env_frame.pack(pady=10, padx=10, fill="both", expand=True)

        self.env_listbox = tk.Listbox(env_frame, selectmode=tk.MULTIPLE)
        self.env_listbox.pack(pady=10, padx=10, fill="both", expand=True)
        self.load_environments()

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

    def on_next_version_click(self):
        latest_tag = self.get_latest_tag()
        if latest_tag:
            version_parts = latest_tag[1:].split('.')
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
                subprocess.run(
                    ["git", "fetch", "--tags"],
                    cwd=directory,
                    capture_output=True,
                    text=True,
                    check=True
                )

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
        directory = self.cyframe_directory.get()
        if not directory or not os.path.isdir(directory):
            messagebox.showwarning("Warning", "Invalid Cyframe directory.")
            return

        if self.is_on_main_branch(directory):
            messagebox.showerror("Error", "The repository is on the main branch. Please create a new branch and try again.")
            return

        # Fetch the latest version from main
        try:
            subprocess.run(["git", "fetch", "origin", "main"], cwd=directory, check=True)
            subprocess.run(["git", "checkout", "main"], cwd=directory, check=True)
            subprocess.run(["git", "pull", "origin", "main"], cwd=directory, check=True)
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Error", f"Failed to fetch latest version from main: {e}")
            return

        # Read the current version from version.txt
        version_file = os.path.join(directory, "version.txt")
        if not os.path.exists(version_file):
            with open(version_file, "w") as f:
                f.write("v1.0.0")

        with open(version_file, "r") as f:
            current_version = f.read().strip()

        # Increment the version
        version_parts = current_version[1:].split('.')
        major = int(version_parts[0])
        minor = int(version_parts[1])
        patch = int(version_parts[2]) + 1
        new_version = f"v{major}.{minor}.{patch}"

        # Write the new version back to version.txt
        with open(version_file, "w") as f:
            f.write(new_version)

        # Commit and push the new version to main
        try:
            subprocess.run(["git", "add", "version.txt"], cwd=directory, check=True)
            subprocess.run(["git", "commit", "-m", f"Update version to {new_version}"], cwd=directory, check=True)
            subprocess.run(["git", "push", "origin", "main"], cwd=directory, check=True)
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Error", f"Failed to push new version to main: {e}")
            return

        # Switch back to the feature branch
        try:
            subprocess.run(["git", "checkout", "-"], cwd=directory, check=True)
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Error", f"Failed to switch back to feature branch: {e}")
            return

        # Create the patch with the new version
        generate_patch(directory, new_version)
        messagebox.showinfo("Info", f"Patch created with version {new_version}.")