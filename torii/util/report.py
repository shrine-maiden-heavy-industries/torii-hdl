# SPDX-License-Identifier: BSD-2-Clause

'''
This module provides the machinery to automatically collect the needed information to fill out
a Torii issue/feature request template.

'''

import platform
from pathlib      import Path
from subprocess   import PIPE, Popen, check_call
from typing       import Final
from urllib.parse import quote
from tempfile     import NamedTemporaryFile
from os           import environ

from ..           import __version__

_ISSUE_URL: Final[str] = 'https://github.com/shrine-maiden-heavy-industries/torii-hdl/issues/new'

class Report:
	torii_version: str
	python_impl: str
	python_version: str
	platform_system: str
	platform_version: str

	def __init__(self) -> None:
		self._collect_info()

	# XXX(aki): This needs testing
	def _disambiguate_sunos(self, platform_info: platform.uname_result) -> str:
		try:
			# Split on `.` and pull out the first two splits
			version = platform_info.release.split('.')[:2]
			version_tuple = (int(version[0]), int(version[1]))
		except Exception:
			return 'Other'

		if version_tuple <= (5, 11):
			return 'Solaris'

		sunos_uname = Popen(['/usr/bin/uname', '-o'], shell = True, stdout = PIPE)
		stdout, _ = sunos_uname.communicate()
		retcode = sunos_uname.returncode

		if retcode != 0:
			return 'Other'

		match stdout.decode('utf-8').lower().strip():
			case 'illumos':
				return 'illumos'
			case 'solaris':
				return 'Solaris'
			case _:
				return 'Other'

	def _get_system(self, platform_info: platform.uname_result) -> str:
		match platform_info.system.lower():
			case 'linux':
				return 'Linux'
			case 'freebsd' | 'openbsd' | 'netbsd' | 'dragonfly':
				return 'BSD'
			case 'sunos':
				return self._disambiguate_sunos(platform_info)
			case 'darwin':
				return 'macOS'
			case 'windows':
				return 'Windows'
			case _:
				return 'Other'

	def _get_linux_release(self) -> str:
		lsb_release = Path('/etc/lsb-release')

		if lsb_release.exists():
			with lsb_release.open('r') as f:
				lsb_info = { e[0]: e[1] for e in (line.split('=') for line in f.readlines() ) }
			return lsb_info.get("DISTRIB_DESCRIPTION", platform.platform())
		else:
			return platform.platform()

	def _collect_info(self) -> None:
		self.torii_version  = __version__
		self.python_impl    = platform.python_implementation()
		self.python_version = '.'.join(platform.python_version_tuple()[:2])

		platform_info = platform.uname()

		self.platform_system = self._get_system(platform_info)

		match self.platform_system:
			case 'Linux':
				self.platform_version = self._get_linux_release().strip()
			case 'Other':
				self.platform_version = f'{platform_info.system.strip()} {platform_info.release.strip()}'
			case _:
				self.platform_version = platform_info.release.strip()

	def _get_editor(self) -> str:
		# TODO(aki): YOLO, I guess
		return environ.get('EDITOR', 'nvim')

	def _get_body(self, type: str) -> str | None:
		editor = self._get_editor()

		temp = NamedTemporaryFile('w+', prefix = 'torii_report_')

		temp.writelines((
			'\n',
			f'# You are filling out a {type} for Torii\n',
			'#\n',
			'# Please enter report details, Lines starting with `#` will\n',
			'# be ignored.\n',
			'#\n',
			'# Relevant Details:\n',
			f'#   * Torii Version:         {self.torii_version}\n',
			f'#   * Python Implementation: {self.python_impl}\n',
			f'#   * Python Version:        {self.python_version}\n',
			f'#   * System Platform:       {self.platform_system}\n',
			f'#   * System Version:        {self.platform_version}\n',
			'#\n',
			'# To fill out a report manually visit:\n'
			f'# {_ISSUE_URL}'
		))

		temp.flush()

		try:
			check_call([editor, temp.name])
			temp.seek(0)

			# Collect report body
			lines = list(filter(lambda line: not line.startswith('#'), temp.readlines()))

			# Check to see if we have any valid user input
			if len(lines) == 0:
				print('a')
				return None
			elif len(lines) == 1:
				if lines[0].strip() == '':
					return None
			# If we do, smush it together
			body = '\n'.join(lines).strip()
			temp.close()
			return quote(body)
		except ChildProcessError:
			# If the editor exited or didn't run, just abort
			temp.close()
			return None

	def _query_params(self, type: str) -> str:
		return '&'.join((
			f'torii-version={self.torii_version}',
			f'python-version={self.python_impl}%20{self.python_version}',
			f'platform={self.platform_system}',
			f'platform-version={quote(self.platform_version)}',
			f'bug-description={self._get_body(type)}'
		))

	@property
	def bug_report_url(self) -> str:
		return f'{_ISSUE_URL}?template=1-bug-report.yml&{self._query_params(type = "Bug Report")}'

	@property
	def docs_issue_url(self) -> str:
		return f'{_ISSUE_URL}?template=2-documentation.yml&{self._query_params(type = "Documentation Issue")}'

	@property
	def feature_request_url(self) -> str:
		return f'{_ISSUE_URL}?template=3-feature-suggestion.yml&{self._query_params(type = "Feature Suggestion")}'

	@property
	def other_issue_url(self) -> str:
		return f'{_ISSUE_URL}?template=99-other.yml&{self._query_params(type = "Other Report")}'
