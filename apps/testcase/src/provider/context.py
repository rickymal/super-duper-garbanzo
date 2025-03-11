class PrototypeInstance:
    pass


# Classe Context
class TestContext(PrototypeInstance):
    def __init__(self, output):
        self.data = {}
        self.errors = []
        self.container = None
        self.alucinator = None
        self.output = output
        self.status = 'not initialized'
        self.forward_ctx = None
        self.backward_ctx = None
        self.on_approved = None
        self.on_rejected = None
        self.on_concluded = None
        self.on_status_checked = None

    def set(self, key, value):
        self.data[key] = value


    def get_status(self):
        return self.on_status_checked()

    def get(self, key, default=None):
        value = self.data.get(key, default)
        if value is None and self.backward_ctx is not None:
            value = self.backward_ctx.get(key, value)    
        return value

    def approve(self):
        self.on_approved()

    def reject(self, error_message: str):
        self.on_rejected()
        self.errors.append(error_message)

    def conclude(self):
        self.on_concluded()


    def chain_new_context(self, status = 'not initialized', ctx: 'TestContext' = None):
        new_ctx = TestContext(self.output) if ctx is None else ctx
        self.forward_ctx = new_ctx
        new_ctx.container = self.container
        new_ctx.status = status
        new_ctx.backward_ctx = self
        return new_ctx


    def get_status(self):
        return self.on_status_checked()

    

    def iter_ctx(self):
        ctx = self
        while ctx:
            yield ctx
            ctx = ctx.forward_ctx

    def iter_items(self):
        for ctx in self.iter_ctx():
            yield from ctx.data.items()


class SchemaContext(TestContext):

    def __init__(self, output, field):
        super().__init__(output)
        self.field = field
    pass
