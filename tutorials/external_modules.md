# Including External non-Torii Modules

Occasionally it is desired to include modules that are written in something like [Verilog], [SystemVerilog], or [VHDL] in a Torii based design. This is most commonly needed for things like external [IP] from other sources such as FPGA primitives or designed generated from another HDL such as [Clash], [SpinalHDL], or [Chisel], as they are not directly interoperable with Torii.


Luckily, this is fairly easy to do with the Torii {py:class}`torii.hdl.ir.Instance`, it allows you to construct an instance of an arbitrary module, defining all of the inputs, outputs, and properties.

## Torii `Instance`

A Torii instance takes the name of the module or primitive you wish to instantiate, and lets you define the parameters, ports, and attributes, most of which can be directly hooked up with other Torii types such as {py:class}`torii.hdl.ast.Signal`.

An example of an `Instance` that instantiates a module called `MyInverter` (who's implementation is not important) which has 1 input port named `src` and 1 output port named `dst` would be as follows.

```py

Instance(
	'MyInverter',
	i_src = input_signal,
	o_dst = output_signal
)

```

The prefix on the front of the port name is important, as it tells Torii what that parameter of the instance is, and the port name itself must match the port name of the module or cell you're instantiating. The accepted prefixes and corresponding types are listed in the table below.

| Prefix | Corresponding Type         |
|--------|----------------------------|
| `a_`   | Attribute                  |
| `p_`   | Parameter                  |
| `i_`   | Input Port/Signal          |
| `o_`   | Output Port/Signal         |
| `io_`  | Bi-directional Port/Signal |


## Including External Sources

When you are using a generated or a raw [Verilog] module, then you need to tell torii to include it so it can properly synthesize, you do this with the {py:meth}`torii.build.plat.Platform.add_file` method, it takes the name and contents of a file to add to the sources collection which is then used in the synthesis step.

An example Torii elaboratable for a [Verilog]  module would look like this:


```py

from pathlib import Path

from torii import Elaboratable, Module, Signal, Instance

class MyInverter(Elaboratable):
	def __init__(self) -> None:
		self.input = Signal()
		self.output = Signal()
		self.extern_module = Path('./my_inverter.v').resolve()

	def elaborate(self, platform) -> Module:
		# Add the file to the platform
		if platform is not None:
			with self.extern_module.open('r') as f:
				platform.add_file(self.extern_module.name, f)

		m = Module()

		# Add the
		m.submodules += Instance(
			'MyInverter',
			i_src = self.input,
			i_dst = self.output
		)

		return m

```

It's not necessary to pass the file in within the elaborate of the module itself, however keeping the wrapper elaboratable coupled to the dependant HDL source file is recommended.





[Verilog]: https://ieeexplore.ieee.org/document/1620780
[SystemVerilog]: https://ieeexplore.ieee.org/document/8299595
[VHDL]: https://ieeexplore.ieee.org/document/8938196
[Clash]: https://clash-lang.org/
[Chisel]: https://www.chisel-lang.org/
[SpinalHDL]: https://github.com/SpinalHDL/SpinalHDL
[Torii-Boards]: https://github.com/shrine-maiden-heavy-industries/torii-boards
