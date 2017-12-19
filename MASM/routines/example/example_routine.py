
from MASM.outputs import OutputHandler
from MASM.classes import State
from .classes import This, That

def example_daily_routine(state:State, output:OutputHandler):
    
    this = This()
    that = That()
    
    this.do_this()
    that.do_that()
    
def example_monthly_routine(state:State, output:OutputHandler):

    pass
    