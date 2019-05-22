from .qvars import *

class Garbage:

    ################### Garbage

    # a decorator that makes function into a with statement
    def garbage(self, f):

        class WrapGarbage():
            def __init__(s, *args, **kwargs):
                s.args = args
                s.kwargs = kwargs

            def __enter__(s):
                self.queue_stack.append([])
                self.pile_stack_py.append([])

                out = f(*s.args, **s.kwargs)

                s.pile = self.pile_stack_py.pop()

                return out

            def __exit__(s, ty,val,tr): # ignore exception stuff
                self.pile_stack_py.append(s.pile)

                with self.inv(): f(*s.args, **s.kwargs)

                pile = self.pile_stack_py.pop()

                queue = self.queue_stack.pop()

                self.do_garbage(queue, pile)


        def wrapper(*args,**kwargs):
            return WrapGarbage(*args,**kwargs)

        return wrapper

    def do_garbage(self, queue, pile):
        if self.queue_action("do_garbage", queue, pile): return

        self.pile_stack_qq.append(pile)

        for tup in queue: self.call(tup)
        newpile = self.pile_stack_qq.pop()

        #if key=="keyless" and len(pile) > 0:
        if len(newpile) > 0:
            raise SyntaxError("Garbage collector error: pile was not clean after uncomputation.")


    def do_garbage_inv(self, queue, pile):
        if self.queue_action("do_garbage_inv", queue, pile): return

        self.queue_stack.append([]) # just reverse the queue
        for tup in queue[::-1]: self.call(tup, invert=True)
        rev_queue = self.queue_stack.pop()

        # also reverse the pile
        pile = pile[::-1]

        # self.do_garbage(rev_queue, pile, key)
        self.do_garbage(rev_queue, pile)
