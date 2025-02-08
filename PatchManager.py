from registery_manager import RegistryManager
from gui.main_window import MainWindow
import winreg
import os

def get_ini_path_from_registry():
    """
    Récupère le chemin du fichier INI à partir du registre.
    Tente d'abord la vue 64 bits, puis la vue 32 bits si nécessaire.
    """
    registry_manager = RegistryManager()
    key_path = r"SOFTWARE\CMA Solutions\CMA Central"
    value_name = "CONFIG_PATH"

    # Si non trouvé, essayer en mode 32 bits
    ini_path = registry_manager.read_value(key_path, value_name, is_32bit=True)
    if ini_path:
        print(f"Fichier INI trouvé (32 bits) : {ini_path}")
        return ini_path + "CMATC.INI"

if __name__ == "__main__":
    # Récupérer le chemin du fichier INI depuis le registre
    ini_file = get_ini_path_from_registry()
    if ini_file:
        # Lancement de l'interface graphique avec le fichier INI
        app = MainWindow(ini_file)
        app.mainloop()
    else:
        print("Impossible de trouver le chemin du fichier INI dans le registre.")