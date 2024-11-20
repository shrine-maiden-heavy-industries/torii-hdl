# SPDX-License-Identifier: BSD-2-Clause

import os
import re
import shutil
import subprocess
import textwrap
import traceback
from pathlib          import Path

from torii.hdl.ast    import *
from torii.hdl.ir     import *
from torii.back       import rtlil
from torii.tools      import require_tool, ToolNotFound
from torii.test       import ToriiTestCase


__all__ = (
	'ToriiTestSuiteCase',
)


class ToriiTestSuiteCase(ToriiTestCase):
	def assertRepr(self, obj, repr_str):
		if isinstance(obj, list):
			obj = Statement.cast(obj)

		def prepare_repr(repr_str):
			repr_str = re.sub(r'\s+', ' ',  repr_str)
			repr_str = re.sub(r'\( (?=\()', '(', repr_str)
			repr_str = re.sub(r'\) (?=\))', ')', repr_str)
			return repr_str.strip()
		self.assertEqual(prepare_repr(repr(obj)), prepare_repr(repr_str))

	# TODO: Once the Torii formal bits are better defined remove this and add formal to ToriiTestCase
	def assertFormal(self, spec, mode = 'bmc', depth = 1):
		stack      = traceback.extract_stack()
		file_dir   = Path(__file__).resolve().parent
		formal_dir = Path.cwd() / 'torii-formal'

		if not formal_dir.exists():
			formal_dir.mkdir(parents = True, exist_ok = True)

		for frame in reversed(stack):
			if str(file_dir) not in frame.filename:
				break
			caller = frame

		fname = Path(caller.filename).resolve().stem.replace('test_', 'spec_')
		spec_name = f'{fname}_{caller.name.replace("test_", "")}'
		spec_dir = formal_dir / spec_name

		# The sby -f switch seems not fully functional when sby is reading from stdin.
		if spec_dir.exists():
			shutil.rmtree(spec_dir)

		if mode == 'hybrid':
			# A mix of BMC and k-induction, as per personal communication with Claire Wolf.
			script = 'setattr -unset init w:* a:torii.sample_reg %d'
			mode   = 'bmc'
		else:
			script = ''

		config = textwrap.dedent(f'''\
		[options]
		mode {mode}
		depth {depth}
		wait on
		multiclock on

		[engines]
		smtbmc

		[script]
		read_rtlil top.il
		prep
		{script}

		[file top.il]
		{rtlil.convert_fragment(Fragment.get(spec, platform = 'formal').prepare())[0]}
		''')

		try:
			sby = require_tool('sby')
		except ToolNotFound:
			self.skipTest('SBY not installed')

		with subprocess.Popen([
				sby, '-f', '-d', spec_name
			],
			cwd                = formal_dir,
			env                = {
				**os.environ,
				'PYTHONWARNINGS': 'ignore'
			},
			universal_newlines = True,
			stdin              = subprocess.PIPE,
			stdout             = subprocess.PIPE
		) as proc:
			stdout, stderr = proc.communicate(config)
			if proc.returncode != 0:
				self.fail('Formal verification failed:\n' + stdout)
