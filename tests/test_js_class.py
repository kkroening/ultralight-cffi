import gc
import pytest
import threading
import ultralight_cffi as ultra


def do_thing(js_ctx):
    finalized = []

    class MyClass(ultra.JSClass):
        def _initialize(self, obj: ultra.JSObject):
            print('MyClass initialize obj', threading.get_ident(), obj)

        def _finalize(self, obj_ref: ultra.JSObjectRef):
            print(
                'MyClass finalize obj',
                threading.get_ident(),
                obj_ref,
                ultra.JSClass._active_instances,
            )
            finalized.append(obj_ref)

    print('Creating class')
    jcls = MyClass()

    print('Creating object')
    jobj_ref = ultra.JSObjectMake(js_ctx.ref, jcls.ref, ultra.NULL)
    # jobj = ultra.JSObject(jobj_ref, js_ctx)

    dummy_refs = []
    while not finalized:
        dummy_refs.append(ultra.JSObjectMake(js_ctx.ref, ultra.NULL, ultra.NULL))
    print('Created', len(dummy_refs), 'dummy objects to force JS GC')

    assert finalized == [jobj_ref]

    # if False:
    #     print('protected:', js_ctx.get_protected_object_count())
    #     print('Wrapping object')
    #     jobj = ultra.JSObject(jobj_ref, js_ctx)
    #     print('protected:', js_ctx.get_protected_object_count())
    #     print('Deleting object')
    #     del jobj
    #     print('protected:', js_ctx.get_protected_object_count())

    print('Deleting class')
    jcls_ref = jcls.ref
    del jcls

    gc.collect()

    # for i in range(6):
    #     print('GC')
    #     js_ctx.garbage_collect()
    #     time.sleep(1)

    print('Done')


def test_JSClass___example(js_ctx):
    do_thing(js_ctx)
