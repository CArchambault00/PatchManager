import winreg

class RegistryManager:
    @staticmethod
    def read_value(key_path, value_name, hive=winreg.HKEY_LOCAL_MACHINE, is_32bit=False):
        try:
            access = winreg.KEY_READ | (winreg.KEY_WOW64_32KEY if is_32bit else winreg.KEY_WOW64_64KEY)
            registry_key = winreg.OpenKey(hive, key_path, 0, access)
            value, _ = winreg.QueryValueEx(registry_key, value_name)
            winreg.CloseKey(registry_key)
            return value
        except FileNotFoundError:
            print(f"Key '{key_path}' or value '{value_name}' not found in the registry.")
            return None
        except Exception as e:
            print(f"Error reading registry: {e}")
            return None