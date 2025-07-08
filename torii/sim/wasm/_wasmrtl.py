# SPDX-License-Identifier: BSD-2-Clause

from ...hdl.ir import Fragment

__all__ = (
	'_WASMFragmentCompiler',
)

class _WASMFragmentCompiler:
	def __init__(self, state) -> None:
		self.state = state

	def __call__(self, fragment: Fragment):
		pass
