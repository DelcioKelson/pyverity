"""Tests for pyverity.effects."""

from pyverity.effects import Cost, Fallible, Latent


class TestLatent:
    def test_default_seconds_is_none(self):
        effect = Latent()
        assert effect.seconds is None

    def test_with_seconds(self):
        effect = Latent(2.5)
        assert effect.seconds == 2.5

    def test_repr_with_seconds(self):
        assert repr(Latent(1.0)) == "Latent(1.0)"

    def test_repr_without_seconds(self):
        assert repr(Latent()) == "Latent"


class TestFallible:
    def test_is_singleton(self):
        from pyverity.effects import _FallibleSingleton
        a = _FallibleSingleton()
        b = _FallibleSingleton()
        assert a is b

    def test_fallible_singleton_instance(self):
        from pyverity.effects import _FallibleSingleton
        assert isinstance(Fallible, _FallibleSingleton)

    def test_repr(self):
        assert repr(Fallible) == "Fallible"


class TestCost:
    def test_default_max_usd_is_none(self):
        effect = Cost()
        assert effect.max_usd is None

    def test_with_max_usd(self):
        effect = Cost(0.01)
        assert effect.max_usd == 0.01

    def test_repr_with_value(self):
        assert repr(Cost(0.05)) == "Cost(0.05)"

    def test_repr_without_value(self):
        assert repr(Cost()) == "Cost"
