from logic import process


def run(queue):
    print("before loopdy-loop")
    while not (task := queue.get()).kill:
        print("inside loopdy-loop")
        process(task)
