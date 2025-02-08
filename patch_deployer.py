import os
import subprocess

def deploy_patch_on_envs(selected_envs, patch_directory, username, password, ini_manager):
    try:
        for env in selected_envs:
            print(f"Deploying patch on {env}...")
            run_sql_script(patch_directory, env, username, password, ini_manager)
            run_xcopy_web_files(patch_directory, env, ini_manager)
    except Exception as e:
        print(f"Error deploying patch: {e}")


def run_sql_script(patch_directory, env, username, password, ini_manager):
    main_sql_path = f"{patch_directory}/MainSQL.sql"
    log_path = os.path.join(os.getcwd(), "SQL.log")

    if not os.path.exists(main_sql_path):
        print(f"Script file not found: {main_sql_path}")
        return
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

        with open(log_path, "w") as log_file:
            log_file.write(stdout)

        if "SP2-" in stdout or "ORA-" in stdout:
            print("SQL*Plus encountered errors. Check the log file for details.")
            return False

        print(f"Database patch applied succesfully for {env}")
        return True

    except subprocess.CalledProcessError as e:
        print(f"Error executing SQL*Plus: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False
    
def run_xcopy_web_files(patch_directory, env, ini_manager):
    log_path = os.path.join(os.getcwd(), "Web.log")
    web_path = ini_manager.read_key(env, "WEB_PATH", "not set")
    
    # Open the log file in append mode to add entries without overwriting
    with open(log_path, "a") as log_file:
        if web_path == "not set":
            log_message = f"Web path not found in INI file for environment {env}.\n"
            log_file.write(log_message)
            print(log_message)  # Optional: Print to console for visibility
            return

        xcopy_command = f"xcopy {patch_directory}\\Web\\* {web_path} /s /y /r"
        
        try:
            subprocess.run(xcopy_command, shell=True, check=True)
            log_message = f"Web files copied successfully for environment {env}.\n"
            log_file.write(log_message)
            print(log_message)  # Optional: Print to console for visibility
            return True
        except subprocess.CalledProcessError as e:
            log_message = f"Error executing xcopy for environment {env}: {e}\n"
            log_file.write(log_message)
            print(log_message)  # Optional: Print to console for visibility
            return False
        except Exception as e:
            log_message = f"Unexpected error for environment {env}: {e}\n"
            log_file.write(log_message)
            print(log_message)  # Optional: Print to console for visibility
            return False