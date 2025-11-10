import configparser
import os
from typing import Optional

class INIManager:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.config = configparser.ConfigParser()
        self.reload()

    def reload(self):
        if os.path.exists(self.file_path):
            self.config.read(self.file_path)
        else:
            open(self.file_path, 'w').close()

    def get(self, section: str, option: str, fallback: Optional[str] = None) -> Optional[str]:
        return self.config.get(section, option, fallback=fallback)

    def get_int(self, section: str, option: str, fallback: Optional[int] = None) -> Optional[int]:
        return self.config.getint(section, option, fallback=fallback)

    def get_bool(self, section: str, option: str, fallback: Optional[bool] = None) -> Optional[bool]:
        return self.config.getboolean(section, option, fallback=fallback)

    def set(self, section: str, option: str, value: str):
        if not self.config.has_section(section):
            self.config.add_section(section)
        self.config.set(section, option, value)
        self.save()

    def remove_option(self, section: str, option: str):
        if self.config.has_section(section) and self.config.has_option(section, option):
            self.config.remove_option(section, option)
            self.save()

    def remove_section(self, section: str):
        if self.config.has_section(section):
            self.config.remove_section(section)
            self.save()

    def save(self):
        with open(self.file_path, "w") as f:
            self.config.write(f)
