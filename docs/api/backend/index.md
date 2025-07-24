# Torii Backends

```{warning}
The Torii API reference is a work in progress and we are actively working on improving it,
however it may be deficient or missing in places.
```

Torii has 3 primary backends, [RTLIL], [Verilog], and [CXXRTL], each takes a Torii {py:class}`Fragment <torii.hdl.ir.Fragment>` or {py:class}`Elaboratable <torii.hdl.ir.Elaboratable>` and produces an RTL netlist in the given output format. There is also the [JSON] backend for generic netlist output.

The primary lingua franca of the Torii backends is [RTLIL], the [Verilog], [CXXRTL], and [JSON] backends first convert the IR into it, and then use [Yosys] to convert the RTLIL netlist into their respective output formats

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

## JSON Backend

```{eval-rst}
.. automodule:: torii.back.json
  :members:

```

## Example

Lets say you have the following Torii design:

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

To convert it to the wanted format, call `convert` from the wanted backend and pass in the instance of the elaboratable.

```{eval-rst}
.. tab:: Verilog

    .. code-block:: python
      :linenos:

      from torii.back.verilog import convert

      verilog = convert(Blinky(), name = 'blinker', ports = [])

    Will result in:

    .. code-block:: verilog
      :linenos:

      (* top =  1  *)
      (* generator = "Torii 0.8.0" *)
      module blinker(rst, clk);
        reg \$auto$verilog_backend.cc:2373:dump_module$1  = 0;
        (* src = "<python-input-0>:9" *)
        wire [20:0] \$1 ;
        (* src = "<python-input-0>:9" *)
        wire [20:0] \$2 ;
        (* src = "torii/back/verilog.py:77" *)
        input clk;
        wire clk;
        (* src = "<python-input-0>:5" *)
        wire led;
        (* src = "torii/back/verilog.py:77" *)
        input rst;
        wire rst;
        (* src = "<python-input-0>:6" *)
        reg [19:0] timer = 20'h00000;
        (* src = "<python-input-0>:6" *)
        reg [19:0] \timer$next ;
        assign \$2  = timer + (* src = "<python-input-0>:9" *) 1'h1;
        always @(posedge clk)
          timer <= \timer$next ;
        always @* begin
          if (\$auto$verilog_backend.cc:2373:dump_module$1 ) begin end
          \timer$next  = \$2 [19:0];
          (* src = "torii/hdl/xfrm.py:556" *)
          if (rst) begin
            \timer$next  = 20'h00000;
          end
        end
        assign \$1  = \$2 ;
        assign led = timer[19];
      endmodule

.. tab:: CXXRTL

    .. code-block:: python
      :linenos:

      from torii.back.cxxrtl import convert

      cxxrtl = convert(Blinky(), name = 'blinker', ports = [])

    Will result in:

    .. code-block:: cpp
      :linenos:

      #include <cxxrtl/cxxrtl.h>

      #if defined(CXXRTL_INCLUDE_CAPI_IMPL) || \
          defined(CXXRTL_INCLUDE_VCD_CAPI_IMPL)
      #include <cxxrtl/capi/cxxrtl_capi.cc>
      #endif

      #if defined(CXXRTL_INCLUDE_VCD_CAPI_IMPL)
      #include <cxxrtl/capi/cxxrtl_capi_vcd.cc>
      #endif

      using namespace cxxrtl_yosys;

      namespace cxxrtl_design {

      // \top: 1
      // \generator: Torii 0.8.0
      struct p_blinker : public module {
              // \src: <python-input-0>:6
              // \init: 0
              wire<20> p_timer;
              // \src: torii/back/cxxrtl.py:68
              /*input*/ value<1> p_rst;
              // \src: torii/back/cxxrtl.py:68
              /*input*/ value<1> p_clk;
              value<1> prev_p_clk;
              bool posedge_p_clk() const {
                      return !prev_p_clk.slice<0>().val() && p_clk.slice<0>().val();
              }
              // \src: <python-input-0>:5
              /*outline*/ value<1> p_led;
              // \src: <python-input-0>:6
              /*outline*/ value<20> p_timer_24_next;
              p_blinker(interior) {}
              p_blinker() {
                      reset();
              };

              void reset() override;

              bool eval(performer *performer = nullptr) override;

              template<class ObserverT>
              bool commit(ObserverT &observer) {
                      bool changed = false;
                      if (p_timer.commit(observer)) changed = true;
                      prev_p_clk = p_clk;
                      return changed;
              }

              bool commit() override {
                      observer observer;
                      return commit<>(observer);
              }

              void debug_eval();
              debug_outline debug_eval_outline { std::bind(&p_blinker::debug_eval, this) };

              void debug_info(debug_items *items, debug_scopes *scopes, std::string path, metadata_map &&cell_attrs = {}) override;
      }; // struct p_blinker

      void p_blinker::reset() {
              p_timer = wire<20>{0u};
      }

      bool p_blinker::eval(performer *performer) {
              bool converged = true;
              bool posedge_p_clk = this->posedge_p_clk();
              // cells $4 $procmux$1 $3
              if (posedge_p_clk) {
                      p_timer.next = (p_rst ? value<20>{0u} : add_uu<21>(p_timer.curr, value<1>{0x1u}).slice<19,0>().val());
              }
              return converged;
      }

      void p_blinker::debug_eval() {
              // cells $procmux$1 $3
              p_timer_24_next = (p_rst ? value<20>{0u} : add_uu<21>(p_timer.curr, value<1>{0x1u}).slice<19,0>().val());
              // connection
              p_led = p_timer.curr.slice<19>().val();
      }

      CXXRTL_EXTREMELY_COLD
      void p_blinker::debug_info(debug_items *items, debug_scopes *scopes, std::string path, metadata_map &&cell_attrs) {
              assert(path.empty() || path[path.size() - 1] == ' ');
              if (scopes) {
                      scopes->add(path.empty() ? path : path.substr(0, path.size() - 1), "blinker", metadata_map({
                              { "top", UINT64_C(1) },
                              { "generator", "Torii 0.8.0" },
                      }), std::move(cell_attrs));
              }
              if (items) {
                      items->add(path, "led", "src\000s<python-input-0>:5\000", debug_eval_outline, p_led);
                      items->add(path, "timer$next", "src\000s<python-input-0>:6\000", debug_eval_outline, p_timer_24_next);
                      items->add(path, "timer", "src\000s<python-input-0>:6\000init\000u\000\000\000\000\000\000\000\000", p_timer, 0, debug_item::DRIVEN_SYNC);
                      items->add(path, "rst", "src\000s/torii/back/cxxrtl.py:68\000", p_rst, 0, debug_item::INPUT|debug_item::UNDRIVEN);
                      items->add(path, "clk", "src\000s/torii/back/cxxrtl.py:68\000", p_clk, 0, debug_item::INPUT|debug_item::UNDRIVEN);
              }
      }

      } // namespace cxxrtl_design

      extern "C"
      cxxrtl_toplevel cxxrtl_design_create() {
              return new _cxxrtl_toplevel { std::unique_ptr<cxxrtl_design::p_blinker>(new cxxrtl_design::p_blinker) };
      }

.. tab:: JSON

    .. code-block:: python
      :linenos:

      from torii.back.json import convert

      json = convert(Blinky(), name = 'blinker', ports = [])

    Will result in:

    .. code-block:: json
      :linenos:

      {
        "creator": "Yosys 0.55",
        "modules": {
          "blinker": {
            "attributes": {
              "top": "00000000000000000000000000000001",
              "generator": "Torii 0.8.0"
            },
            "ports": {
              "rst": {
                "direction": "input",
                "bits": [ 2 ]
              },
              "clk": {
                "direction": "input",
                "bits": [ 3 ]
              }
            },
            "cells": {
              "$3": {
                "hide_name": 1,
                "type": "$add",
                "parameters": {
                  "A_SIGNED": "00000000000000000000000000000000",
                  "A_WIDTH": "00000000000000000000000000010100",
                  "B_SIGNED": "00000000000000000000000000000000",
                  "B_WIDTH": "00000000000000000000000000000001",
                  "Y_WIDTH": "00000000000000000000000000010101"
                },
                "attributes": {
                  "src": "<python-input-0>:9"
                },
                "port_directions": {
                  "A": "input",
                  "B": "input",
                  "Y": "output"
                },
                "connections": {
                  "A": [ 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23 ],
                  "B": [ "1" ],
                  "Y": [ 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44 ]
                }
              },
              "$4": {
                "hide_name": 1,
                "type": "$dff",
                "parameters": {
                  "CLK_POLARITY": "00000000000000000000000000000001",
                  "WIDTH": "00000000000000000000000000010100"
                },
                "attributes": {
                },
                "port_directions": {
                  "CLK": "input",
                  "D": "input",
                  "Q": "output"
                },
                "connections": {
                  "CLK": [ 3 ],
                  "D": [ 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64 ],
                  "Q": [ 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23 ]
                }
              },
              "$procmux$1": {
                "hide_name": 1,
                "type": "$mux",
                "parameters": {
                  "WIDTH": "00000000000000000000000000010100"
                },
                "attributes": {
                  "src": "torii/hdl/xfrm.py:556"
                },
                "port_directions": {
                  "A": "input",
                  "B": "input",
                  "S": "input",
                  "Y": "output"
                },
                "connections": {
                  "A": [ 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43 ],
                  "B": [ "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0" ],
                  "S": [ 2 ],
                  "Y": [ 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64 ]
                }
              }
            },
            "netnames": {
              "$1": {
                "hide_name": 1,
                "bits": [ 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44 ],
                "attributes": {
                  "src": "<python-input-0>:9"
                }
              },
              "$2": {
                "hide_name": 1,
                "bits": [ 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44 ],
                "attributes": {
                  "src": "<python-input-0>:9"
                }
              },
              "$procmux$1_Y": {
                "hide_name": 1,
                "bits": [ 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64 ],
                "attributes": {
                }
              },
              "$procmux$2_CMP": {
                "hide_name": 1,
                "bits": [ 2 ],
                "attributes": {
                }
              },
              "clk": {
                "hide_name": 0,
                "bits": [ 3 ],
                "attributes": {
                  "src": "torii/back/json.py:55"
                }
              },
              "led": {
                "hide_name": 0,
                "bits": [ 23 ],
                "attributes": {
                  "src": "<python-input-0>:5"
                }
              },
              "rst": {
                "hide_name": 0,
                "bits": [ 2 ],
                "attributes": {
                  "src": "torii/back/json.py:55"
                }
              },
              "timer": {
                "hide_name": 0,
                "bits": [ 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23 ],
                "attributes": {
                  "init": "00000000000000000000",
                  "src": "<python-input-0>:6"
                }
              },
              "timer$next": {
                "hide_name": 0,
                "bits": [ 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64 ],
                "attributes": {
                  "src": "<python-input-0>:6"
                }
              }
            }
          }
        }
      }
```


[RTLIL]: https://yosyshq.readthedocs.io/projects/yosys/en/latest/appendix/rtlil_text.html
[Verilog]: https://yosyshq.readthedocs.io/projects/yosys/en/latest/cmd/write_verilog.html
[CXXRTL]: https://yosyshq.readthedocs.io/projects/yosys/en/latest/cmd/write_cxxrtl.html
[JSON]: https://yosyshq.readthedocs.io/projects/yosys/en/latest/cmd/write_json.html
[Yosys]: https://github.com/YosysHQ/yosys
