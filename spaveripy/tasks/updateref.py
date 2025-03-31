"""UpdateRef Task."""
import os

from ..methods import ConfigSpaveripy
from deode.tasks.base import Task
from deode.tasks.batch import BatchJob


class UpdateRef(Task):
    """Update the Global DT's config file"""

    def __init__(self, config):
        """Construct object.

        Args:
            config (deode.ParsedConfig): Configuration
        """
        Task.__init__(self, config, __name__)

        path_task = os.path.dirname(os.path.abspath(__file__))
        os.chdir(path_task)
        self.load_var_env("../../config/user_settings.env")
        self.verif_home = os.environ.get("TOOL_DIR")
        self.config_verif = ConfigSpaveripy(self.config)
        self.exp_name = "iekm"
        self.model = "DestinE 4.4 km"
        self.path_archive = os.path.join(self.config_verif.path_ref_gribs,"%Y%m%d")        
        self.filename = "ICMGG+%Lgrib2.sfc"
        self._exp_args = None
        self._vars_dt = {
            "pcp": {
                "var": "tp",
                "accum": True,
                "verif_0h": False,
                "postprocess": "m_mm",
                "find_min": False
            }
        }

    def execute(self):
        os.chdir(str(self.verif_home))
        case = self.config_verif.case
        exp = self.config_verif.exp
        exp_ref = self.write_config_dt()
        print(f"CASE VALUE: {case}")
        print(f"EXP VALUE: {exp}")
        print(f"EXP REF VALUE: {exp_ref}")

    def write_config_dt(self):
        """Write the yaml configuration file of the experiment

        Returns:
            exp (str) : experiment's name
        """
        inits_str, fcsts_str = self.config_verif._get_times_args()
        init_dict = {}
        for k, v in zip(inits_str, fcsts_str):
            if k[-2:] == "00":
                init_dict.update({
                    k: {
                        "path": 0,
                        "fcast_horiz": v
                    }
                })

        exp = self.exp_name
        config_filename = os.path.join(
            self.verif_home, f"config/exp/config_{exp}.yaml"
        )
        if os.path.isfile(config_filename):
            self._exp_args = ConfigSpaveripy.load_yaml(config_filename)
            self._exp_args["inits"].update(init_dict)
        else:
            self._exp_args = ConfigSpaveripy.load_yaml(
                os.path.join(self.verif_home, "config/templates/config_exp.yaml")
            )
            self._exp_args["model"]["name"] = self.model
            self._exp_args["format"]["filepaths"] = [self.path_archive,]
            self._exp_args["format"]["filename"] = self.filename
            self._exp_args["format"]["fileformat"] = "Grib"
            self._exp_args["inits"] = init_dict
            self._exp_args["vars"] = self._vars_dt

        ConfigSpaveripy.save_yaml(config_filename, self._exp_args)
        return exp

    @staticmethod
    def load_var_env(file_env):
        with open(file_env) as f:
            for line in f:
                if line.startswith("#") or not line.strip():
                    continue
                key, value = line.strip().split("=", 1)
                os.environ[key] = value.strip('"').strip("'")

