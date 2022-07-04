#  ECSTATIC: Extensible, Customizable STatic Analysis Tester Informed by Configuration
#
#  Copyright (c) 2022.
#
#  This program is free software: you can redistribute it and/or modify
#      it under the terms of the GNU General Public License as published by
#      the Free Software Foundation, either version 3 of the License, or
#      (at your option) any later version.
#
#      This program is distributed in the hope that it will be useful,
#      but WITHOUT ANY WARRANTY; without even the implied warranty of
#      MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#      GNU General Public License for more details.
#
#      You should have received a copy of the GNU General Public License
#      along with this program.  If not, see <https://www.gnu.org/licenses/>.

import argparse
import logging
import os
import shutil
import subprocess
import sys
import tempfile
from abc import abstractmethod, ABC
from dataclasses import dataclass
from functools import partial
from multiprocessing.dummy import Pool
from pathlib import Path
from typing import Optional, Callable, TypeAlias, Iterable, List

import dill as pickle

from src.ecstatic.readers.AbstractReader import AbstractReader
from src.ecstatic.runners.AbstractCommandLineToolRunner import AbstractCommandLineToolRunner
from src.ecstatic.util.BenchmarkReader import validate, logger
from src.ecstatic.util.PotentialViolation import PotentialViolation
from src.ecstatic.util.UtilClasses import FinishedFuzzingJob
from src.ecstatic.violation_checkers.AbstractViolationChecker import get_file_name, AbstractViolationChecker

DeltaDebuggingPredicate: TypeAlias = Callable[[PotentialViolation], bool]


@dataclass
class DeltaDebuggingJob:
    predicate: DeltaDebuggingPredicate
    potential_violation: PotentialViolation
    runner: AbstractCommandLineToolRunner
    reader: AbstractReader
    violation_checker: AbstractViolationChecker


class AbstractDeltaDebugger(ABC):

    @abstractmethod
    def make_predicates(self, potential_violation: PotentialViolation) -> Iterable[DeltaDebuggingPredicate]:
        """
        Creates the predicate(s) for the delta debugger. Each predicate returned will create a delta debugging
        job.
        @param potential_violation: The potential violation we are delta debugging on.
        @return: The predicate that the delta debugger should check.
        """
        pass

    def __init__(self, runner: AbstractCommandLineToolRunner, reader: AbstractReader,
                 violation_checker: AbstractViolationChecker):
        self.runner = runner
        self.reader = reader
        self.violation_checker = violation_checker

    def delta_debug(self, potential_violation: PotentialViolation, campaign_directory: str, timeout: Optional[int]):
        for index, predicate in enumerate(self.make_predicates(potential_violation)):
            # First, create artifacts. We need to pickle the violation, as well as creating the script.
            directory = os.path.abspath(os.path.join(campaign_directory, 'deltadebugging',
                                                     os.path.dirname(get_file_name(potential_violation)),
                                                     os.path.basename(potential_violation.job1.job.target.name),
                                                     str(index)))
            print(f"Making delta debugging directory {directory}")
            if os.path.exists(os.path.join(directory, "log.txt")):
                logger.critical(
                    f'Delta debugging result {os.path.join(directory, "log.txt")} already exists. Not removing. Skipping this violation.')
                return None
            if os.path.exists(directory):
                logger.info("Ignoring existing result")
                shutil.rmtree(directory, ignore_errors=True)
            Path(directory).mkdir(exist_ok=True, parents=True)

            # Copy benchmarks folder so that we have our own code location.
            shutil.copytree(src="benchmarks", dst=os.path.join(directory, "benchmarks"))
            potential_violation.job1.job.target = validate(potential_violation.job1.job.target, directory)
            logging.info(f'Moved benchmark, so target is now {potential_violation.job1.job.target}')
            potential_violation.job2.job.target = potential_violation.job1.job.target
            try:
                if len(potential_violation.job1.job.target.sources) == 0:
                    logging.critical(f"Cannot delta debug benchmark record {potential_violation.job1.job.target} without sources.")
                    return None
            except TypeError:
                logging.exception(potential_violation.job1.job.target)

            # Then, create the script.
            job = DeltaDebuggingJob(predicate=predicate,
                                    runner=self.runner,
                                    reader=self.reader,
                                    violation_checker=self.violation_checker,
                                    potential_violation=potential_violation)

            script_location = self.create_script(job, directory)
            build_script = potential_violation.job1.job.target.build_script
            os.chmod(build_script, 700)
            os.chmod(script_location, 700)

            cmd = self.get_delta_debugger_cmd(build_script, directory, potential_violation, script_location)

            print(f"Running delta debugger with cmd {' '.join(cmd)}")
            subprocess.run(cmd, stdout=sys.stdout, stderr=sys.stderr, text=True)
            print("Delta debugging completed.")

    @abstractmethod
    def get_delta_debugger_cmd(self, build_script, directory, potential_violation, script_location):
        # Then, run the delta debugger
        cmd: List[str] = "java -jar /SADeltaDebugger/ViolationDeltaDebugger/target/ViolationDeltaDebugger-1.0" \
                         "-SNAPSHOT-jar-with-dependencies.jar".split(' ')
        sources = [['--sources', s] for s in potential_violation.job1.job.target.sources]
        [cmd.extend(s) for s in sources]
        cmd.extend(["--target", potential_violation.job1.job.target.name])
        cmd.extend(["--bs", os.path.abspath(build_script)])
        cmd.extend(["--vs", os.path.abspath(script_location)])
        cmd.extend(["--logs", os.path.join(directory, "log.txt")])
        cmd.extend(['--hdd'])
        cmd.extend(['--class-reduction'])
        cmd.extend(['--timeout', '120'])
        return cmd

    def create_script(self, job: DeltaDebuggingJob, directory: str) -> str:
        """

        :param job: The delta debugging job.
        :param directory: Where to put the script.
        :return: The location of the script.
        """
        job_tmp = tempfile.NamedTemporaryFile(delete=False, dir=directory)
        pickle.dump(job, open(job_tmp.name, 'wb'))
        job_tmp.close()

        with tempfile.NamedTemporaryFile(mode='w', dir=directory, delete=False) as f:
            f.write("#!/bin/bash\n")
            cmd = f"deltadebugger {job_tmp.name}"
            f.write(cmd + "\n")
            result = f.name
            logger.info(f"Wrote cmd {cmd} to delta debugging script.")
        return result


def main():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    parser = argparse.ArgumentParser()
    parser.add_argument("job", help="The location of the pickled job.")
    args = parser.parse_args()

    with open(args.job, 'rb') as f:
        job: DeltaDebuggingJob = pickle.load(f)

    logger.info(f'Read delta debugging job from {args.job}')
    # Create tool runner.
    tmpdir = tempfile.TemporaryDirectory()

    partial_function = partial(job.runner.run_job, output_folder=tmpdir.name)
    with Pool(2) as p:
        finished_jobs: Iterable[FinishedFuzzingJob] = p.map(partial_function, [job.potential_violation.job1.job,
                                                                               job.potential_violation.job2.job])
    violations: Iterable[PotentialViolation] = \
        job.violation_checker.check_violations(
            [f for f in finished_jobs if f is not None and f.results_location is not None], tmpdir.name)
    relevant_violation = [v for v in violations if v.partial_orders == job.potential_violation.partial_orders]
    if num_violations := len(relevant_violation) > 0:
        raise RuntimeError(f"{num_violations} potential violations detected on partial order set "
                           f"{job.potential_violation.partial_orders}. "
                           f"Not sure how to proceed.")
    else:
        exit(0 if job.predicate(relevant_violation[0]) else 1)
