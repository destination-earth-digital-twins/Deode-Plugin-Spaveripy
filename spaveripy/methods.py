"""ConfigSpaveripy class"""
import os
import re
from datetime import datetime, timedelta
from dateutil import parser
import pandas as pd
import yaml
import pyproj

from deode.toolbox import Platform


def hours_between_dates(date_ini, date_end):
    hours = int((date_end - date_ini).total_seconds() / 3600.0)
    return hours

def replace_function(text, replace_with):
    if isinstance(replace_with, int):
        return str(replace_with).zfill(len(text) - 1)
    else:
        return "*"

def lead_time_replace(text, replace_with = '*'):
    pattern = r'(%L+)'
    new_text = re.sub(pattern, lambda match: replace_function(match.group(0), replace_with), text)
    return new_text

class ConfigSpaveripy(object):
    """verification exercise set-up"""

    def __init__(self, config):
        """Construct the config object.

        Args:
            config (deode.ParsedConfig): Configuration
        """
        self.config = config
        self.platform = Platform(config)
        self.verif_user = self.platform.get_value("submission.spaveripy_group.ENV.VERIF_USER")
        self.duser= self.platform.get_value("submission.spaveripy_group.ENV.DUSER")        
        self.home = self.platform.get_value("submission.spaveripy_group.ENV.TOOL_DIR")
        self.obs = self.platform.get_value("submission.spaveripy_group.ENV.VERIF_OBS")
        self.path_ref_gribs=self.platform.get_value("submission.spaveripy_group.ENV.PATH_REF_GRIBS")
        self.ref_name = self.platform.get_value("submission.spaveripy_group.ENV.REF_NAME")
        self.use_operational_indexing = self.platform.get_value("submission.spaveripy_group.ENV.USE_OPERATIONAL_INDEXING")
        self.dest_dir = self.platform.get_value("submission.spaveripy_group.ENV.DEST_DIR")
        self.plugin_dir = self.platform.get_value("submission.spaveripy_group.ENV.PLUGIN_DIR")
        self.dw_dir = self.platform.get_value("submission.spaveripy_group.ENV.DW_DIR")
        self.tool_dir = self.platform.get_value("submission.spaveripy_group.ENV.TOOL_DIR")
        self.launchs_dir = self.platform.get_value("submission.spaveripy_group.ENV.LAUNCHS_DIR")        	
        self.cnmexp = self.config["general.cnmexp"]
        self.csc = self.config["general.csc"]
        self.cycle = self.config["general.cycle"]
        self.event_type = self.config["general.event_type"]
        self.start = self.platform.get_value("general.times.start")
        self.cycle_length = self.platform.get_value("general.times.cycle_length")
        self.forecast_range = self.platform.get_value("general.times.forecast_range")
        self.domain_name = self.config["domain.name"]
        self.nimax = self.platform.get_value("domain.nimax")
        self.njmax = self.platform.get_value("domain.njmax")
        self.domain_number = self.platform.get_value("domain.number")
        self.xdx = self.platform.get_value("domain.xdx")
        self.xdy = self.platform.get_value("domain.xdy")
        self.xlatcen = self.platform.get_value("domain.xlatcen")
        self.xloncen = self.platform.get_value("domain.xloncen")
        self.xlat0 = self.platform.get_value("domain.xlat0")
        self.xlon0 = self.platform.get_value("domain.xlon0")
        self.case_identifier = self.config["system.case_identifier"]
        if str(self.use_operational_indexing).strip().lower() in {"yes", "y", "true"}:
           inits_str, fcsts_str = self._get_times_args()
           # Extract year, month, day from the first init string
           first_init = inits_str[0]  # Example: "2025040412"
           dt = datetime.strptime(first_init, "%Y%m%d%H")
           yy = dt.strftime("%Y")  # 4 digits
           mm = dt.strftime("%m")
           dd = dt.strftime("%d")
           event_type = self.event_type
           domain_number  = self.domain_number
           self.relative_indexed_path=f"{yy}/{mm}/{dd}/{event_type}/{domain_number}"
        else:
           self.relative_indexed_path="/"
        self.file_fp = self._set_file_fp()
        self.archive = self._set_archive()
        if self.duser is not None:
            self.ext_archive = self._set_ext_archive()
            self.ecfs_archive = self._set_ecfs_archive()
        self.case = self._set_case()
        self.exp = self._set_exp()

        self._case_args = None
        self._exp_args = None
        self._vars_deode = {
            "pcp": {
                "var": "tp",
                "accum": True,
                "verif_0h": False,
                "postprocess": "None",
                "find_min": False
            },
            "rain": {
                "var": "tirf",
                "accum": True,
                "verif_0h": False,
                "postprocess": "None",
                "find_min": False
            },
            "lat": {
                "var": "lat",
                "description": "latitude coordinates in degrees"
            },
            "lon": {
                "var": "lon",
                "description": "longitude coordinates in degrees"
            }
        }

    def write_config_case(self):
        """Write the yaml configuration file of the case study

        Returns:
            case (str) : name of the case study
        """
        inits_str, fcsts_str = self._get_times_args()
        lon_min, lon_max, lat_min, lat_max = self._compute_extension()
        case=self.case
        relative_indexed_path=self.relative_indexed_path
        config_filename = os.path.join(
            self.home, f"config/Case/{relative_indexed_path}/config_{case}.yaml"
        )
        if not os.path.isfile(config_filename):
            self._case_args = ConfigSpaveripy.load_yaml(
                os.path.join(self.home, "config/templates/config_Case.yaml")
            )
            self._case_args["dates"]["ini"] = inits_str[0]
            self._case_args["dates"]["end"] = fcsts_str[-1]
            self._case_args["location"]["NOzoom"] = [
                lon_min, lon_max, lat_min, lat_max
            ]
            dd = 1.0
            self._case_args["verif_domain"] = {
                inits_str[0]: [
                    lon_min + dd, lon_max - dd, lat_min + dd, lat_max - dd
                ]
            }
            os.makedirs(os.path.dirname(config_filename), exist_ok=True)
            ConfigSpaveripy.save_yaml(config_filename, self._case_args)
            print("Wrote config_case at {config_filename}")
        return case

    def write_config_exp(self):
        """Write the yaml configuration file of the experiment

        Returns:
            exp (str) : experiment's name
        """
        inits_str, fcsts_str = self._get_times_args()
        init_dict = {}
        for k, v in zip(inits_str, fcsts_str):
            init_dict.update({
                k: {
                    "path": 0,
                    "fcast_horiz": v
                }
            })
        exp = self.exp
        relative_indexed_path=self.relative_indexed_path
        config_filename = os.path.join(
            self.home, f"config/exp/{relative_indexed_path}/config_{exp}.yaml"
        )
        if os.path.isfile(config_filename):
            self._exp_args = ConfigSpaveripy.load_yaml(config_filename)
            self._exp_args["inits"].update(init_dict)
        else:
            self._exp_args = ConfigSpaveripy.load_yaml(
                os.path.join(self.home, "config/templates/config_exp.yaml")
            )
            self._exp_args["model"]["name"] = self.csc
            self._exp_args["format"]["filepaths"] = [self.archive,]
            self._exp_args["format"]["filename"] = self.file_fp
            self._exp_args["format"]["fileformat"] = "Grib"
            self._exp_args["inits"] = init_dict
            self._exp_args["vars"] = self._vars_deode

        os.makedirs(os.path.dirname(config_filename), exist_ok=True)
        ConfigSpaveripy.save_yaml(config_filename, self._exp_args)
        print("Wrote config_exp at {config_filename}")

        return exp

    def _get_times_args(self):
        date_ini = parser.parse(self.start)
        freq = self.cycle_length[2:].lower()
        match = re.match(r"P(\d+)(D|T(\d+)H)", self.forecast_range)
        if match:
            if match.group(2) == "D":  # Days format (e.g., P2D)
               fcst = int(match.group(1)) * 24
            else:  # Hours format (e.g., PT48H)
               fcst = int(match.group(3))
        else:
            raise ValueError(f"Unrecognized forecast format: {forecast_range}")
        date_end = date_ini + timedelta(hours=fcst)  # since date_end disappeared from config files
        dates = pd.date_range(date_ini, date_ini, freq=timedelta(hours=fcst)).to_pydatetime() # Hardcode single runs for now
        inits = [date.strftime("%Y%m%d%H") for date in dates]

        fcsts = []
        for date in dates:
            date_fcst = date + timedelta(hours=fcst)
            fcsts.append(date_fcst.strftime("%Y%m%d%H"))
        return inits, fcsts

    def _compute_extension(self):
        proj4 = "+proj=lcc " \
            + f"+lat_0={self.xlat0} +lon_0={self.xlon0} " \
            + f"+lat_1={self.xlat0} +lat_2={self.xlat0}"
        projection = pyproj.Proj(proj4)
        half_height = int(self.njmax / 2) * self.xdy
        half_width = int(self.nimax / 2) * self.xdx
        x_0, y_0 = projection(self.xloncen, self.xlatcen)
        lon_0, lat_max = projection(x_0, y_0 + half_height, inverse=True)
        lon_min, lat_ul = projection(
            x_0 - half_width, y_0 + half_height, inverse=True
        )
        lon_max, lat_ur = projection(
            x_0 + half_width, y_0 + half_height, inverse=True
        )
        lon_ll, lat_min = projection(
            x_0 - half_width, y_0 - half_height, inverse=True
        )
        return lon_min, lon_max, lat_min, lat_max

    def _set_case(self):
        inits_str, _ = self._get_times_args()
        ymd_start = inits_str[0][:-2]
        case = "_".join([self.event_type, self.domain_name, ymd_start])
        return case

    def _set_exp(self):
        abbr = {"HARMONIE_AROME": "HA", "AROME": "AR", "ALARO": "AL"}
        cycle_lower = self.cycle.lower()
        csc_replace = abbr[self.csc]
        exp = "_".join(
            [self.cnmexp, cycle_lower, csc_replace, self.domain_name]
        )
        return exp

    def _set_file_fp(self):
        duration_raw = self.config["file_templates.duration.archive"]
        duration_replace = (
            duration_raw.replace("@LLLH@", "%LLLL")
                        .replace("@LM@", "00")
                        .replace("@LS@", "00")
        )
        duration = self.platform.get_value("file_templates.duration.archive")
        file_fp = self.platform.get_value("file_templates.fullpos.archive")
        return file_fp.replace(duration, duration_replace)

    def _set_archive(self):
        archive_timestamp_raw = self.config["system.archive_timestamp"]
        archive_timestamp_replace = (
            archive_timestamp_raw.replace("@YYYY@", "%Y")
                                 .replace("@MM@", "%m")
                                 .replace("@DD@", "%d")
                                 .replace("@HH@", "%H")
        )
        archive_timestamp = self.platform.get_system_value("archive_timestamp")
        archive = self.platform.get_system_value("archive")
        return archive.replace(archive_timestamp, archive_timestamp_replace)

    def _set_ext_archive(self):
        archive = self.archive
        ext_archive = archive.replace(self.verif_user, self.duser)
        return ext_archive

    def _set_ecfs_archive(self):
        archiving_prefix_raw = self.config["archiving.prefix.ecfs"]
        archiving_prefix_replace = archiving_prefix_raw.replace("@USER@", self.duser)
        archiving_prefix = self.platform.substitute(archiving_prefix_replace)
        archive_timestamp_raw = self.config["system.archive_timestamp"]
        archive_timestamp_replace = (
            archive_timestamp_raw.replace("@YYYY@", "%Y")
                                 .replace("@MM@", "%m")
                                 .replace("@DD@", "%d")
                                 .replace("@HH@", "%H")
        )
        #archiving_ecfs_raw = self.config["archiving.hour.ecfs.grib_files.outpath"]
        archiving_ecfs_raw = self.config["archiving.hour.ecfs.fpgrib_files.outpath"]  #for tag 0.15.0 and newer
        archiving_ecfs_raw = self.config["system.sub_casedir"]
        explicit_case_identifier=self.case_identifier.replace("@XDX@",str(self.xdx)).replace("@EVENT_TYPE@",self.event_type).replace("@DOMAIN_NUMBER@",str(self.domain_number)).replace("@CSC@",self.csc)
        archiving_ecfs_replace = archiving_ecfs_raw.replace("@ARCHIVE_TIMESTAMP@", archive_timestamp_replace).replace("@CASE_IDENTIFIER@",explicit_case_identifier)
        print("archiving_ecfs_raw is")
        print(archiving_ecfs_raw)
        print("archiving_ecfs_replace is") 
        print(archiving_ecfs_replace)
        ecfs_archive = os.path.join(archiving_prefix, archiving_ecfs_replace)
        return ecfs_archive

    @staticmethod
    def load_yaml(config_file):
        with open(config_file, 'r') as stream:
            data_loaded = yaml.safe_load(stream)
        return data_loaded

    def save_yaml(config_file, data):
        with open(config_file, "w") as stream:
            yaml.dump(data, stream, default_flow_style=False)
