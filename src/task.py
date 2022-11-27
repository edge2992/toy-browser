import threading
from typing import List


class Task:
    def __init__(self, task_code, *args):
        self.task_code = task_code
        self.args = args
        self.__name__ = "task"

    def run(self):
        if self.task_code is not None:
            self.task_code(*self.args)
            self.task_code = None
            self.args = None
        else:
            raise Exception("Task already run")


class TaskRunner:
    def __init__(self):
        self.tasks: List[Task] = []
        self.condition = threading.Condition()

    def schedule_task(self, task: Task):
        self.condition.acquire(blocking=True)
        self.tasks.append(task)
        self.condition.release()

    def run(self):
        self.condition.acquire(blocking=True)
        task = None
        if len(self.tasks) > 0:
            task = self.tasks.pop(0)
        self.condition.release()
        if task:
            task.run()

        self.condition.acquire(blocking=True)
        if len(self.tasks) == 0:
            pass
            # self.condition.wait()
        self.condition.release()
