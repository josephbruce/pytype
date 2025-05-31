from pytype.tests import test_base

class UnusedCoroutineTest(test_base.BaseTest):
  """Tests for the unused-coroutine error."""

  def test_trigger_unused_coroutine(self):
    errors = self.Check('''
      async def sample_coro():
        return 1
      sample_coro()
    ''')
    self.assertErrorRegexes(errors, {"unused-coroutine": r"Coroutine result was not used"})

  def test_correct_coroutine_usage(self):
    ty = self.Infer('''
      import asyncio

      async def sample_coro():
        return 1

      async def main():
        await sample_coro()
        x = sample_coro()
        asyncio.create_task(sample_coro())
        my_list = [sample_coro()]
        my_dict = {"a": sample_coro()}
        return x, my_list, my_dict

      def regular_func(): return 1
      regular_func()
    ''')
    self.assertNoCrash(ty)
    # We expect no "unused-coroutine" errors.
    # If self.Check or self.Infer raises an error not in assertErrorRegexes, the test fails.
    # So, not calling assertErrorRegexes here implicitly checks for no errors.
    # Check that "unused-coroutine" is not in the errors:
    error_names = [e.name for e in ty.errors]
    self.assertNotIn("unused-coroutine", error_names)

  def test_wrapper_returns_unused_coroutine(self):
    errors = self.Check('''
      async def sample_coro():
        return 1
      def wrapper():
        return sample_coro()
      wrapper()
    ''')
    self.assertErrorRegexes(errors, {"unused-coroutine": r"Coroutine result was not used"})

  def test_assign_to_underscore(self):
    ty = self.Infer('''
      async def sample_coro():
        return 1
      _ = sample_coro()
    ''')
    self.assertNoCrash(ty)
    error_names = [e.name for e in ty.errors]
    self.assertNotIn("unused-coroutine", error_names)

  def test_coroutine_in_used_expression(self):
    # This should ideally not trigger 'unused-coroutine'.
    # It will likely trigger a different error like 'unsupported-operands'.
    errors = self.Check('''
      async def sample_coro():
        return 1
      y = 1 + sample_coro() # This is a TypeError at runtime
    ''')
    error_names = [e.name for e in errors.errors]
    self.assertNotIn("unused-coroutine", error_names)
    # Optionally, assert that the expected error (e.g., unsupported-operands) IS present
    self.assertErrorRegexes(errors, {"unsupported-operands": r"unsupported operand type.*for \+"})
