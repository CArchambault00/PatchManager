import subprocess
import os
import shutil
def generate_patch(directory, version):
    # Get modified files that have been committed and pushed to the remote
    web_modified_files = get_committed_and_pushed_files(directory, "webpage/")
    database_modified_files = get_committed_and_pushed_files(directory, "Database/")
    sql_files = get_sql_files(directory)

    patch_directory = create_patch_directory(directory, version)
    directory = directory + "\\"
    create_database_files(directory ,patch_directory, database_modified_files,  sql_files)
    create_web_files(directory, patch_directory, web_modified_files)

def get_committed_and_pushed_files(directory, folder):
    # Get the current branch
    current_branch = get_current_branch(directory)
    if not current_branch:
        return []

    # Fetch the latest updates from the remote
    subprocess.run(["git", "fetch"], cwd=directory, capture_output=True, text=True, check=True)

    # Get the list of files that have been committed and pushed to the remote branch
    result = subprocess.run(
        ["git", "diff", "--name-only", f"main...{current_branch}", "--", folder],
        cwd=directory,
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        # Return the list of modified files
        return result.stdout.strip().splitlines()
    else:
        print(f"Error getting committed and pushed files: {result.stderr}")
        return []

def get_sql_files(directory):
    # Get all SQL files in directory except MainSQL.sql
    sql_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".sql") and file != "MainSQL.sql":
                sql_files.append(os.path.join(root, file))


def create_patch_directory(directory, version):
    # Create the patch directory in directory/Patches with the version number if already exists overwrite it
    patch_directory = os.path.join(directory, "Patches", version)
    os.makedirs(patch_directory, exist_ok=True)
    return patch_directory

def create_database_files(directory, patch_directory, database_modified_files, sql_files):
    # Create a MainSQL.sql file in the patch directory
    with open(os.path.join(patch_directory, "MainSQL.sql"), "w") as main_sql:
        main_sql.write("promp &&HOST\n")
        main_sql.write("promp &&PERSON\n")
        main_sql.write("set echo on\n\n")
        if database_modified_files:
            for file in database_modified_files:
            
                file = file.replace('/', '\\')
                dest_path = file
                dest_path = dest_path.replace('Database\\', f'{patch_directory}\\DB\\')  # Replace Database path

                dest_dir = os.path.dirname(dest_path)  # Get the directory of the destination path
                os.makedirs(dest_dir, exist_ok=True)  # Create the directory structure if it doesn't exist
                
                try:
                    shutil.copy2(directory + file, dest_dir)  # Copy the file to the destination directory
                except FileNotFoundError as e:
                    print(f"File not found: {file} - {e}")
                except Exception as e:
                    print(f"Error copying file: {file} - {e}")

                schema = file.split('\\')[1]  # Get schema from the path
                dest = f"DB\\{file.replace('Database/', '')}"  # Construct destination path for SQL command
                write_sql_commands(main_sql, dest, schema)
        if sql_files:
            for file in sql_files:
                if 'MainSQL.sql' not in file:
                    shutil.copy2(file, os.path.join(patch_directory, "SCRIPT"))
                    dest = f"SCRIPT/{os.path.basename(file)}"
                    write_sql_commands(main_sql, dest, None)

def write_sql_commands(sql_file, file_path, schema):
    """Writes SQL commands to the specified SQL file."""
    sql_file.write("set scan on\n")
    if schema:
        sql_file.write(f"connect {schema}/{schema}@&&HOST\n")
    else:
        sql_file.write("#WARNING connect schema/schema@&&HOST\n")
    sql_file.write("set scan off\n")
    sql_file.write("set echo off\n")
    sql_file.write(f"prompt Loading \"{file_path}\" ...\n")
    sql_file.write(f"@@\"{file_path}\"\n")
    sql_file.write("show error\n")
    sql_file.write("set echo on\n\n")

def create_web_files(directory, patch_directory, web_modified_files):
    if web_modified_files:
        for file in web_modified_files:
            file = file.replace('/', '\\')
            dest_path = file
            dest_path = file.replace('webpage\\', f'{patch_directory}\\Web\\')
            dest_dir = os.path.dirname(dest_path)
            os.makedirs(dest_dir, exist_ok=True)
            shutil.copy2(directory + file, dest_dir)

def get_current_branch(directory):
    # Get the current Git branch
    result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=directory,
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        return result.stdout.strip()
    else:
        print(f"Error getting current branch: {result.stderr}")
        return None
