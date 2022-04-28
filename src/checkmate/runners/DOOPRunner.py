import logging
import os
import shutil
import subprocess
import time
from typing import List

from src.checkmate.runners.CommandLineToolRunner import CommandLineToolRunner
from src.checkmate.util.UtilClasses import BenchmarkRecord, FuzzingJob

logger = logging.getLogger("DOOPRunner")


class DOOPRunner(CommandLineToolRunner):
    def get_whole_program(self) -> List[str]:
        return ["--ignore-main-method"]

    def get_input_option(self, benchmark_record: BenchmarkRecord) -> List[str]:
        return f"-i {benchmark_record.name}".split(" ")

    def get_output_option(self, output_file: str) -> List[str]:
        return []

    def get_task_option(self, task: str) -> str:
        if task == 'cg':
            pass
        else:
            raise NotImplementedError(f'DOOP does not support task {task}.')

    def get_base_command(self) -> List[str]:
        return ["doop", "--ignore-main-method", "-t", "120"]

    def run_from_cmd(self, cmd: List[str], job: FuzzingJob, output_file: str) -> str:
        cmd.extend(self.get_input_option(job.target))
        logger.info(f"Cmd is {cmd}")
        ps = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in ps.stdout.split("\n"):
            if line.startswith("Making database available"):
                output_dir = line.split(" ")[-1]
                logger.info(f"Output directory: {output_dir}")
                break
        try:
            intermediate_file = os.path.join(output_dir, "CallGraphEdge.csv")
        except UnboundLocalError as ule:
            raise RuntimeError(ps.stdout)
        shutil.move(intermediate_file, output_file)
        logger.info(f'Now removing directory {output_dir}')
        shutil.rmtree(os.path.realpath(output_dir))
        return ps.stdout
