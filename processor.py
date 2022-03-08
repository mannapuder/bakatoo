from logic import process


def run(queue):
    print("before loopty-loop")
    while not (task := queue.get()).kill:
        print("inside loopty-loop")
        process(task)
