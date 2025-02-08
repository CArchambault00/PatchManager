import os
import shutil
import subprocess
from utils import get_current_branch, get_committed_and_pushed_files

def generate_patch(directory, version):
    web_modified_files = get_committed_and_pushed_files(directory, "webpage/")
    database_modified_files = get_committed_and_pushed_files(directory, "Database/")
    sql_files = get_sql_files(directory)

    patch_directory = create_patch_directory(directory, version)
    directory = directory + "\\"
    create_database_files(directory, patch_directory, database_modified_files, sql_files)
    create_web_files(directory, patch_directory, web_modified_files)

def get_sql_files(directory):
    sql_files = []
    for file in os.listdir(directory):
        if file.endswith(".sql") and file != "MainSQL.sql":
            sql_files.append(os.path.join(directory, file))
    return sql_files

def create_patch_directory(directory, version):
    patch_directory = os.path.join(directory, "Patches", version)
    os.makedirs(patch_directory, exist_ok=True)
    return patch_directory

def create_database_files(directory, patch_directory, database_modified_files, sql_files):
    with open(os.path.join(patch_directory, "MainSQL.sql"), "w") as main_sql:
        main_sql.write("promp &&HOST\n")
        main_sql.write("promp &&PERSON\n")
        main_sql.write("set echo on\n\n")
        if database_modified_files:
            for file in database_modified_files:
                file = file.replace('/', '\\')
                dest_path = file.replace('Database\\', f'{patch_directory}\\DB\\')
                dest_dir = os.path.dirname(dest_path)
                os.makedirs(dest_dir, exist_ok=True)
                shutil.copy2(directory + file, dest_dir)
                schema = file.split('\\')[1]
                dest = f"DB\\{file.replace('Database/', '')}"
                write_sql_commands(main_sql, dest, schema)
        if sql_files:
            for file in sql_files:
                if 'MainSQL.sql' not in file:
                    shutil.copy2(file, os.path.join(patch_directory, "SCRIPT"))
                    dest = f"SCRIPT/{os.path.basename(file)}"
                    write_sql_commands(main_sql, dest, None)

def write_sql_commands(sql_file, file_path, schema):
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
            dest_path = file.replace('webpage\\', f'{patch_directory}\\Web\\')
            dest_dir = os.path.dirname(dest_path)
            os.makedirs(dest_dir, exist_ok=True)
            shutil.copy2(directory + file, dest_dir)