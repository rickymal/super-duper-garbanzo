from abc import ABC, abstractmethod
import asyncio
from concurrent.futures import ThreadPoolExecutor
import time
from utils import hook_status_in_context
from context import TestContext


class IExecutable(ABC):

    @abstractmethod
    def execute(self, context = None, event_loop = None, thread_pool_executor = None,):
        pass




# Classe Container # event_loop_executor = asyncio.new_event_loop(), thread_pool_executor = ThreadPoolExecutor(max_workers=10, thread_name_prefix="pipe")
class Container(IExecutable):
    def __init__(self, name : str, output,):
        
        self.futures = []
        self.output = output
        self.actual_context = TestContext(output)

        self.name = name
        # self.subcontainers: list[IExecutable] = []
        self.pipelines = []
        self.hooks_before_each: list[Step] = []
        self.hooks_after_each: list[Step] = []
        self.fixtures = {}
        self.factories = {}
        self.steps: list[IExecutable] = []
        self.annotations = {}
        self.tags = []
        self.parent = None
        self.output = output
        self.actual_context = TestContext(self.output)

    def it(self, description):
        def decorator(step):
            self.steps.append((description, step))

        return decorator

    def add_step(self, description: str, func, isolated: bool, **kwargs):
        step = Step(description, func, isolated, **kwargs)
        self.steps.append(step)

    def wait_ctx(self, ctx: TestContext, time_sleep: int = 1, timeout: int = 10, event_loop = None, thread_pool_executor = None,):
        future = event_loop.run_in_executor(thread_pool_executor, lambda: time.sleep(timeout))
        event_loop.run_until_complete(future)
        while ctx.status == 'pending' and not future.done():
            time.sleep(time_sleep)

    def wait_future(self, func_execution: asyncio.Future, time_sleep: int = 1, timeout: int = 10):
        future = self.event_loop.run_in_executor(self.thread_pool_executor, lambda: time.sleep(timeout))
        self.event_loop.run_until_complete(future)
        while not func_execution.done() and not future.done():
            time.sleep(time_sleep)

    def create_container(self, name: str):
        new_container = Container(name = name, output= self.output)
        self.steps.append(new_container)
        return new_container

    def before(self, func, isolated: bool):
        step = Step("before", func, isolated=isolated)
        self.hooks_before_each.append(step)

    def after(self, func, isolated: bool):
            step = Step("before", func, isolated=isolated)
            self.hooks_after_each.append(step)
            

    def execute(self, context = None, event_loop = None, thread_pool_executor = None,):
        self.output.start_test_instance(self)
        future = asyncio.Future()
        ctx_hk_before, ctx_hk_after, ctx_step, ctx_all = self.get_status_builder()
        
        self._run_sequence(context, event_loop, thread_pool_executor, ctx_hk_before, self.hooks_before_each, 'before')

        self._run_sequence(context, event_loop, thread_pool_executor, ctx_step, self.steps, 'middle')

        self._run_sequence(context, event_loop, thread_pool_executor, ctx_hk_after, self.hooks_after_each, 'end')

        future.set_result(ctx_all)

        context.approve()
        self.output.end_test_instance(self)

        return future

    def _run_sequence(self, context, event_loop, thread_pool_executor, ctx_hk_before, iterable, status_progress: str):
        ctx_hk_before['status'] = 'pending'
        futures_list: list[asyncio.Future] = []
        for hook in iterable:
            status = {'status': 'not initialized'}
            hook_status_in_context(context, status)
            # context.on_approved = lambda : status.update({'status': 'approved'})
            # context.on_rejected = lambda : status.update({'status': 'rejected'})
            # context.on_concluded = lambda : status.update({'status': 'concluded'})
            # context.on_status_checked = lambda : status['status']
            status.update({'status': 'pending'})
            ctx_hk_before['values'].append(status)
            future = hook.execute(context = context, event_loop = event_loop, thread_pool_executor=thread_pool_executor)
            futures_list.append(future)
            if not future.done():
                self.wait_ctx(context, time_sleep= 1, timeout= 10, event_loop = event_loop, thread_pool_executor = thread_pool_executor) # and self.wait_future(future)
            
            if context.get_status() != "approved":
                ctx_hk_before['status'] = 'error'
                raise Exception("Error")
        ctx_hk_before['status'] = 'concluded'

        if not all(ctx['status'] == 'approved' for ctx in ctx_hk_before['values']):
            raise Exception("Opa meu patrão")


    
    def __str__(self) -> str:
        return "Container: {}".format(self.name)
    
    def __repr__(self) -> str:
        return self.__str__()
    
    def get_status_builder(self):
        before_hook_statuses = {
            'status': 'not initialized',
            'values': []
        }

        after_hook_statuses = {
            'status': 'not initialized',
            'values': []
        }

        step_hook_statuses = {
            'status': 'not initialized',
            'values': []
        }

        all_pipeline_status = {
            'hook': {
                'before': before_hook_statuses,
                'after': after_hook_statuses,
            },
            'step': step_hook_statuses
        }

        return before_hook_statuses, after_hook_statuses, step_hook_statuses, all_pipeline_status

    def add_fixture(self, key, value):
        self.fixtures[key] = value

    def get_fixture(self, key, default=None):
        if key in self.fixtures:
            return self.fixtures[key]
        elif self.parent:
            return self.parent.get_fixture(key, default)
        else:
            return default

    def add_factory(self, name, factory_func, alucinator=None):
        self.factories[name] = {'func': factory_func, 'alucinator': alucinator}

    def get_factory(self, name):
        if name in self.factories:
            return self.factories[name]
        elif self.parent:
            return self.parent.get_factory(name)
        else:
            return None

# Classe Step
class Step(IExecutable):
    def __init__(self, description: str, func, isolated: bool, **kwargs):
        self.description = description
        self.func = func
        self.kwargs = kwargs
        self.isolated = isolated


    def __repr__(self) -> str:
        return "step: {}".format(self.description)

    def execute(self, context: TestContext, event_loop: asyncio.BaseEventLoop = None,  thread_pool_executor: ThreadPoolExecutor = None) -> asyncio.Future:
        context.output.start_step(self)
        future_result = asyncio.Future()
        context.step_description = self.description
        if self.isolated:
            thread_pool_executor = thread_pool_executor.submit(self.func, context)
        else:
            if context is None:
                print("OI")
            rr = self.func(context,)
            future_result.set_result(rr)
        status = "PASSED" if context.status == 'approved' else "FAILED"
        context.output.end_step(self, status)
        if future_result is None:
            pass
        return future_result

