from threading import Thread
import queue
import web
import processor

work_queue = queue.Queue()
web = Thread(target=web.run, args=(work_queue,))
processor = Thread(target=processor.run, args=(work_queue,))

web.start()
processor.start()
