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

import logging
from typing import Tuple, Any

from src.checkmate.readers.callgraph.AbstractCallGraphReader import AbstractCallGraphReader
from src.checkmate.util.CGCallSite import CGCallSite
from src.checkmate.util.CGTarget import CGTarget

logger = logging.getLogger(__name__)


class DOOPCallGraphReader(AbstractCallGraphReader):
    def process_line(self, line: str) -> Tuple[CGCallSite, CGTarget]:
        tokens = line.split("\t")
        if len(tokens) == 5:
            return super().process_line(line)
        else:
            return CGCallSite(tokens[0].split('/')[0],
                              '/'.join(tokens[0].split('/')[1:]),
                              tokens[1]), CGTarget(tokens[2], tokens[3])
