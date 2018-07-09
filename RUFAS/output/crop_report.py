from RUFAS.output.report_handler import BaseReportHandler

class CropReport(BaseReportHandler):

    def __init__(self, data):

        #
        # Sets active, report_name, f_name using data
        #
        self.set_properties(data)

        #
        # Daily Outputs
        # 1D Lists [julianDay]
        #

        self.daily_fr_PHU = [None]*366
        self.daily_biomass_actual = [None] * 366
        self.daily_LAI_actual = [None] * 366
        self.daily_bio_N = [None] * 366
        self.daily_bio_P = [None] * 366
        self.daily_z_root = [None] * 366
        self.daily_Et_actual = [None] * 366
        self.daily_yield_actual = [None] * 366

        #
        # Yearly Outputs
        # 1D Lists [julianDay]
        #

        #
        # Makes a csv header from the variable names of the daily outputs
        #
        def make_header():
            variables = vars(self)
            header_parts = []
            for variable in variables:
                if variable[0:6] == "daily_":
                    header_parts.append(variable[6:])
            header_parts.sort()
            return "Day," + ",".join(header_parts) + "\n"

        #
        # static
        #
        self.csvHeader = make_header()




    # ---------------------------------------------------------------------------
    # Method: initialize
    # ---------------------------------------------------------------------------
    def initialize(self, state):
        '''Transfers the needed data from state object to the report handler.'''
        d = 0

        cropType = state.crop.crops_list["corn"]
        # Copy daily output values here
        self.daily_fr_PHU[d] = cropType.fr_PHU
        self.daily_biomass_actual[d] = cropType.biomass_actual
        self.daily_LAI_actual[d] = cropType.LAI_actual
        self.daily_bio_N[d] = cropType.bio_N
        self.daily_bio_P[d] = cropType.bio_P
        self.daily_z_root[d] = cropType.z_root
        self.daily_Et_actual[d] = cropType.Et_actual
        self.daily_yield_actual[d] = cropType.yield_actual

    # ---------------------------------------------------------------------------
    # Method: daily_update
    # ---------------------------------------------------------------------------
    def daily_update(self, state, weather, time):
        '''Stores the daily values that need to be printed in the report.'''

        d = time.day
        cropType = state.crop.crops_list["corn"]
        # Copy daily output values here
        self.daily_fr_PHU[d] = cropType.fr_PHU
        self.daily_biomass_actual[d] = cropType.biomass_actual
        self.daily_LAI_actual[d] = cropType.LAI_actual
        self.daily_bio_N[d] = cropType.bio_N
        self.daily_bio_P[d] = cropType.bio_P
        self.daily_z_root[d] = cropType.z_root
        self.daily_Et_actual[d] = cropType.Et_actual
        self.daily_yield_actual[d] = cropType.yield_actual

    # ---------------------------------------------------------------------------
    # Method: annual_update
    # ---------------------------------------------------------------------------
    def annual_update(self, state, weather, time):
        '''Stores the yearly values that need to be printed in the report.'''
        pass

    # ---------------------------------------------------------------------------
    # Method: write_annual_report
    # ---------------------------------------------------------------------------
    def write_annual_report(self, y):
        '''Appends the annual report to the output file.'''

        mode = 'a+' if self.get_fPath().exists() else 'w+'

        dailyData = list(zip(
            self.daily_Et_actual,
            self.daily_LAI_actual,
            self.daily_bio_N,
            self.daily_bio_P,
            self.daily_biomass_actual,
            self.daily_fr_PHU,
            self.daily_yield_actual,
            self.daily_z_root
        ))

        with self.get_fPath().open(mode) as f:
            # Write year header here
            if mode == "w+":
                f.write(self.csvHeader)
            for d in range(366):
                data = [str(x) for x in dailyData[d]]
                line = str(d) + "," + ",".join(data) + "\n"
                f.write(line)



    # ---------------------------------------------------------------------------
    # Method: annual_flush
    # ---------------------------------------------------------------------------
    def annual_flush(self):
        '''Sets all of the values in the output object to the default value.'''

        self.sample_daily_output_1 = [None] * 366
        self.sample_daily_output_2 = [None] * 366

        self.average_val = None
