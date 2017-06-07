import threading
from time import clock, sleep
lock1 = threading.Lock()
lock2 = threading.Lock()

def one():
    global lock1
    while True:
        lock1.acquire(blocking=True)
        print(' [ ', end='')
        for i in range(10):
            for j in range(1000): pass
            print('1', end='')
        print(' ] ', end='')
        lock1.release()

def two():
    global lock2
    while True:
        lock2.acquire(blocking=True)
        print('2', end='')
        for j in range(1000): pass
        lock2.release()

t1 = threading.Thread(target=one)
t1.start()

t2 = threading.Thread(target=two)
t2.start()

