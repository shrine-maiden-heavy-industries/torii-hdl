# First-in First-out Queues

The {py:mod}`torii.lib.fifo` module provides building blocks for first-in, first-out queues.

```{eval-rst}
.. autoclass:: torii.lib.fifo.FIFOInterface
```

:::{note}
The {py:class}`FIFOInterface <torii.lib.fifo.FIFOInterface` class can be used directly to substitute a FIFO in tests, or inherited from in a custom FIFO implementation.
:::

```{eval-rst}
.. autoclass:: torii.lib.fifo.SyncFIFO
.. autoclass:: torii.lib.fifo.SyncFIFOBuffered
.. autoclass:: torii.lib.fifo.AsyncFIFO
.. autoclass:: torii.lib.fifo.AsyncFIFOBuffered
```
