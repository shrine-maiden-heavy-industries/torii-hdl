#!/usr/bin/env python3
# SPDX-License-Identifier: BSD-2-Clause
import sys
from pathlib import Path

try:
	from torii.test._runner import ToriiTestRunner
except ImportError:
	torii_path = Path(__file__).resolve()

	if (torii_path.parent.parent / 'torii').is_dir():
		sys.path.insert(0, str(torii_path.parent))

	from torii.test._runner import ToriiTestRunner

from unittest import main

main(module=None, testRunner = ToriiTestRunner)
