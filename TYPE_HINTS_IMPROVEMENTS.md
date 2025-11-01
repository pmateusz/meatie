# Type Hints Improvements - Phase 1, Point 1

## Summary

Improved IDE type hinting support for the `@endpoint` decorator by adding `@overload` declarations that distinguish between async and sync functions.

## Changes Made

### 1. Enhanced `src/meatie/endpoint.py`

**Added:**

- Import `Awaitable` and `overload` from typing
- Two `@overload` declarations:
  - One for async functions: `Callable[[Callable[PT, Awaitable[T]]], Callable[PT, Awaitable[T]]]`
  - One for sync functions: `Callable[[Callable[PT, T]], Callable[PT, T]]`
- Updated the implementation signature to use a `Union` of both types
- Enhanced docstring to document type preservation behavior

**Benefits:**

- IDEs can now distinguish between async and sync decorated methods
- Better type inference for return types (Awaitable[T] vs T)
- Preserved parameter type information through ParamSpec (PT)
- Full autocomplete support for method parameters and return values

### 2. Created `tests/test_type_hints.py`

A comprehensive test suite that verifies:

- Async endpoint descriptors are correctly created
- HTTP methods are properly inferred
- Parameters are correctly registered (query, path, body)
- Method signatures are preserved for IDE inspection
- Pydantic models work correctly with type hints
- Type annotations are properly maintained

**Test Coverage:**

- `test_async_endpoint_return_types()` - Verifies descriptor types and HTTP methods
- `test_async_endpoint_parameter_types()` - Verifies parameter registration
- `test_endpoint_decorator_preserves_signatures()` - Verifies method accessibility
- `test_chained_method_calls_preserve_types()` - Verifies Pydantic integration
- `test_reveal_decorator_type_for_documentation()` - Documents decorator behavior

All tests pass ✅

### 3. Created `tests/examples/type_hints_demo.py`

A demonstration file showing real-world usage with detailed comments explaining what IDEs should infer. Includes examples of:

- Basic async endpoints with no parameters
- Path parameters
- Query parameters (required and optional)
- Body parameters
- Mixed parameters (path + body)
- Different return types (Model, list[Model], int, None, bytes, str)

## Backward Compatibility

✅ **Fully backward compatible** - All existing tests pass:

- `tests/examples/` (26 tests) - All pass
- `tests/client/aiohttp/` (64 tests) - All pass
- No breaking changes to existing API

## IDE Support Improvements

### Before

```python
@endpoint("/todos")
async def get_todos(self) -> list[Todo]: ...
# IDE sees: Callable[..., T] (generic, unclear if async)
```

### After

```python
@endpoint("/todos")
async def get_todos(self) -> list[Todo]: ...
# IDE sees: Callable[[], Awaitable[list[Todo]]]
# ✅ Knows it's async
# ✅ Knows it returns list[Todo] after await
# ✅ Knows there are no required parameters
```

## Type Checking Benefits

IDEs and type checkers now correctly understand:

1. **Async vs Sync**: Can distinguish `async def` from `def`
2. **Return Types**: Properly infer `Awaitable[T]` for async, `T` for sync
3. **Parameters**: Full parameter information preserved via ParamSpec
4. **Autocomplete**: Works on returned objects (e.g., `user.name`, `post.title`)
5. **Required vs Optional**: Correctly shows which parameters have defaults
6. **Error Detection**: Can catch missing required parameters at type-check time

## Testing

Run the new tests:

```bash
uv run pytest tests/test_type_hints.py -v
```

Run the demo (to see IDE hints in action):

```bash
# Open tests/examples/type_hints_demo.py in your IDE
# Hover over variables and methods to see type inference
```

Verify backward compatibility:

```bash
uv run pytest tests/examples/ -v
uv run pytest tests/client/aiohttp/ -v
```

## Next Steps (Future Phases)

This completes **Phase 1, Point 1** of the type hints improvement plan.

Future enhancements could include:

- **Phase 1, Point 2**: Create a `Stub` or `EndpointStub` protocol
- **Phase 1, Point 3**: Add generic constraints to Context types
- **Phase 2**: Enhanced type safety for `api_ref` and option builders
- **Phase 3**: Documentation and `.pyi` stub files

## Technical Details

### How It Works

The `@overload` decorator provides static type checkers (mypy, pyright) with multiple type signatures to choose from. When decorating an async function, the first overload matches; when decorating a sync function, the second overload matches.

The actual implementation uses a Union type that encompasses both cases, with runtime behavior determined by `inspect.iscoroutinefunction()`.

### Key Files Modified

- `src/meatie/endpoint.py` - Added @overload declarations
- `tests/test_type_hints.py` - New test file (5 tests)
- `tests/examples/type_hints_demo.py` - New demo file

### Lines Changed

- Modified: ~40 lines in `src/meatie/endpoint.py`
- Added: ~215 lines in `tests/test_type_hints.py`
- Added: ~200 lines in `tests/examples/type_hints_demo.py`

Total: ~455 lines added/modified

## Verification

✅ All new tests pass (5/5)
✅ All existing example tests pass (26/26)
✅ All existing client tests pass (64/64)
✅ No linter errors
✅ Backward compatible
✅ Type hints improved for IDE support

## Impact

This improvement enhances the developer experience for all users of the meatie library by providing:

- Better IDE autocomplete
- Improved error detection at development time
- Clearer type information in documentation
- More confidence when writing API client code

No changes required to existing code - improvements are automatic for all decorated methods.
