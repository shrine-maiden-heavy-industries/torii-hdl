# Torii Backends

```{warning}
The Torii API reference is a work in progress and we are actively working on improving it,
however it may be deficient or missing in places.
```

Torii has 3 primary backends, [RTLIL], [Verilog], and [CXXRTL], each takes a Torii {py:class}`Fragment <torii.hdl.ir.Fragment>` or {py:class}`Elaboratable <torii.hdl.ir.Elaboratable>` and produces an RTL netlist in the given output format.

The primary lingua franca of the Torii backends is [RTLIL], the [Verilog] and [CXXRTL] backends first convert the IR into it, and then use [Yosys] to convert the RTLIL netlist into their respective output formats

## RTLIL Backend

```{eval-rst}
.. automodule:: torii.back.rtlil
  :members:

```

## Verilog Backend

```{eval-rst}
.. automodule:: torii.back.verilog
  :members:

```

## CXXRTL Backend

```{eval-rst}
.. automodule:: torii.back.cxxrtl
  :members:

```

## Example

Lets say you have the following Torii design you would like to convert to Verilog:

```py
class Blinky(Elaboratable):
    def elaborate(self, platform) -> Module:
        led   = Signal()
        timer = Signal(20)

        m = Module()
        m.d.sync += timer.eq(timer + 1)
        m.d.comb += led.eq(timer[-1])
        return m
```

You can do so by importing the {py:meth}`torii.back.verilog.convert` method and then passing an instance of the elaboratable to it, like so:

```py
from torii.back.verilog import convert

verilog = convert(Blinky(), name = 'blinker', ports = [])
```

That will result in the following Verilog code in `verilog`:

```verilog
(* top =  1  *)
(* generator = "Torii" *)
module blinker(clk, rst, led);
  reg \$auto$verilog_backend.cc:2355:dump_module$1  = 0;
  (* src = "<python-input-8>:7" *)
  wire [20:0] \$1 ;
  (* src = "<python-input-8>:7" *)
  wire [20:0] \$2 ;
  (* src = "torii/hdl/ir.py:541" *)
  input clk;
  wire clk;
  (* src = "<python-input-17>:1" *)
  input led;
  wire led;
  (* src = "<python-input-8>:3" *)
  wire \led$4 ;
  (* src = "torii/hdl/ir.py:541" *)
  input rst;
  wire rst;
  (* src = "<python-input-8>:4" *)
  reg [19:0] timer = 20'h00000;
  (* src = "<python-input-8>:4" *)
  reg [19:0] \timer$next ;
  assign \$2  = timer + (* src = "<python-input-8>:7" *) 1'h1;
  always @(posedge clk)
    timer <= \timer$next ;
  always @* begin
    if (\$auto$verilog_backend.cc:2355:dump_module$1 ) begin end
    \timer$next  = \$2 [19:0];
    (* src = "torii/hdl/xfrm.py:576" *)
    if (rst) begin
      \timer$next  = 20'h00000;
    end
  end
  assign \$1  = \$2 ;
  assign \led$4  = timer[19];
endmodule
```

[RTLIL]: https://yosyshq.readthedocs.io/projects/yosys/en/latest/appendix/rtlil_text.html
[Verilog]: https://yosyshq.readthedocs.io/projects/yosys/en/latest/cmd/write_verilog.html
[CXXRTL]: https://yosyshq.readthedocs.io/projects/yosys/en/latest/cmd/write_cxxrtl.html
[Yosys]: https://github.com/YosysHQ/yosys
