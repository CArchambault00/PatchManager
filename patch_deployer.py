import os
import sys
import subprocess
from tkinter import ttk, messagebox, filedialog

def deploy_patch_on_envs(selected_envs, patch_directory, username, password, ini_manager):
    for env in selected_envs:
        print(f"Deploying patch on {env}...")
        sql_success = run_sql_script(patch_directory, env, username, password, ini_manager)
        if not sql_success:
            SQLlog(f"Stopping deployment due to SQL script failure on {env}.")
            messagebox.showerror("Error", f"An error occurred while deploying Database Patch on {env}.")
            sys.exit()  # Close the app after the error message is acknowledged
            break  # Stop deployment if SQL script fails
        
        web_success = run_xcopy_web_files(patch_directory, env, ini_manager)
        if not web_success:
            XCopyLog(f"Stopping deployment due to Web file copy failure on {env}.")
            messagebox.showerror("Error", f"An error occurred while deploying Web Patch on {env}.")
            sys.exit()  # Close the app after the error message is acknowledged
            break  # Stop deployment if Web file copy fails
    messagebox.showinfo("Success", "All environments have been patched successfully.")

def run_sql_script(patch_directory, env, username, password, ini_manager):
    main_sql_path = f"{patch_directory}/MainSQL.sql"

    if not os.path.exists(main_sql_path):
        log_message = f"Script file not found: {main_sql_path}\n"
        SQLlog(log_message)
        print(log_message)
        return False
    
    try:
        connection_string = ini_manager.read_key(env, "CONNECTSTRING", "not set")
        if connection_string == "not set":
            raise Exception("Connection string not found in INI file.")

        host = connection_string.split(";")[3].split("=")[1]
        input_text = f"{host}\n{username}\n"

        process = subprocess.Popen(
            ["sqlplus.exe", "/nolog", f"@{main_sql_path}"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=True
        )

        stdout, stderr = process.communicate(input=input_text)

        # Log the SQL output to SQL.log
        SQLlog(stdout + stderr)

        if "SP2-" in stdout or "ORA-" in stdout:
            log_message = f"SQL*Plus encountered errors. Check the log file for details.\n"
            SQLlog(log_message)
            print(log_message)
            return False

        print(f"Database patch applied successfully for {env}")
        return True

    except subprocess.CalledProcessError as e:
        log_message = f"Error executing SQL*Plus for {env}: {e}\n"
        SQLlog(log_message)
        print(log_message)
        return False
    except Exception as e:
        log_message = f"Unexpected error for {env}: {e}\n"
        SQLlog(log_message)
        print(log_message)
        return False

def run_xcopy_web_files(patch_directory, env, ini_manager):
    web_path = ini_manager.read_key(env, "WEB_PATH", "not set")

    if web_path == "not set":
        log_message = f"Web path not found in INI file for environment {env}.\n"
        XCopyLog(log_message)
        print(log_message)
        return False

    xcopy_command = f"xcopy {patch_directory}\\Web\\* {web_path} /s /y /r"

    try:
        subprocess.run(xcopy_command, shell=True, check=True)
        log_message = f"Web files copied successfully for environment {env}.\n"
        XCopyLog(log_message)
        print(log_message)
        return True
    except subprocess.CalledProcessError as e:
        log_message = f"Error executing xcopy for environment {env}: {e}\n"
        XCopyLog(log_message)
        print(log_message)
        return False
    except Exception as e:
        log_message = f"Unexpected error for environment {env}: {e}\n"
        XCopyLog(log_message)
        print(log_message)
        return False

# Log to SQL.log
def SQLlog(message):
    log_path = os.path.join(os.getcwd(), "SQL.log")
    with open(log_path, "a") as log_file:
        log_file.write(message)

# Log to Web.log
def XCopyLog(message):
    log_path = os.path.join(os.getcwd(), "Web.log")
    with open(log_path, "a") as log_file:
        log_file.write(message)
