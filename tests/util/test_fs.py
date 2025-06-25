# SPDX-License-Identifier: BSD-2-Clause

from pathlib       import Path
from tempfile      import TemporaryDirectory

from torii.test    import ToriiTestCase
from torii.util.fs import working_dir

class FsUtilsTestCase(ToriiTestCase):
	def test_working_dir(self):
		# Make a temp dir and get the old CWD
		temp = TemporaryDirectory()
		cwd = Path.cwd()

		# Some quick sanity checks
		self.assertNotEqual(Path(temp.name), cwd)

		# Switch into the temp dir
		with working_dir(temp.name) as new_cwd:
			# Capture the CWD
			prev_cwd = Path.cwd()

			# Ensure our old CWD and new CWD are different
			self.assertNotEqual(cwd, new_cwd)

			# Ensure the switch took place
			self.assertEqual(new_cwd, prev_cwd)
			# ... and that it's in the right dir
			self.assertEqual(Path(temp.name), new_cwd)

		# Check to ensure we're back in the right spot
		self.assertEqual(cwd, Path.cwd())
		# ... and that it's different from the old
		self.assertNotEqual(cwd, prev_cwd)

		# Clean up the temp dir
		temp.cleanup()
