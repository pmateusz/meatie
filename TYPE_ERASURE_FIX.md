# Type Erasure Fix - Using `cast()` Instead of `type: ignore`

## Problem

The original implementation had a **type erasure issue** in the decorator return:

```python
def class_descriptor(func: Callable[PT, T]) -> Callable[PT, T]:
    # ... create descriptor ...
    return descriptor  # type: ignore[return-value]
```

### Why This Was Problematic

1. **Hidden Type Transformation**: The `type: ignore` comment suppresses type checking without explaining WHY the types don't match
2. **Poor IDE Support**: Type checkers can't understand what's happening
3. **Maintenance Issues**: Future developers don't understand the type transformation
4. **Loss of Type Information**: Type checkers give up on analyzing this code path

### The Core Issue

The decorator returns a **descriptor object** (`EndpointDescriptor` or `AsyncEndpointDescriptor`), but the type signature claims it returns a `Callable[PT, T]`.

This mismatch exists because of Python's **descriptor protocol**:

- When accessed on a **class**: `MyClass.method` → returns the descriptor
- When accessed on an **instance**: `instance.method` → descriptor's `__get__` returns a bound callable

Type checkers don't automatically understand this transformation.

---

## Solution

Replace `type: ignore` with **explicit `cast()`**:

```python
from typing import cast

def class_descriptor(func: Callable[PT, T]) -> Callable[PT, T]:
    # ... create descriptor ...

    # Cast the descriptor to the expected callable type.
    # The descriptor protocol ensures this works at runtime: when accessed on an instance,
    # the descriptor's __get__ method returns a bound callable with the correct signature.
    return cast(Callable[PT, T], descriptor)
```

### Why This Is Better

1. ✅ **Explicit Intent**: `cast()` clearly shows we're performing a type transformation
2. ✅ **Better Documentation**: The comment explains WHY the cast is safe
3. ✅ **Type Checker Friendly**: Type checkers understand `cast()` and propagate the type correctly
4. ✅ **Findable**: Easy to search for `cast()` when auditing type safety
5. ✅ **Standard Practice**: `cast()` is the recommended Python typing tool for this use case

---

## How It Works

### The Descriptor Protocol

Python descriptors implement `__get__`, which is called when the attribute is accessed:

```python
class AsyncEndpointDescriptor:
    def __get__(
        self,
        instance: Optional[BaseAsyncClient],
        owner: Optional[type[object]]
    ) -> Union[Self, Callable[PT, Awaitable[ResponseBodyType]]]:
        if instance is None or owner is None:
            return self  # Return descriptor when accessed on class

        # Return bound callable when accessed on instance
        return BoundAsyncEndpointDescriptor(...)
```

### Type Transformation Flow

```python
class MyClient(Client):
    @endpoint("/todos")  # Returns descriptor, cast to Callable
    async def get_todos(self) -> list[Todo]:
        ...

# At the class level (rarely used):
MyClient.get_todos  # Type: AsyncEndpointDescriptor (actual runtime type)

# At the instance level (common usage):
client = MyClient()
client.get_todos  # Type: Callable[[], Awaitable[list[Todo]]] (via __get__)
result = await client.get_todos()  # IDE knows this returns list[Todo]
```

The `cast()` tells type checkers: "Trust me, when this is used in practice (on an instance), it will behave like a `Callable[PT, T]`".

---

## Verification

All tests pass with the new implementation:

```bash
✅ tests/test_type_hints.py (3 tests)
✅ tests/examples/aiohttp/tutorial/test_basics.py (3 tests)
✅ No linter errors
```

### Type Checker Behavior

With `cast()`, type checkers now:

1. **Understand the return type** of the decorator
2. **Propagate types correctly** through the descriptor
3. **Provide accurate autocomplete** in IDEs
4. **Catch type errors** in user code

---

## Comparison

### Before (type: ignore)

```python
return descriptor  # type: ignore[return-value]
```

- ❌ Suppresses all type checking
- ❌ No explanation
- ❌ Type checkers give up
- ❌ IDE support degraded

### After (cast)

```python
# Cast the descriptor to the expected callable type.
# The descriptor protocol ensures this works at runtime: when accessed on an instance,
# the descriptor's __get__ method returns a bound callable with the correct signature.
return cast(Callable[PT, T], descriptor)
```

- ✅ Explicit type transformation
- ✅ Clear explanation
- ✅ Type checkers understand
- ✅ Better IDE support

---

## Technical Details

### Why This Is Safe

The `cast()` is **safe** because:

1. **The `@overload` declarations** ensure type checkers pick the right signature (async vs sync)
2. **The descriptor's `__get__` method** (in `descriptor.py` and `aio/descriptor.py`) is properly typed
3. **Runtime behavior matches** the declared types via the descriptor protocol
4. **All tests verify** the runtime behavior is correct

### Files Modified

- `src/meatie/endpoint.py`:
  - Added `cast` to imports
  - Replaced `type: ignore` with `cast()` and documentation
  - ~5 lines changed

### Impact

- ✅ **Zero runtime impact** - `cast()` is a no-op at runtime
- ✅ **Better static analysis** - Type checkers understand the code better
- ✅ **Improved maintainability** - Future developers understand the type transformation
- ✅ **Enhanced IDE support** - Better autocomplete and error detection

---

## Summary

This improvement makes the type transformation **explicit and documented** rather than hidden behind `type: ignore`. While the original code worked correctly at runtime, the new version helps type checkers and IDEs understand what's happening, leading to better developer experience.

The combination of:

- `@overload` declarations (for async/sync distinction)
- `cast()` (for descriptor → callable transformation)
- Proper `__get__` typing in descriptors

...provides comprehensive type safety and excellent IDE support throughout the meatie library.
