# Instance Initialized once per simulation
class Test():

    def __init__(self):
        self.this = This()
        self.that = That()
        
    def annual_reset(self):
        pass
    
# Whatever class your routines need
class This():

    def __init__(self):
        self.this_parameter = "this is something from class: This"
        self.increase_one_per_day = 0
        self.increase_one_per_month = 0
        self.increase_one_per_year = 0

    def do_this(self):
        pass

class That():

    def __init__(self):
        self.that_parameter = "this is something from class: That"

    def do_that(self):
        pass
