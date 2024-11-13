"""ECFSdownloader Task."""
import os
import subprocess
from glob import glob
from datetime import datetime

from ..methods import ConfigSpaveripy, hours_between_dates, lead_time_replace
from deode.tasks.base import Task


class ExpsTransfer(Task):
    """Link observation files to verif directory."""

    def __init__(self, config):
        """Construct object.

        Args:
            config (deode.ParsedConfig): Configuration
        """
        Task.__init__(self, config, __name__)

        self.config_verif = ConfigSpaveripy(self.config)
        self.date_format = "%Y%m%d%H"
        self._dest_dir = None

    def execute(self):
        inits_str, lts_str = self.config_verif._get_times_args()
        for t_ini, t_end in zip(inits_str, lts_str):
            self._check_dest_dir(t_ini)
            if not self._files_exist_in_dest(t_ini, t_end):
                try:
                    self._transfer_files_from_scratch(t_ini)
                except Exception as e:
                    self._transfer_files_from_ecfs(t_ini)

    def _check_dest_dir(self, init_time):
        dest_dir_format = self.config_verif.archive
        date_init = datetime.strptime(init_time, self.date_format)
        dest_dir = date_init.strftime(dest_dir_format)
        if not os.path.exists(dest_dir):
            print(
                f"Destination directory '{dest_dir}' does not exist. "
                "Creating it."
            )
            os.makedirs(dest_dir)
        else:
            print(f"Destination directory '{dest_dir}' already exists.")
        self._dest_dir = dest_dir

    def _files_exist_in_dest(self, time_ini, time_end):
        file_format = self.config_verif.file_fp
        date_ini = datetime.strptime(time_ini, self.date_format)
        date_end = datetime.strptime(time_end, self.date_format)
        fcst = hours_between_dates(date_ini, date_end)
        for lead_time in range(fcst + 1):
            file_name = lead_time_replace(file_format, lead_time)
            file_path = os.path.join(self._dest_dir, file_name)
            if not os.path.isfile(file_path):
                print(
                    f"File '{file_name}' does not exist in the destination "
                    "directory."
                )
                return False
        print(
            "All files are already downloaded in the destination directory."
        )
        return True

    def _transfer_files_from_scratch(self, init_time):
        source_dir_format = self.config_verif.ext_archive
        file_format = self.config_verif.file_fp

        date_init = datetime.strptime(init_time, self.date_format)
        source_dir = date_init.strftime(source_dir_format)
        file_name = lead_time_replace(file_format)
        files_path = os.path.join(source_dir, file_name)
        list_files = glob(files_path)
        list_files.sort()

        try:
            print(
                f"Copying {file_name} from {source_dir} to {self._dest_dir}."
            )
            subprocess.run(
                ["cp", *list_files, self._dest_dir], check=True
            )
        except subprocess.CalledProcessError as e:
            print(f"Error while copying '{file_name}': {e}")

    def _transfer_files_from_ecfs(self, init_time):
        source_dir_format = self.config_verif.ecfs_archive
        file_format = self.config_verif.file_fp

        date_init = datetime.strptime(init_time, self.date_format)
        source_dir = date_init.strftime(source_dir_format)
        file_name = lead_time_replace(file_format)
        files_path = os.path.join(source_dir, file_name)

        try:
            print(
                f"Copying {file_name} from {source_dir} to {self._dest_dir}."
            )
            subprocess.run(
                ["ecp", files_path, self._dest_dir], check=True
            )
        except subprocess.CalledProcessError as e:
            print(f"Error while copying '{file_name}': {e}")
