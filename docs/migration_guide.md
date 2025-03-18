# Torii v0.X to v1.0 Migration Guide

```{todo}
This document is a work in progress and should be updated as the progression v1.0 progresses
```

## Module Changes

### `DomainRenamer`

In past versions of Torii, you could use the {py:class}`DomainRenamer <torii.hdl.xfrm.DomainRenamer>` in two ways, the first was to pass a single string into it, which would be used to re-map the `sync` domain in the wrapped elaboratables to that domain, or pass a dictionary literally to map one or more domains.

These have been replaced with using `kwargs` to more directly display the intent of the renamer over passing a single string, and also to clean up visual noise when passing a dictionary.

```python
DomainRenamer('meow')(elab)

DomainRenamer({'sync': 'meow'})(elab)
```

This should now be written as follows:

```python
DomainRenamer(sync = 'meow')(elab)
```

If you need to pass a dictionary that is built at runtime to the domain renamer, then you can simply un-pack the dictionary into the constructor like so:

```python
DomainRenamer(**domain_map)(elab)
```
