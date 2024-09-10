#!/usr/bin/env python
# SPDX-License-Identifier: BSD-2-Clause
import sys
from pathlib import Path

try:
	from torii.cli import main
except ImportError:
	torii_path = Path(sys.argv[0]).resolve()

	if (torii_path.parent / 'torii').is_dir():
		sys.path.insert(0, str(torii_path.parent))

	from torii.cli import main

sys.exit(main())
