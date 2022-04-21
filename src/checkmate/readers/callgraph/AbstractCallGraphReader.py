import logging
from abc import ABC, abstractmethod
from typing import Tuple, Dict

from networkx import DiGraph

from src.checkmate.readers.callgraph.CGNode import CGNode
from src.checkmate.util.CGCallSite import CGCallSite
from src.checkmate.util.CGTarget import CGTarget


class AbstractCallGraphReader(ABC):

    def import_graph(self, file: str) -> DiGraph:
        logging.info(f'Reading callgraph from {file}')
        callgraph: Dict[CGCallSite, CGTarget] = {}
        with open(file) as f:
            lines = f.readlines()
        for l in lines[1:]:  # skip header line
            callsite, target = self.process_line(l)
            if callsite not in callgraph:
                callgraph[callsite] = []
            callgraph[callsite].append(target)
        return {str(k): [str(v1) for v1 in v] for k, v in callgraph.items()}

    """
    Creates call graph nodes from input line.
    Expects line to have the following format:
    caller\tcallsite\tcalling_context\ttarget\ttarget_context
    """
    def process_line(self, line: str) -> Tuple[CGCallSite, CGTarget]:
        tokens = line.split('\t')
        callsite = CGCallSite(tokens[0], tokens[1], tokens[2])
        target = CGCallSite(tokens[3], tokens[4])
        return callsite, target