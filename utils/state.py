import asyncio


class State:
    def __init__(self, loop: asyncio.AbstractEventLoop):
        self.loop = loop
        self.tasks = set()
        self.running: bool = False
        self.api_object_holder = None

    def start(self):
        self.running = True
        print('State: Running: ', self.running)

    def stop(self):
        self.running = False
        print('State: Running: ', self.running)

    def callback(self, task: asyncio.Task):
        print('Canceling', task.get_name())
        self.tasks.discard(task)