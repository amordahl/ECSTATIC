#  CheckMate: A Configuration Tester for Static Analysis
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
from src.checkmate.readers.AbstractReader import AbstractReader
from src.checkmate.violation_checkers.AbstractViolationChecker import AbstractViolationChecker
from src.checkmate.violation_checkers.CallgraphViolationChecker import CallgraphViolationChecker
from src.checkmate.violation_checkers.FlowDroidFlowViolationChecker import FlowDroidFlowViolationChecker


def get_violation_checker_for_task(task: str, tool: str, jobs: int,
                                   groundtruths: str, reader: AbstractReader) -> AbstractViolationChecker:
    if task.lower() == "cg":
        return CallgraphViolationChecker(jobs, reader, groundtruths)
    elif task.lower() == "taint" and tool.lower() == "flowdroid":
        return FlowDroidFlowViolationChecker(jobs, reader, groundtruths)
    else:
        raise ValueError(f"No violation checker exists for task {task} on tool {tool}.")