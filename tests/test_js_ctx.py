import ultralight_cffi as ultra


def test_scoped_global__get_name__set_name(lib):
    """Tests the ``scoped_global``, ``get_name``, and ``set_name`` functions of
    :mod:`ultra.js_ctx`.
    """

    with ultra.js_ctx.scoped_global() as ctx1:
        # Expectation - Making changes to the context should be persisted:
        ctx1_name = 'sample context 1'
        ultra.js_ctx.set_name(ctx1, ctx1_name)
        assert ultra.js_ctx.get_name(ctx1) == ctx1_name

        # Expectation - Creating multiple contexts should remain independent:
        with ultra.js_ctx.scoped_global() as ctx2:
            ctx2_name = 'sample context 2'
            ultra.js_ctx.set_name(ctx2, ctx2_name)
            assert ultra.js_ctx.get_name(ctx2) == ctx2_name
            assert ultra.js_ctx.get_name(ctx1) == ctx1_name

        # Expectation - Retaining an existing context should return the same context,
        # without fully releasing the original context prematurely:
        with ultra.js_ctx.scoped_global(ctx1) as ctx3:
            assert ctx3 == ctx1
            assert ultra.js_ctx.get_name(ctx3) == ctx1_name
        assert ultra.js_ctx.get_name(ctx1) == ctx1_name

    # TODO: ideally there would be a way to confirm that the context was fully released/
    # garbage collected - other than expecting a segfault if the context is used after
    # being freed.
