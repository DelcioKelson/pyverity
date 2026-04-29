"""Tests for pyverity.pipeline."""

import pytest

from pyverity.pipeline import Pipeline


async def _double(x: int) -> int:
    return x * 2


async def _add_ten(x: int) -> int:
    return x + 10


async def _to_dict(x: int) -> dict:
    return {"value": x}


async def _from_dict(value: int) -> int:
    return value + 1


class TestPipeline:
    async def test_single_step(self):
        pipeline = Pipeline(_double)
        result = await pipeline(x=5)
        assert result == 10

    async def test_two_steps_scalar(self):
        pipeline = Pipeline(_double, _add_ten)
        result = await pipeline(x=3)
        # double(3) = 6, add_ten(6) = 16
        assert result == 16

    async def test_dict_output_unpacked_as_kwargs(self):
        pipeline = Pipeline(_to_dict, _from_dict)
        result = await pipeline(x=9)
        # _to_dict(9) = {"value": 9}, _from_dict(value=9) = 10
        assert result == 10

    async def test_rshift_creates_pipeline(self):
        class FakePrompt:
            async def __call__(self, **kwargs):
                return kwargs.get("x", 0) + 1

            def __rshift__(self, other):
                return Pipeline(self, other)

        p = FakePrompt()
        pipeline = p >> _add_ten
        assert isinstance(pipeline, Pipeline)

    async def test_pipeline_rshift_extends(self):
        pipeline1 = Pipeline(_double)
        pipeline2 = pipeline1 >> _add_ten
        assert isinstance(pipeline2, Pipeline)
        result = await pipeline2(x=2)
        # double(2) = 4, add_ten(4) = 14
        assert result == 14
