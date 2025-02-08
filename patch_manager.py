import subprocess

class PatchManager:
    def __init__(self, db_host, db_user, db_password):
        self.db_host = db_host
        self.db_user = db_user
        self.db_password = db_password

    def run_sql_script(self, script_path):
        command = f'sqlplus {self.db_user}/{self.db_password}@{self.db_host} @{script_path}'
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return result.stdout

    def copy_files(self, source, destination):
        command = f'xcopy "{source}" "{destination}" /s /y /r'
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return result.stdout