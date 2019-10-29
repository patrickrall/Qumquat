from .qvars import *

# control.py
#  - inv

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

    def control(self, expr):
        expr = Expression(expr, self)
        class WrapIf():
            def __enter__(s):
                self.push_mode("control")
                self.do_control(expr)

            def __exit__(s, *args):
                self.pop_mode("control")
                self.do_control_inv(expr)

        return WrapIf()

    def do_control(self, expr):
        if self.queue_action("do_control", expr): return
        self.controls.append(expr)

    def do_control_inv(self, expr):
        if self.queue_action("do_control_inv", expr): return
        self.controls.pop()

