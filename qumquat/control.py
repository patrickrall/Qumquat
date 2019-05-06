from .qvars import *

# control.py
#  - inv
#  - q_if
#  - q_while
#  - garbage, assert_pile_clean

class Control:
     ######################## Invert

    def inv(self):
        class WrapInv():
            def __enter__(s):
                self.push_mode("inv")
                self.queue_stack.append([])

            def __exit__(s, *args):
                self.pop_mode("inv")

                queue = self.queue_stack.pop()
                for tup in queue[::-1]:
                    self.call(tup, invert=True)

        return WrapInv()

    ################### If

    def q_if(self, expr):
        expr = Expression(expr, self)
        class WrapIf():
            def __enter__(s):
                self.do_if(expr)

            def __exit__(s, *args):
                self.do_if_inv(expr)

        return WrapIf()

    def do_if(self, expr):
        if self.queue_action("do_if", expr): return
        self.controls.append(expr)

    def do_if_inv(self, expr):
        if self.queue_action("do_if_inv", expr): return
        self.controls.pop()

    ################### While

    def q_while(self, expr, key):
        expr = Expression(expr, self)
        class WrapWhile():
            def __enter__(s):
                self.queue_stack.append([])

            def __exit__(s, *args):
                queue = self.queue_stack.pop()
                self.do_while(queue, expr, key)

        return WrapWhile()

    def do_while(self, queue, expr, key):
        if self.queue_action("do_while", queue, expr, key): return
        self.assert_mutable(key)

        for branch in self.controlled_branches():
            if branch[key.index()] != 0: raise ValueError("While loop variable must be initialized to 0.")
        if key.key in expr.keys: raise SyntaxError("While loop expression cannot depend on loop variable.")

        count = 0
        while True:
            # check if all branches are done
            if all([expr.c(b) == 0 for b in self.controlled_branches()]): break

            with self.q_if(expr): key += 1

            with self.q_if(key > count):
                for tup in queue: self.call(tup)

            count += 1


    def do_while_inv(self, queue, expr, key):
        if self.queue_action("do_while_inv", queue, expr, key): return
        self.assert_mutable(key)

        if key.key in expr.keys: raise SyntaxError("While loop expression cannot depend on loop variable.")

        # initial count is maximum value of key
        count = max([b[key.index()] for b in self.controlled_branches()])

        # loop only depends on value of key
        while True:
            if count == 0: break

            count -= 1

            with self.q_if(key > count):
                for tup in queue[::-1]: self.call(tup, invert=True)

            with self.q_if(expr): key -= 1


