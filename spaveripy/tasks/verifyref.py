"""Verification Task."""
import os

from ..methods import ConfigSpaveripy
from deode.tasks.base import Task
from deode.tasks.batch import BatchJob


class VerifyRef(Task):
    """Compute FSS and SAL values"""

    def __init__(self, config):
        """Construct object.

        Args:
            config (deode.ParsedConfig): Configuration
        """
        Task.__init__(self, config, __name__)

        self.config_verif = ConfigSpaveripy(self.config)
        self.binary = "python3"
        self.batch = BatchJob(os.environ)

    def execute(self):
        os.chdir(self.config_verif.home)
        obs = self.config_verif.obs
        case = self.config_verif.case
        ref = self.config_verif.ref_name
        relative_indexed_path = self.config_verif.relative_indexed_path
        if "ECCODES_DEFINITION_PATH" in os.environ:
            del os.environ["ECCODES_DEFINITION_PATH"]
        self.batch.run(f"{self.binary} main.py --obs {obs} --case {case} --exp {ref} --relative_indexed_path={relative_indexed_path} --link_obs --run_regrid --run_plot_regrid --run_verif --run_panels")
        #self.batch.run(f"{self.binary} main.py --obs {obs} --case {case} --exp {ref} --relative_indexed_path={relative_indexed_path} --run_verif --run_panels")
        
