from __future__ import annotations

import inspect
from typing import Any


class Pipeline:
    """A composed sequence of Verity prompts connected with the ``>>`` operator.

    The output of each step is forwarded to the next:

    - If the output is a ``dict``, it is unpacked as keyword arguments.
    - Otherwise it is passed as the first positional argument.

    Example::

        pipeline = extract >> summarize
        result = await pipeline(text="Some long article...")
    """

    def __init__(self, *steps: Any) -> None:
        self._steps = steps

    def __rshift__(self, other: Any) -> Pipeline:
        return Pipeline(*self._steps, other)

    async def __call__(self, **kwargs: Any) -> Any:
        result: Any = None
        for i, step in enumerate(self._steps):
            if i == 0:
                result = await step(**kwargs)
            elif isinstance(result, dict):
                result = await step(**result)
            else:
                # Pass the result as the first parameter of the next step
                sig = inspect.signature(step)
                params = list(sig.parameters.keys())
                if not params:
                    result = await step()
                else:
                    result = await step(**{params[0]: result})
        return result
