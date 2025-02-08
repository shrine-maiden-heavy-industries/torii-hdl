# Language Guide


```{warning}
   This guide is a work in progress and is seriously incomplete!
```

This guide introduces the Torii language in depth. It assumes familiarity with synchronous digital logic and the Python programming language, but does not require prior experience with any hardware description language. See the [Tutorials](../tutorials/index.md) section for a step-by-step introduction to the language.

<!-- TODO: link to a good synchronous logic tutorial and a Python tutorial? -->


## The prelude

Because Torii is a regular Python library, it needs to be imported before use. The root `torii` module, called *the prelude*, is carefully curated to export a small amount of the most essential names, useful in nearly every design. In source files dedicated to Torii code, it is a good practice to use a {ref}`glob import <python:tut-pkg-import-star>` for readability:

```py
   from torii import *
```

However, if a source file uses Torii together with other libraries, or if glob imports are frowned upon, it is conventional to use a short alias instead:

```py
   import torii as tr
```

All of the examples below assume that a glob import is used.

```{eval-rst}
.. testsetup::

   from torii import *

```

## Shapes

A `Shape` is an object with two attributes, `.width` and `.signed`. It can be constructed directly:

```{eval-rst}
.. doctest::

   >>> Shape(width=5, signed=False)
   unsigned(5)
   >>> Shape(width=12, signed=True)
   signed(12)
```

However, in most cases, the shape is always constructed with the same signedness, and the aliases `signed` and `unsigned` are more convenient:

```{eval-rst}
.. doctest::

   >>> unsigned(5) == Shape(width=5, signed=False)
   True
   >>> signed(12) == Shape(width=12, signed=True)
   True
```

## Shapes of values

All values have a `.shape()` method that computes their shape. The width of a value `v`, `v.shape().width`, can also be retrieved with `len(v)`.

```{eval-rst}
.. doctest::

   >>> Const(5).shape()
   unsigned(3)
   >>> len(Const(5))
   3
```

## Values

