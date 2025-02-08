import configparser
import re

class INIFileManager:
    def __init__(self, filename):
        self.filename = filename
        self.config = configparser.ConfigParser(strict=False)

    def _sanitize_ini_file(self):
        sanitized_lines = []
        try:
            with open(self.filename, "r", encoding="utf-8") as f:
                for line in f:
                    if not re.match(r"^\s*(//|')", line):
                        sanitized_lines.append(line)

            temp_filename = self.filename + ".tmp"
            with open(temp_filename, "w", encoding="utf-8") as f:
                f.writelines(sanitized_lines)

            return temp_filename
        except Exception as e:
            print(f"Error sanitizing INI file: {e}")
            return None

    def _read_config(self):
        sanitized_file = self._sanitize_ini_file()
        if sanitized_file:
            self.config.read(sanitized_file, encoding="utf-8")

    def read_key(self, section, key, default=None):
        self._read_config()
        return self.config.get(section, key, fallback=default)

    def write_key(self, section, key, value):
        self._read_config()
        if section not in self.config:
            self.config[section] = {}
        self.config[section][key] = value
        with open(self.filename, 'w', encoding="utf-8") as configfile:
            self.config.write(configfile)

    def read_section(self, section):
        self._read_config()
        return dict(self.config[section]) if section in self.config else {}

    def read_section_names(self):
        self._read_config()
        return self.config.sections()

    def get_environments(self):
        sections = self.read_section_names()
        return [section for section in sections if section.startswith("ENV")]

    def merge_duplicate_sections(self):
        self._read_config()
        merged_sections = {}

        for section in self.config.sections():
            if section not in merged_sections:
                merged_sections[section] = {}
            for key, value in self.config[section].items():
                merged_sections[section][key] = value

        with open(self.filename, 'w', encoding="utf-8") as configfile:
            for section, keys in merged_sections.items():
                configfile.write(f"[{section}]\n")
                for key, value in keys.items():
                    configfile.write(f"{key} = {value}\n")
                configfile.write("\n")