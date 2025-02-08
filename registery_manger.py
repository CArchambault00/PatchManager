import winreg

class RegistryManager:
    @staticmethod
    def read_value(key_path, value_name, hive=winreg.HKEY_LOCAL_MACHINE, is_32bit=False):
        """
        Lit une valeur du registre Windows.
        :param key_path: Chemin de la clé (ex: "SOFTWARE\\CMA Solutions\\CMA Central")
        :param value_name: Nom de la valeur à lire (ex: "CONFIG_PATH")
        :param hive: Hive du registre (par défaut HKEY_LOCAL_MACHINE)
        :param is_32bit: Si True, accède à la vue 32 bits du registre.
        :return: La valeur lue ou None si la clé ou la valeur n'existe pas.
        """
        try:
            # Ajouter l'option pour accéder à la vue 32 bits si nécessaire
            access = winreg.KEY_READ | (winreg.KEY_WOW64_32KEY if is_32bit else winreg.KEY_WOW64_64KEY)
            registry_key = winreg.OpenKey(hive, key_path, 0, access)
            value, _ = winreg.QueryValueEx(registry_key, value_name)
            winreg.CloseKey(registry_key)
            return value
        except FileNotFoundError:
            print(f"La clé '{key_path}' ou la valeur '{value_name}' n'existe pas dans le registre.")
            return None
        except Exception as e:
            print(f"Erreur lors de la lecture du registre : {e}")
            return None