The basic building block of the Torii language is a *value*, which is a term for a binary number that is computed or stored anywhere in the design. Each value has a *width*---the amount of bits used to represent the value---and a *signedness*---the interpretation of the value by arithmetic operations---collectively called its *shape*. Signed values always use [two's complement] representation.


## Constants


The simplest Torii value is a *constant*, representing a fixed number, and introduced using `Const(...)`:

```{eval-rst}
.. doctest::

   >>> ten = Const(10)
   >>> minus_two = Const(-2)

```

The code above does not specify any shape for the constants. If the shape is omitted, Torii uses unsigned shape for positive numbers and signed shape for negative numbers, with the width inferred from the smallest amount of bits necessary to represent the number. As a special case, in order to get the same inferred shape for `True` and `False`, `0` is considered to be 1-bit unsigned.

```{eval-rst}
.. doctest::

   >>> ten.shape()
   unsigned(4)
   >>> minus_two.shape()
   signed(2)
   >>> Const(0).shape()
   unsigned(1)

```

The shape of the constant can be specified explicitly, in which case the number's binary representation will be truncated or extended to fit the shape. Although rarely useful, 0-bit constants are permitted.

```{eval-rst}
.. doctest::

   >>> Const(360, unsigned(8)).value
   104
   >>> Const(129, signed(8)).value
   -127
   >>> Const(1, unsigned(0)).value
   0

```

## Shape casting

Shapes can be *cast* from other objects, which are called *shape-castable*. Casting is a convenient way to specify a shape indirectly, for example, by a range of numbers representable by values with that shape.

Casting to a shape can be done explicitly with `Shape.cast`, but is usually implicit, since shape-castable objects are accepted anywhere shapes are.


### Shapes from integers

Casting a shape from an integer `i` is a shorthand for constructing a shape with `unsigned(i)`:

```{eval-rst}
.. doctest::

   >>> Shape.cast(5)
   unsigned(5)
   >>> Const(0, 3).shape()
   unsigned(3)

```

### Shapes from ranges

Casting a shape from a {class}`range` `r` produces a shape that:

 * has a width large enough to represent both `min(r)` and `max(r)`, but not larger, and
 * is signed if `r` contains any negative values, unsigned otherwise.

Specifying a shape with a range is convenient for counters, indexes, and all other values whose width is derived from a set of numbers they must be able to fit:

```{eval-rst}
.. doctest::

   >>> Const(0, range(100)).shape()
   unsigned(7)
   >>> items = [1, 2, 3]
   >>> Const(1, range(len(items))).shape()
   unsigned(2)

```
```{eval-rst}
.. note::

   Python ranges are *exclusive* or *half-open*, meaning they do not contain their ``.stop`` element. Because of this, values with shapes cast from a ``range(stop)`` where ``stop`` is a power of 2 are not wide enough to represent ``stop`` itself:

   .. doctest::

      >>> fencepost = Const(256, range(256))
      >>> fencepost.shape()
      unsigned(8)
      >>> fencepost.value
      0

   This is detected in :py:class:`Const` and :py:class:`Signal` when invoked with a suspected off-by-one error, which then emits a diagnostic message.

```

### Shapes from enumerations

Casting a shape from an {class}`enum.Enum` subclass `E`:

 * fails if any of the enumeration members have non-integer values,
 * has a width large enough to represent both `min(m.value for m in E)` and `max(m.value for m in E)`, and
 * is signed if either `min(m.value for m in E)` or `max(m.value for m in E)` are negative, unsigned otherwise.

Specifying a shape with an enumeration is convenient for finite state machines, multiplexers, complex control signals, and all other values whose width is derived from a few distinct choices they must be able to fit:

```{eval-rst}
.. testsetup::

   import enum

.. testcode::

   class Direction(enum.Enum):
       TOP    = 0
       LEFT   = 1
       BOTTOM = 2
       RIGHT  = 3

.. doctest::

   >>> Shape.cast(Direction)
   unsigned(2)

```

```{note}
The enumeration does not have to subclass {class}`enum.IntEnum`; it only needs to have integers as values of every member. Using enumerations based on {class}`enum.Enum` rather than {class}`enum.IntEnum` prevents unwanted implicit conversion of enum members to integers.
```

## Value casting

Like shapes, values may be *cast* from other objects, which are called *value-castable*. Casting to values allows objects that are not provided by Torii, such as integers or enumeration members, to be used in Torii expressions directly.

<!-- TODO: link to ValueCastable -->

Casting to a value can be done explicitly with `Value.cast`, but is usually implicit, since value-castable objects are accepted anywhere values are.


### Values from integers


Casting a value from an integer `i` is equivalent to `Const(i)`:

```{eval-rst}
.. doctest::

   >>> Value.cast(5)
   (const 3'd5)

```

```{note}
If a value subclasses :class:`enum.IntEnum` or its class otherwise inherits from both :class:`int` and :class:`Enum`, it is treated as an enumeration.
```

### Values from enumeration members

Casting a value from an enumeration member `m` is equivalent to `Const(m.value, type(m))`:

```{eval-rst}
.. doctest::

   >>> Value.cast(Direction.LEFT)
   (const 2'd1)

```

```{note}
If a value subclasses :class:`enum.IntEnum` or its class otherwise inherits from both :class:`int` and :class:`Enum`, it is treated as an enumeration.
```

# Constant casting

A subset of [values](#values) are *constant-castable*. If a value is constant-castable and all of its operands are also constant-castable, it can be converted to a `Const`, the numeric value of which can then be read by Python code. This provides a way to perform computation on Torii values while constructing the design.

```{todo}
link to m.Case and v.matches() below
```

Constant-castable objects are accepted anywhere a constant integer is accepted. Casting to a constant can also be done explicitly with `Const.cast`:

```{eval-rst}
.. doctest::

   >>> Const.cast(Cat(Direction.TOP, Direction.LEFT))
   (const 4'd4)

```

```{note}
   At the moment, only the following expressions are constant-castable:

   * :class:`Const`
   * :class:`Cat`

   This list will be expanded in the future.
```

## Signals


A *signal* is a value representing a (potentially) varying number. Signals can be [*assigned*](#assigning-to-signals) in a [combinatorial](#combinatorial-evaluation) or [synchronous](#synchronous-evaluation) domain, in which case they are generated as wires or registers, respectively. Signals always have a well-defined value; they cannot be uninitialized or undefined.

### Signal shapes

A signal can be created with an explicitly specified shape (any [shape-castable](#shape-casting) object); if omitted, the shape defaults to `unsigned(1)`. Although rarely useful, 0-bit signals are permitted.

```{eval-rst}
.. doctest::

   >>> Signal().shape()
   unsigned(1)
   >>> Signal(4).shape()
   unsigned(4)
   >>> Signal(range(-8, 7)).shape()
   signed(4)
   >>> Signal(Direction).shape()
   unsigned(2)
   >>> Signal(0).shape()
   unsigned(0)

```
### Signal names

Each signal has a *name*, which is used in the waveform viewer, diagnostic messages, Verilog output, and so on. In most cases, the name is omitted and inferred from the name of the variable or attribute the signal is placed into:

```{eval-rst}
.. testsetup::

   class dummy(object): pass
   self = dummy()

.. doctest::

   >>> foo = Signal()
   >>> foo.name
   'foo'
   >>> self.bar = Signal()
   >>> self.bar.name
   'bar'

```

However, the name can also be specified explicitly with the `name` parameter:

```{eval-rst}
.. doctest::

   >>> foo2 = Signal(name = 'second_foo')
   >>> foo2.name
   'second_foo'
```

The names do not need to be unique; if two signals with the same name end up in the same namespace while preparing for simulation or synthesis, one of them will be renamed to remove the ambiguity.

### Initial signal values

Each signal has an *initial value*, specified with the `reset` parameter. If the initial value is not specified explicitly, zero is used by default. An initial value can be specified with an integer or an enumeration member.

Signals [assigned](#assigning-to-signals) in a [combinatorial](#combinatorial-evaluation) domain assume their initial value when none of the assignments are [active](#active-and-inactive-assignments). Signals assigned in a [synchronous](#synchronous-evaluation) domain assume their initial value after *power-on reset* and, unless the signal is [reset-less](#reset-less-signals), *explicit reset*. Signals that are used but never assigned are equivalent to constants of their initial value.

<!-- TODO: using "reset" for "initial value" is awful, let's rename it to "init" -->

```{eval-rst}
.. doctest::

   >>> Signal(4).reset
   0
   >>> Signal(4, reset = 5).reset
   5
   >>> Signal(Direction, reset = Direction.LEFT).reset
   1

```

### Reset-less signals

Signals assigned in a [synchronous](#synchronous-evaluation) domain can be *resettable* or *reset-less*, specified with the `reset_less` parameter. If the parameter is not specified, signals are resettable by default. Resettable signals assume their [initial value](#initial-signal-values) on explicit reset, which can be asserted via the clock domain or by using `ResetInserter`. Reset-less signals are not affected by explicit reset.

<!-- TODO: link to clock domain and ResetInserter docs -->

Signals assigned in a [combinatorial](#combinatorial-evaluation) domain are not affected by the `reset_less` parameter.

```{eval-rst}
.. doctest::

   >>> Signal().reset_less
   False
   >>> Signal(reset_less=True).reset_less
   True

```

## Operators

To describe computations, Torii values can be combined with each other or with [value-castable](#value-casting) objects using a rich array of arithmetic, bitwise, logical, bit sequence, and other *operators* to form *expressions*, which are themselves values.

### Performing or describing computations?


Code written in the Python language *performs* computations on concrete objects, like integers, with the goal of calculating a concrete result:

```{eval-rst}
.. doctest::

   >>> a = 5
   >>> a + 1
   6

```

In contrast, code written in the Torii language *describes* computations on abstract objects, like [signals](#signals), with the goal of generating a hardware *circuit* that can be simulated, synthesized, and so on. Torii expressions are ordinary Python objects that represent parts of this circuit:

```{eval-rst}
.. doctest::

   >>> a = Signal(8, reset = 5)
   >>> a + 1
   (+ (sig a) (const 1'd1))

```

Although the syntax is similar, it is important to remember that Torii values exist on a higher level of abstraction than Python values. For example, expressions that include Torii values cannot be used in Python control flow structures:

```{eval-rst}
.. doctest::

   >>> if a == 0:
   ...     print('Zero!')
   Traceback (most recent call last):
     ...
   TypeError: Attempted to convert Torii value to Python boolean
```

Because the value of `a`, and therefore `a == 0`, is not known at the time when the `if` statement is executed, there is no way to decide whether the body of the statement should be executed---in fact, if the design is synthesized, by the time `a` has any concrete value, the Python program has long finished! To solve this problem, Torii provides its own [control structures](#control-structures) that, also, manipulate circuits.


### Width extension

Many of the operations described below (for example, addition, equality, bitwise OR, and part select) extend the width of one or both operands to match the width of the expression. When this happens, unsigned values are always zero-extended and signed values are always sign-extended regardless of the operation or signedness of the result.

### Arithmetic operators

Most arithmetic operations on integers provided by Python can be used on Torii values, too.

Although Python integers have unlimited precision and Torii values are represented with a [finite amount of bits](#values), arithmetics on Torii values never overflows because the width of the arithmetic expression is always sufficient to represent all possible results.

```{eval-rst}
.. doctest::

   >>> a = Signal(8)
   >>> (a + 1).shape() # needs to represent 1 to 256
   unsigned(9)
```

Similarly, although Python integers are always signed and Torii values can be either [signed or unsigned](#values), if any of the operands of an Torii arithmetic expression is signed, the expression itself is also signed, matching the behavior of Python.

```{eval-rst}
.. doctest::

   >>> a = Signal(unsigned(8))
   >>> b = Signal(signed(8))
   >>> (a + b).shape() # needs to represent -128 to 382
   signed(10)

```

While arithmetic computations never result in an overflow, [assigning](#assigning-to-signals)  their results to signals may truncate the most significant bits.

The following table lists the arithmetic operations provided by Torii:


| Operation | Description    |
|-----------|----------------|
| `a + b`   | addition       |
| `-a`      | negation       |
| `a - b`   | subtraction    |
| `a * b`   | multiplication |
| `a // b`  | floor division |
| `a % b`   | modulo         |
| `abs(a)`  | absolute value |


### Comparison operators

All comparison operations on integers provided by Python can be used on Torii values. However, due to a limitation of Python, chained comparisons (e.g. `a < b < c`) cannot be used.

Similar to arithmetic operations, if any operand of a comparison expression is signed, a signed comparison is performed. The result of a comparison is a 1-bit unsigned value.

The following table lists the comparison operations provided by Torii:

| Operation | Description           |
|-----------|-----------------------|
| `a == b`  | equality              |
| `a != b`  | inequality            |
| `a < b`   | less than             |
| `a <= b`  | less than or equal    |
| `a > b`   | greater than          |
| `a >= b`  | greater than or equal |


### Bitwise, shift, and rotate operators

All bitwise and shift operations on integers provided by Python can be used on Torii values as well.

Similar to arithmetic operations, if any operand of a bitwise expression is signed, the expression itself is signed as well. A shift expression is signed if the shifted value is signed. A rotate expression is always unsigned.

Rotate operations with variable rotate amounts cannot be efficiently synthesized for non-power-of-2 widths of the rotated value. Because of that, the rotate operations are only provided for constant rotate amounts, specified as Python {class}`int`s.

The following table lists the bitwise and shift operations provided by Torii:

| Operation          | Description                                        |
|--------------------|----------------------------------------------------|
| `~a`               | bitwise NOT; complement                            |
| `a & b`            | bitwise AND                                        |
| `a \| b`           | bitwise OR                                         |
| `a ^ b`            | bitwise XOR                                        |
| `a.implies(b)`     | bitwise [IMPLY]                                    |
| `a >> b`           | arithmetic right shift by variable amount [^1][^2] |
| `a << b`           | left shift by variable amount [^2]                 |
| `a.rotate_left(i)` | left rotate by constant amount [^3]                |
| `a.rotate_right(i)`| right rotate by constant amount [^3]               |
| `a.shift_left(i)`  | left shift by constant amount [^3]                 |
| `a.shift_right(i)` | right shift by constant amount [^3]                |


[IMPLY]: https://en.wikipedia.org/wiki/IMPLY_gate
[^1]: Logical and arithmetic right shift of an unsigned value are equivalent. Logical right shift of a signed value can be expressed by [converting it to unsigned](#conversion-operators) first.
[^2]: Shift amount must be unsigned; integer shifts in Python require the amount to be positive.
[^3]: Shift and rotate amounts can be negative, in which case the direction is reversed.


```{eval-rst}
.. note::

   Because Torii ensures that the width of a variable left shift expression is wide enough to represent any possible result, variable left shift by a wide amount produces exponentially wider intermediate values, stressing the synthesis tools:

   .. doctest::

      >>> (1 << C(0, 32)).shape()
      unsigned(4294967296)

   Although Torii will detect and reject expressions wide enough to break other tools, it is a good practice to explicitly limit the width of a shift amount in a variable left shift.

```

### Reduction operators

Bitwise reduction operations on integers are not provided by Python, but are very useful for hardware. They are similar to bitwise operations applied "sideways"; for example, if bitwise AND is a binary operator that applies AND to each pair of bits between its two operands, then reduction AND is an unary operator that applies AND to all of the bits in its sole operand.

The result of a reduction is a 1-bit unsigned value.

The following table lists the reduction operations provided by Torii:

| Operation  | Description                                  |
|------------|----------------------------------------------|
| `a.all()`  | reduction AND; are all bits set? [^4]        |
| `a.any()`  | reduction OR; is any bit set? [^4]           |
| `a.xor()`  | reduction XOR; is an odd number of bits set? |
| `a.bool()` | conversion to boolean; is non-zero? [^5]     |

[^4]: Conceptually the same as applying the Python {func}`all` or {func}`any` function to the value viewed as a collection of bits.
[^5]: Conceptually the same as applying the Python {func}`bool` function to the value viewed as an integer.


### Logical operators

Unlike the arithmetic or bitwise operators, it is not possible to change the behavior of the Python logical operators `not`, `and`, and `or`. Due to that, logical expressions in Torii are written using bitwise operations on boolean (1-bit unsigned) values, with explicit boolean conversions added where necessary.

The following table lists the Python logical expressions and their Torii equivalents:

| Python expression | Torii expression (any operands) |
|-------------------|---------------------------------|
| `not a`           | `~(a).bool()`                   |
| `a and b`         | `(a).bool() & (b).bool()`       |
| `a or b`          | `(a).bool() \| (b).bool()`      |


When the operands are known to be boolean values, such as comparisons, reductions, or boolean signals, the `.bool()` conversion may be omitted for clarity:


| Python expression | Torii expression (boolean operands) |
|-------------------|-------------------------------------|
| `not p`           | `~(p)`                              |
| `p and q`         | `(p) & (q)`                         |
| `p or q`          | `(p) \| (q)`                        |


```{eval-rst}
.. warning::

   Because of Python :ref:`operator precedence <python:operator-summary>`, logical operators bind less tightly than comparison operators whereas bitwise operators bind more tightly than comparison operators. As a result, all logical expressions in Torii **must** have parenthesized operands.

   Omitting parentheses around operands in an Torii a logical expression is likely to introduce a subtle bug:

   .. doctest::

      >>> en = Signal()
      >>> addr = Signal(8)
      >>> en & (addr == 0) # correct
      (& (sig en) (== (sig addr) (const 1'd0)))
      >>> en & addr == 0 # WRONG! addr is truncated to 1 bit
      (== (& (sig en) (sig addr)) (const 1'd0))

   .. TODO: can we detect this footgun automatically? #380

.. warning::

   When applied to Torii boolean values, the ``~`` operator computes negation, and when applied to Python boolean values, the ``not`` operator also computes negation. However, the ``~`` operator applied to Python boolean values produces an unexpected result:

   .. doctest::

      >>> ~False
      -1
      >>> ~True
      -2

   Because of this, Python booleans used in Torii logical expressions **must** be negated with the ``not`` operator, not the ``~`` operator. Negating a Python boolean with the ``~`` operator in an Torii logical expression is likely to introduce a subtle bug:

   .. doctest::

      >>> stb = Signal()
      >>> use_stb = True
      >>> (not use_stb) | stb # correct
      (| (const 1'd0) (sig stb))
      >>> ~use_stb | stb # WRONG! MSB of 2-bit wide OR expression is always 1
      (| (const 2'sd-2) (sig stb))

   Torii automatically detects some cases of misuse of ``~`` and emits a detailed diagnostic message.

   .. TODO: this isn't quite reliable, #380

```

### Bit sequence operators

Apart from acting as numbers, Torii values can also be treated as bit {ref}`sequences <python:typesseq>`, supporting slicing, concatenation, replication, and other sequence operations. Since some of the operators Python defines for sequences clash with the operators it defines for numbers, Torii gives these operators a different name. Except for the names, Torii values follow Python sequence semantics, with the least significant bit at index 0.

Because every Torii value has a single fixed width, bit slicing and replication operations require the subscripts and count to be constant, specified as Python {class}`int`s. It is often useful to slice a value with a constant width and variable offset, but this cannot be expressed with the Python slice notation. To solve this problem, Torii provides additional *part select* operations with the necessary semantics.

The result of any bit sequence operation is an unsigned value.

The following table lists the bit sequence operations provided by Torii:


| Operation             | Description                                      |
|-----------------------|--------------------------------------------------|
| `len(a)`              | bit length; value width [^6]                     |
| `a[i:j:k]`            | bit slicing by constant subscripts [^7]          |
| `iter(a)`             | bit iteration                                    |
| `a.bit_select(b, w)`  | overlapping part select with variable offset     |
| `a.word_select(b, w)` | non-overlapping part select with variable offset |
| `Cat(a, b, ...)`      | concatenation [^8]                               |
| `a.replicate(n)`      | replication                                      |


[^6]: Words "length" and "width" have the same meaning when talking about Torii values. Conventionally, "width" is used.
[^7]: All variations of the Python slice notation are supported, including "extended slicing". E.g. all of `a[0]`, `a[1:9]`, `a[2:]`, `a[:-2]`, `a[::-1]`, `a[0:8:2]` select bits in the same way as other Python sequence types select their elements.
[^8]: In the concatenated value, `a` occupies the least significant bits, and `b` the most significant bits. An arbitrary number of arguments for `Cat` is supported.

For the operators introduced by Torii, the following table explains them in terms of Python code operating on tuples of bits rather than Torii values:


| Torii operation       | Equivalent Python code |
|-----------------------|------------------------|
| `Cat(a, b)`           | `a + b`                |
| `a.replicate(n)`      | `a * n`                |
| `a.bit_select(b, w)`  | `a[b:b+w]`             |
| `a.word_select(b, w)` | `a[b*w:b*w+w]`         |


```{warning}
In Python, the digits of a number are written right-to-left (0th exponent at the right), and the elements of a sequence are written left-to-right (0th element at the left). This mismatch can cause confusion when numeric operations (like shifts) are mixed with bit sequence operations (like concatenations). For example, ``Cat(C(0b1001), C(0b1010))`` has the same value as ``C(0b1010_1001)``, ``val[4:]`` is equivalent to ``val >> 4``, and ``val[-1]`` refers to the most significant bit.

Such confusion can often be avoided by not using numeric and bit sequence operations in the same expression. For example, although it may seem natural to describe a shift register with a numeric shift and a sequence slice operations, using sequence operations alone would make it easier to understand.
```

```{note}
Could Torii have used a different indexing or iteration order for values? Yes, but it would be necessary to either place the most significant bit at index 0, or deliberately break the Python sequence type interface. Both of these options would cause more issues than using different iteration orders for numeric and sequence operations.
```

### Conversion operators

The `.as_signed()` and `.as_unsigned()` conversion operators reinterpret the bits of a value with the requested signedness. This is useful when the same value is sometimes treated as signed and sometimes as unsigned, or when a signed value is constructed using slices or concatenations. For example, `(pc + imm[:7].as_signed()).as_unsigned()` sign-extends the 7 least significant bits of `imm` to the width of `pc`, performs the addition, and produces an unsigned result.


### Choice operator

The `Mux(sel, val1, val0)` choice expression (similar to the {ref}`conditional expression <python:if_expr>` in Python) is equal to the operand `val1` if `sel` is non-zero, and to the other operand `val0` otherwise. If any of `val1` or `val0` are signed, the expression itself is signed as well.


## Modules

A *module* is a unit of the Torii design hierarchy: the smallest collection of logic that can be independently simulated, synthesized, or otherwise processed. Modules associate signals with [control domains](#control-domains), provide [control structures](#control-structures), manage clock domains, and aggregate submodules.

<!-- TODO: link to clock domains -->
<!-- TODO: link to submodules -->

Every Torii design starts with a fresh module:

```{eval-rst}
.. doctest::

   >>> m = Module()

```
### Control domains

A *control domain* is a named group of [signals](#signals) that change their value in identical conditions.

All designs have a single predefined *combinatorial domain*, containing all signals that change immediately when any value used to compute them changes. The name `comb` is reserved for the combinatorial domain.

A design can also have any amount of user-defined *synchronous domains*, also called *clock domains*, containing signals that change when a specific edge occurs on the domain's clock signal or, for domains with asynchronous reset, on the domain's reset signal. Most modules only use a single synchronous domain, conventionally called `sync`, but the name `sync` does not have to be used, and lacks any special meaning beyond being the default.

The behavior of assignments differs for signals in [combinatorial](#combinatorial-evaluation) and [synchronous](#synchronous-evaluation) domains. Collectively, signals in synchronous domains contain the state of a design, whereas signals in the combinatorial domain cannot form feedback loops or hold state.

<!-- TODO: link to clock domains -->

### Assigning to signals

*Assignments* are used to change the values of signals. An assignment statement can be introduced with the `.eq(...)` syntax:

```{eval-rst}
.. doctest::

   >>> s = Signal()
   >>> s.eq(1)
   (eq (sig s) (const 1'd1))

```

Similar to [how Torii operators work](#performing-or-describing-computations), an Torii assignment is an ordinary Python object used to describe a part of a circuit. An assignment does not have any effect on the signal it changes until it is added to a control domain in a module. Once added, it introduces logic into the circuit generated from that module.

### Assignment targets

The target of an assignment can be more complex than a single signal. It is possible to assign to any combination of [signals](#signals), [bit slices](#bit-sequence-operators), [concatenations](#bit-sequence-operators), and [part selects](#bit-sequence-operators) as long as it includes no other values:

<!-- TODO: mention arrays, records, user values -->

```{eval-rst}
.. doctest::

   >>> a = Signal(8)
   >>> b = Signal(4)
   >>> Cat(a, b).eq(0)
   (eq (cat (sig a) (sig b)) (const 1'd0))
   >>> a[:4].eq(b)
   (eq (slice (sig a) 0:4) (sig b))
   >>> Cat(a, a).bit_select(b, 2).eq(0b11)
   (eq (part (cat (sig a) (sig a)) (sig b) 2 1) (const 2'd3))

```

### Assignment domains

The `m.d.<domain> += ...` syntax is used to add assignments to a specific control domain in a module. It can add just a single assignment, or an entire sequence of them:

```{eval-rst}
.. testcode::

   a = Signal()
   b = Signal()
   c = Signal()
   m.d.comb += a.eq(1)
   m.d.sync += [
       b.eq(c),
       c.eq(b),
   ]

```

If the name of a domain is not known upfront, the `m.d['<domain>'] += ...` syntax can be used instead:

```{eval-rst}
.. testcode::

   def add_toggle(num):
       t = Signal()
       m.d[f'sync_{num}'] += t.eq(~t)
   add_toggle(2)

```

Every signal included in the target of an assignment becomes a part of the domain, or equivalently, *driven* by that domain. A signal can be either undriven or driven by exactly one domain; it is an error to add two assignments to the same signal to two different domains:

```{eval-rst}
.. doctest::

   >>> d = Signal()
   >>> m.d.comb += d.eq(1)
   >>> m.d.sync += d.eq(0)
   Traceback (most recent call last):
     ...
   torii.hdl.dsl.SyntaxError: Driver-driver conflict: trying to drive (sig d) from d.sync, but it is already driven from d.comb

.. note::

   Clearly, Torii code that drives a single bit of a signal from two different domains does not describe a meaningful circuit. However, driving two different bits of a signal from two different domains does not inherently cause such a conflict. Would Torii accept the following code?

   .. testcode::

      e = Signal(2)
      m.d.comb += e[0].eq(0)
      m.d.sync += e[1].eq(1)

   The answer is no. While this kind of code is occasionally useful, rejecting it greatly simplifies backends, simulators, and analyzers.

```

### Assignment order

Unlike with two different domains, adding multiple assignments to the same signal to the same domain is well-defined.

Assignments to different signal bits apply independently. For example, the following two snippets are equivalent:

```{eval-rst}
.. testcode::

   a = Signal(8)
   m.d.comb += [
       a[0:4].eq(C(1, 4)),
       a[4:8].eq(C(2, 4)),
   ]

.. testcode::

   a = Signal(8)
   m.d.comb += a.eq(Cat(C(1, 4), C(2, 4)))

```

If multiple assignments change the value of the same signal bits, the assignment that is added last determines the final value. For example, the following two snippets are equivalent:

```{eval-rst}
.. testcode::

   b = Signal(9)
   m.d.comb += [
       b[0:9].eq(Cat(C(1, 3), C(2, 3), C(3, 3))),
       b[0:6].eq(Cat(C(4, 3), C(5, 3))),
       b[3:6].eq(C(6, 3)),
   ]

.. testcode::

   b = Signal(9)
   m.d.comb += b.eq(Cat(C(4, 3), C(6, 3), C(3, 3)))

```

Multiple assignments to the same signal bits are more useful when combined with control structures, which can make some of the assignments [active or inactive](#active-and-inactive-assignments). If all assignments to some signal bits are [inactive](#active-and-inactive-assignments), their final values are determined by the signal's domain, [combinatorial](#combinatorial-evaluation) or [synchronous](#synchronous-evaluation).


### Control structures

Although it is possible to write any decision tree as a combination of [assignments](#assigning-to-signals) and [choice expressions](#choice-operator), Torii provides *control structures* tailored for this task: If, Switch, and FSM. The syntax of all control structures is based on {ref}`context managers <python:context-managers>` and uses `with` blocks, for example:

<!-- TODO: link to relevant subsections -->

```{eval-rst}
.. testcode::

   timer = Signal(8)
   with m.If(timer == 0):
       m.d.sync += timer.eq(10)
   with m.Else():
       m.d.sync += timer.eq(timer - 1)

```

While some Torii control structures are superficially similar to imperative control flow statements (such as Python's `if`), their function---together with [expressions](#performing-or-describing-computations) and [assignments](#assigning-to-signals)---is to describe circuits. The code above is equivalent to:

```{eval-rst}
.. testcode::

   timer = Signal(8)
   m.d.sync += timer.eq(Mux(timer == 0, 10, timer - 1))

```

Because all branches of a decision tree affect the generated circuit, all of the Python code inside Torii control structures is always evaluated in the order in which it appears in the program. This can be observed through Python code with side effects, such as {func}`print`:

```{eval-rst}
.. testcode::

   timer = Signal(8)
   with m.If(timer == 0):
       print('inside `If`')
       m.d.sync += timer.eq(10)
   with m.Else():
       print('inside `Else`')
       m.d.sync += timer.eq(timer - 1)

.. testoutput::

   inside `If`
   inside `Else`

```

### Active and inactive assignments


An assignment added inside an Torii control structure, i.e. `with m.<...>:` block, is *active* if the condition of the control structure is satisfied, and *inactive* otherwise. For any given set of conditions, the final value of every signal assigned in a module is the same as if the inactive assignments were removed and the active assignments were performed unconditionally, taking into account the [assignment order](#assignment-order).

For example, there are two possible cases in the circuit generated from the following code:

```{eval-rst}
.. testcode::

   timer = Signal(8)
   m.d.sync += timer.eq(timer - 1)
   with m.If(timer == 0):
       m.d.sync += timer.eq(10)

```

When `timer == 0` is true, the code reduces to:

```py
   m.d.sync += timer.eq(timer - 1)
   m.d.sync += timer.eq(10)
```

Due to the [assignment order](#assignment-order), it further reduces to:

```py
   m.d.sync += timer.eq(10)
```

When `timer == 0` is false, the code reduces to:

```py
   m.d.sync += timer.eq(timer - 1)
```

Combining these cases together, the code above is equivalent to:

```{eval-rst}
.. testcode::

   timer = Signal(8)
   m.d.sync += timer.eq(Mux(timer == 0, 10, timer - 1))

```

### Combinatorial evaluation


Signals in the combinatorial [control domain](#control-domains) change whenever any value used to compute them changes. The final value of a combinatorial signal is equal to its [initial value](#initial-signal-values) updated by the [active assignments](#active-and-inactive-assignments) in the [assignment order](#assignment-order). Combinatorial signals cannot hold any state.

Consider the following code:

```{eval-rst}
.. testsetup::
   en = Signal()
   b = Signal(8)

.. testcode::

   a = Signal(8, reset=1)
   with m.If(en):
       m.d.comb += a.eq(b + 1)

```

Whenever the signals `en` or `b` change, the signal `a` changes as well. If `en` is false, the final value of `a` is its initial value, `1`. If `en` is true, the final value of `a` is equal to `b + 1`.

A combinatorial signal that is computed directly or indirectly based on its own value is a part of a *combinatorial feedback loop*, sometimes shortened to just *feedback loop*. Combinatorial feedback loops can be stable (i.e. implement a constant driver or a transparent latch), or unstable (i.e. implement a ring oscillator). Torii prohibits using assignments to describe any kind of a combinatorial feedback loop, including transparent latches.

```{warning}

The current version of Torii does not detect combinatorial feedback loops, but processes the design under the assumption that there aren't any. If the design does in fact contain a combinatorial feedback loop, it will likely be **silently miscompiled**, though some cases will be detected during synthesis or place & route.

This hazard will be eliminated in the future.

```

<!-- TODO: fix this, either as a part of https://github.com/amaranth-lang/amaranth/issues/6 or on its own -->

```{note}
In the exceedingly rare case when a combinatorial feedback loop is desirable, it is possible to implement it by directly instantiating technology primitives (e.g. device-specific LUTs or latches). This is also the only way to introduce a combinatorial feedback loop with well-defined behavior in simulation and synthesis, regardless of the HDL being used.
```

### Synchronous evaluation

Signals in synchronous [control domains](#control-domains) change whenever a specific transition (positive or negative edge) occurs on the clock of the synchronous domain. In addition, the signals in clock domains with an asynchronous reset change when such a reset is asserted. The final value of a synchronous signal is equal to its [initial value](#initial-signal-values) if the reset (of any type) is asserted, or to its current value updated by the [active assignments](#active-and-inactive-assignments) in the [assignment order](#assignment-order) otherwise. Synchronous signals always hold state.

<!-- TODO: link to clock domains -->


[two's complement]: https://en.wikipedia.org/wiki/Two's_complement
