# SPDX-License-Identifier: BSD-2-Clause

from typing import TYPE_CHECKING

__all__ = (
	'SimulatorIntegrationTestMixinBase',
	'SimulatorRegressionTestMixinBase',
	'SimulatorUnitTestMixinBase',
)

# NOTE(aki):
# This is just applying typing stubs to ensure the type checker is happy, doesn't effect runtime
# and a chunk of this was taken from the typeshed stubs for `unittest.case.TestCase`.
if TYPE_CHECKING:
	from collections.abc import Callable
	from contextlib      import contextmanager
	from re              import Pattern
	from typing          import Any, Iterator, ParamSpec, TypeVar, overload
	from unittest.case   import _AssertRaisesContext, _AssertWarnsContext

	from torii.sim       import Simulator

	_E = TypeVar('_E', bound = BaseException)
	_P = ParamSpec("_P")

	class SimulatorIntegrationTestMixinBase:
		def fail(self) -> None:
			...

		@contextmanager
		def assertSimulation(self, module, deadline = None) -> Iterator[Simulator]:
			...

		def assertEqual(self, first: Any, second: Any, msg: Any = None) -> None:
			...

		def assertTrue(self, expr: Any, msg: Any = None) -> None:
			...

		@overload
		def assertRaises( # type: ignore
			self, expected_exception: type[BaseException] | tuple[type[BaseException], ...],
			callable: Callable[..., object], *args: Any, **kwargs: Any,
		) -> None:
			...

		@overload
		def assertRaises(
			self, expected_exception: type[_E] | tuple[type[_E], ...], *, msg: Any = ...
		) -> _AssertRaisesContext[_E]:
			...

		@overload
		def assertRaisesRegex( # type: ignore
			self, expected_exception: type[BaseException] | tuple[type[BaseException], ...],
			expected_regex: str | Pattern[str], callable: Callable[..., object], *args: Any, **kwargs: Any,
		) -> None:
			...

		@overload
		def assertRaisesRegex(
			self, expected_exception: type[_E] | tuple[type[_E], ...], expected_regex: str | Pattern[str], *,
			msg: Any = ...
		) -> _AssertRaisesContext[_E]:
			...

	class SimulatorRegressionTestMixinBase:
		def get_simulator(self, dut) -> Simulator:
			...

		def assertEqual(self, first: Any, second: Any, msg: Any = None) -> None:
			...

		@overload
		def assertRaisesRegex( # type: ignore
			self, expected_exception: type[BaseException] | tuple[type[BaseException], ...],
			expected_regex: str | Pattern[str], callable: Callable[..., object], *args: Any, **kwargs: Any,
		) -> None:
			...

		@overload
		def assertRaisesRegex(
			self, expected_exception: type[_E] | tuple[type[_E], ...], expected_regex: str | Pattern[str], *,
			msg: Any = ...
		) -> _AssertRaisesContext[_E]:
			...

		@overload
		def assertWarnsRegex( # type: ignore
			self, expected_warning: type[Warning] | tuple[type[Warning], ...],
			expected_regex: str | Pattern[str], callable: Callable[_P, object], *args: _P.args, **kwargs: _P.kwargs,
		) -> None:
			...

		@overload
		def assertWarnsRegex(
			self, expected_warning: type[Warning] | tuple[type[Warning], ...], expected_regex: str | Pattern[str], *,
			msg: Any = ...
		) -> _AssertWarnsContext:
			...

	class SimulatorUnitTestMixinBase:
		def assertStatement(self, stmt, inputs, output, reset = 0) -> None:
			...
else:
	SimulatorIntegrationTestMixinBase = object
	SimulatorRegressionTestMixinBase = object
	SimulatorUnitTestMixinBase = object
