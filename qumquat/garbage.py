from .qvars import *

class Garbage:

    ################### Garbage

    # https://python-3-patterns-idioms-test.readthedocs.io/en/latest/PythonDecorators.html
    # What a mess: a class that can be both a with wrapper and a decorator,
    # and the decorator supports arguments AND no arguments

    def garbage(self, *keys):
        if len(keys) == 0:
            key = "keyless"
        else:
            key = keys[0]
            if key == "keyless":
                raise SyntaxError("'keyless' is a reserved garbage pile key.")

        class WrapGarbage():
            def enter(s):
                self.garbage_stack.append(key)
                if key == "keyless":
                    self.garbage_piles["keyless"].append([])
                else:

                    if key not in self.garbage_piles:
                        self.garbage_piles[key] = []

                self.queue_stack.append([])

            def exit(s):
                queue = self.queue_stack.pop()

                if key == "keyless":
                    pile = self.garbage_piles["keyless"].pop()
                else:
                    pile = self.garbage_piles[key]

                self.garbage_stack.pop()
                self.do_garbage(queue, pile, key)

            def __call__(s, f):
                def wrapped(*args):
                    s.enter()
                    out = f(*args)
                    s.exit()
                    return out

                return wrapped

            def __enter__(s): s.enter()

            def __exit__(s, *args): s.exit()


        return WrapGarbage()


    def do_garbage(self, queue, pile, key):
        if self.queue_action("do_garbage", queue, pile, key): return

        self.pile_stack.append(pile)

        for tup in queue: self.call(tup)

        if key=="keyless" and len(pile) > 0:
            raise SyntaxError("Keyless garbage pile terminated non-empty.")

        self.pile_stack.pop()


    def do_garbage_inv(self, queue, pile, key):
        if self.queue_action("do_garbage_inv", queue, pile, key): return

        self.queue_stack.append([]) # just reverse the queue
        for tup in queue[::-1]: self.call(tup, invert=True)
        rev_queue = self.queue_stack.pop()

        self.do_garbage(rev_queue, pile, key)

    def assert_pile_clean(self, key):
        if self.queue_action("assert_pile_clean", key): return
        if key not in self.garbage_piles: return
        if len(self.garbage_piles[key]) == 0: return
        raise ValueError("Garbage pile '"+key+"' is not clean.")

    def assert_pile_clean_inv(self, key):
        if self.queue_action("assert_pile_clean_inv", key): return
        self.assert_pile_clean(key)
