from logic import process


def run(queue):
    while not (task := queue.get()).kill:
        process(task)
