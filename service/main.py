
__author__ = 'Nicklas Boerjesson'
from plyer import notification
import os
from kivy.utils import platform

platform = platform()

if __name__ == '__main__':
    try:
        from syncservice import SyncService
    except Exception as e:
        notification.notify("Optimal File Sync Service", "Error in init :" + str(e))


    try:
        # Find home dir
        if platform == "android":
            _home = "/storage/emulated/0/Android/data/"
        else:
            _home = os.path.expanduser("~")
        # Check if there is a settings file there
        _config_path = os.path.join(_home, "se.optimalbpm.optimal_file_sync/config.txt")
        # Raise error if non existing config
        if not os.path.exists(_config_path):
            notification.notify("Optimal File Sync Service", "Could not find config: " + _config_path + ", quitting.")
        else:
            # Pass to service
            _service=SyncService(_cfg_file=_config_path)
            _service.start("Default")
    except Exception as e:
        notification.notify("Optimal File Sync Service", "Error finding config :" + str(e))




