################################################################################
'''
RUFAS: Ruminant Farm Systems Model
File name: base_report_handler.py
Description:
Author(s): Kass Chupongstimun, kass_c@hotmail.com
'''
################################################################################

from pathlib import Path
from abc import ABC, abstractmethod

#-------------------------------------------------------------------------------
# Abstract Class: BaseReportHandler
#-------------------------------------------------------------------------------
class BaseReportHandler(ABC):
    '''
    Contains an interface for report handlers, each output report
    file implements this abstract class.
    '''

    # Default path for output report files
    path = Path("Outputs/Default_Output_Dir")

    def set_properties(self, data):
        self.active = data['active']
        self.report_name = data['report_name']
        self.fName = data['file_name']

    #---------------------------------------------------------------------------
    # Method: get_fPath
    #---------------------------------------------------------------------------
    def get_fPath(self):
        '''Gets the path to which the report handler will write the report.

        Returns:
            Path: path to which the report will be written.
        '''
        return self.path / self.fName

    #---------------------------------------------------------------------------
    # Method: handle_existing_file
    #---------------------------------------------------------------------------
    def handle_existing_file(self):
        '''Deletes the existing output file of the same name if exists.'''

        if self.get_fPath().exists():
            self.get_fPath().unlink()
            print("Existing {} file detected and deleted".format(self.fName))

    #---------------------------------------------------------------------------
    # Abstract Methods
    #---------------------------------------------------------------------------
    @abstractmethod
    def get_data(self): raise NotImplementedError()
    @abstractmethod
    def daily_update(self): raise NotImplementedError()
    @abstractmethod
    def write_annual_report(self): raise NotImplementedError()
    @abstractmethod
    def annual_flush(self): raise NotImplementedError()