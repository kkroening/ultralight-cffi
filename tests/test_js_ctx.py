import ultralight_cffi as ultra


def test_JSGlobalContext__new__enter__exit(lib):
    """Tests the ``scoped_global``, ``get_name``, and ``set_name`` functions of
    :mod:`ultra.js_ctx`.
    """

    with ultra.JSGlobalContext.new() as ctx1:
        # Expectation - Making changes to the context should be persisted:
        ctx1_name = 'sample context 1'
        ctx1.set_name(ctx1_name)
        assert ctx1.get_name() == ctx1_name

        # Expectation - Creating multiple contexts should remain independent:
        with ultra.JSGlobalContext.new() as ctx2:
            ctx2_name = 'sample context 2'
            ctx2.set_name(ctx2_name)
            assert ctx2.get_name() == ctx2_name
            assert ctx1.get_name() == ctx1_name

        # Expectation - Retaining an existing context should return the same context,
        # without fully releasing the original context prematurely:
        with ultra.JSGlobalContext(ctx1.ref) as ctx3:
            assert ctx3.ref == ctx1.ref
        assert ctx1.get_name() == ctx1_name  # confirm still alive

    # TODO: ideally there would be a way to confirm that the context was fully released/
    # garbage collected - other than expecting a segfault if the context is used after
    # being freed.
