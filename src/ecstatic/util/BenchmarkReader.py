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


import importlib
import json
import logging
import os.path

from jsonschema.validators import RefResolver, Draft7Validator

from src.ecstatic.util.ApplicationCodeFilter import ApplicationCodeFilter
from src.ecstatic.util.JavaApplicationCodeFilter import JavaApplicationCodeFilter
from src.ecstatic.util.UtilClasses import Benchmark, BenchmarkRecord

logger = logging.getLogger(__name__)


def try_resolve_path(path: str, root: str = "/") -> str:
    if path is None:
        return None
    logging.info(f'Trying to resolve {path} in {root}')
    if path.startswith("/"):
        path = path[1:]
    if os.path.exists(os.path.join(root, path)):
        return os.path.abspath(os.path.join(root, path))
    for rootdir, dirs, _ in os.walk(os.path.join(root, "benchmarks")):
        cur = os.path.join(os.path.join(root, "benchmarks"), rootdir)
        if os.path.exists(os.path.join(cur, path)):
            return os.path.join(cur, path)
        for d in dirs:
            if os.path.exists(os.path.join(os.path.join(cur, d), path)):
                return os.path.join(os.path.join(cur, d), path)
    raise FileNotFoundError(f"Could not resolve path {path}")


def validate(b: BenchmarkRecord, root: str = "/") -> BenchmarkRecord:
    """
    Validates a benchmark, resolving each of its paths to an absolute path.
    Searches in the supplied root directory.
    Parameters
    ----------
    benchmark : The benchmark to validate.
    root : Where to look for the benchmark files

    Returns
    -------
    A resolved benchmark
    """
    logger.info(f'Original benchmark record is {b}')
    b.name = try_resolve_path(b.name, root)
    b.depends_on = [try_resolve_path(d, root) for d in b.depends_on]
    b.sources = [try_resolve_path(s, root) for s in b.sources]
    b.build_script = try_resolve_path(b.build_script, root)
    logger.info(f'Resolved benchmark record to {b}')
    return b


class BenchmarkReader:
    def __init__(self,
                 schema: str = importlib.resources.path('src.resources.schema', 'benchmark.schema.json'),
                 application_code_filter: ApplicationCodeFilter = JavaApplicationCodeFilter()):
        self.schema = schema
        with open(schema, 'r') as f:
            self.schema = json.load(f)
        self.resolver = RefResolver.from_schema(self.schema)
        self.validator = Draft7Validator(self.schema, self.resolver)
        self.application_code_filter = application_code_filter

    def read_benchmark(self, file: str) -> Benchmark:
        with open(file, 'r') as f:
            index = json.load(f)
        self.validator.validate(index)
        benchmark = Benchmark([validate(BenchmarkRecord(**b)) for b in index['benchmark']])
        if self.application_code_filter is not None:
            benchmark = Benchmark([self.application_code_filter.find_application_packages(br) for br in benchmark.benchmarks])
        return benchmark

