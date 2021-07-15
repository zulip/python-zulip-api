- Replace `asyncio.get_event_loop()` by `asyncio.get_running_loop()` as soon
  as support for Python 3.6 is not necessary any more.
  Reason: `get_event_loop` is depcrecated since Python 3.10.
  See: https://docs.python.org/3/library/asyncio-eventloop.html#asyncio.get_event_loop
- Use `asyncio.run()` to run the `run()`-method as soon as support for Python
  3.6 has been dropped.
