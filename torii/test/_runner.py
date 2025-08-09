# SPDX-License-Identifier: BSD-2-Clause

import sys
from typing           import TextIO, TypeAlias
from types            import TracebackType
from unittest         import TestCase
from unittest.result  import TestResult
from unittest.suite   import TestSuite
from unittest.signals import registerResult
from dataclasses      import dataclass

from rich.console     import Console, ConsoleOptions, RenderResult
from rich.progress    import Progress
from rich.live        import Live


'''
A custom test :py:mod:`unittest` test runner for Torii
'''

# A global test runner console so we don't keep re-initializing it,
_TEST_RUNNER_CONSOLE: Console | None = None

_ERR: TypeAlias = tuple[type[BaseException], BaseException, TracebackType] | tuple[None, None, None]

@dataclass
class _TestCaseTest:
	def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
		return ''

class ToriiTestResult(TestResult):
	'''

	'''

	def __init__(
		self, stream: TextIO | None = None, descriptions: bool | None = None, verbosity: int | None = None, *,
		durations = None, failfast: bool = False, buffer: bool = False, tb_locals: bool = False, count: int = 0
	) -> None:
		# XXX(aki): `stream`, `descriptions`, and `verbosity` are not used in the superclass it seems
		super().__init__(stream, descriptions, verbosity)

		self.failfast = failfast
		self.buffer = buffer
		self.tb_locals = tb_locals

		# Useful internal alias, should already be initialized
		self._console = _TEST_RUNNER_CONSOLE

		self._tests = dict[TestCase, _TestCaseTest]()
		self._progress = Progress(console = self._console)
		self._test_task = self._progress.add_task('Testing', total = count)

	def addDuration(self, test: TestCase, elapsed: float) -> None:
		# print(f'addDuration({test}, {elapsed})')
		return super().addDuration(test, elapsed)

	def addError(self, test: TestCase, err: _ERR) -> None:
		# print(f'addError({test}, {err})')
		self._progress.advance(self._test_task)
		return super().addError(test, err)

	def addExpectedFailure(self, test: TestCase, err: _ERR) -> None:
		# print(f'addExpectedFailure({test}, {err})')
		self._progress.advance(self._test_task)
		return super().addExpectedFailure(test, err)

	def addFailure(self, test: TestCase, err: _ERR) -> None:
		# print(f'addFailure({test}, {err})')
		self._progress.log(f'[red]Test Error: {test}[/]')
		self._progress.log(err)
		self._progress.advance(self._test_task)
		return super().addFailure(test, err)

	def addSubTest(self, test: TestCase, subtest: TestCase, err: _ERR | None) -> None:
		# print(f'addSubTest({test}, {subtest}, {err})')
		return super().addSubTest(test, subtest, err)

	def addSuccess(self, test: TestCase) -> None:
		# print(f'addSuccess({test})')
		self._progress.advance(self._test_task)
		return super().addSuccess(test)

	def addUnexpectedSuccess(self, test: TestCase) -> None:
		# print(f'addUnexpectedSuccess({test})')
		self._progress.advance(self._test_task)
		return super().addUnexpectedSuccess(test)

	def printErrors(self) -> None:
		# print('printErrors()')
		return super().printErrors()

	def startTest(self, test: TestCase) -> None:
		# print(f'startTest({test})')
		self._progress.log(f'Testing: {test._testMethodName} {test.countTestCases()}')
		return super().startTest(test)

	def startTestRun(self) -> None:
		# print('startTestRun()')
		self._progress.start()
		return super().startTestRun()

	def stop(self) -> None:
		# print('stop()')
		return super().stop()

	def stopTest(self, test: TestCase) -> None:
		# print(f'stopTest({test})')
		return super().stopTest(test)

	def stopTestRun(self) -> None:
		# print('stopTestRun()')
		self._progress.stop()
		return super().stopTestRun()

	def wasSuccessful(self) -> bool:
		# print('wasSuccessful()')
		return super().wasSuccessful()

class ToriiTestRunner:
	'''

	'''

	resultclass = ToriiTestResult

	def __init__(
		self, stream: TextIO | None = None, descriptions: bool = True, verbosity: int = 1, failfast: bool = False,
		buffer: bool = False, resultclass: type | None = None, warnings: list[str] | str | None = None, *,
		tb_locals: bool = False, durations = None
	) -> None:
		self.stream = sys.stderr if stream is None else stream
		self.descriptions = descriptions
		self.verbosity = verbosity
		self.failfast = failfast
		self.buffer = buffer
		self.tb_locals = tb_locals
		self.durations = durations
		self.warnings = warnings

		global _TEST_RUNNER_CONSOLE
		# if we've not initialized the global console, do so
		if _TEST_RUNNER_CONSOLE is None:
			_TEST_RUNNER_CONSOLE = Console(file = self.stream)

		# Useful internal alias
		self._console = _TEST_RUNNER_CONSOLE

	def run(self, tests: TestSuite | TestCase) -> ToriiTestResult:

		# Kinda hacky
		test_count = len(list(iter(tests)))

		res = ToriiTestResult(
			self.stream, self.descriptions, self.verbosity, durations = self.durations,
			failfast = self.failfast, buffer = self.buffer, tb_locals = self.tb_locals,
			count = test_count
		)
		registerResult(res)

		res.startTestRun()

		try:
			tests(res)
		finally:
			res.stopTestRun()

		res.printErrors()

		return res
