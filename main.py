import copy
from time import sleep

__author__ = 'Nicklas Boerjesson'
__version__ = '0.1'

from kivy.app import App
from kivy.utils import platform
platform = platform()
from gui.settings import SettingsFrame
from plyer import notification
import os
from shutil import copy

import sys
# If not, large directory structures will cause an error on Android
sys.setrecursionlimit(1000)

class OptimalFileSyncApp(App):
    settingsframe = None

    def build(self):
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
                if not os.path.exists(os.path.join(_home, "se.optimalbpm.optimal_file_sync")):
                    os.mkdir(os.path.join(_home, "se.optimalbpm.optimal_file_sync"))
                if platform == "android":
                    copy("default_config_android.txt", _config_path)
                else:
                    copy("default_config_linux.txt", _config_path)

                notification.notify("Optimal File Sync Service", "First time, using default config.")

            self.settingsframe = SettingsFrame()
            self.settingsframe.init(_cfg_file=_config_path)
            return self.settingsframe
        except Exception as e:
            notification.notify("Optimal File Sync Service", "Error finding config :" + str(e))

    def on_stop(self):
        self.settingsframe.save_settings()


if __name__ == "__main__":
    try:
        OptimalFileSyncApp().run()
    except Exception as e:
        notification.notify(title="Optimal Backup error:", message =  str(e))
        raise

