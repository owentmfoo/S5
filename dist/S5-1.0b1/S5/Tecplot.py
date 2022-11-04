import pathlib

import pandas as pd
import re
import warnings
import io
import pytest


class TecplotData:
    def __init__(self, filename=None):
        self.title = 'Title'
        self.pressure = 0
        self.temperature = 0
        self.datum = ['Datum']
        self.zone = TPHeaderZone()
        self.data = pd.DataFrame()
        if filename is not None:
            self.filename = filename
            self.readfile(filename)
        else:
            self.filename = None

    def readfile(self, filename) -> None:
        """populate the class attributes from the file, data is available in self.data as pandas.dataframe
        :param filename: file name of .dat file or pathlib.Path object of equivalent
        :return: None, data are stored as attributes in the class object.

        >> tvel.readfile("Velocity.dat")
        """
        '''
        This will act as the base class for specific filed (e.g. History, Weather, Motor)
        '''
        if not (isinstance(filename,pathlib.Path) or isinstance(filename,str)):
            raise TypeError("filename should either be string or pathlib.Path")
        if isinstance(filename,pathlib.Path):
            filename = str(filename)
        self.filename =filename
        with open(filename) as f:
            # phrase title
            try:
                self.title = re.match('Title = (.+)', f.readline()).group(1).strip("\"")
            except AttributeError as err:
                raise SyntaxError('Tecplot file ' + filename + ' missing title\n')

            # phrase variable title
            try:
                variable = re.match('Variables = (.+)', f.readline()).group(1)
            except AttributeError as err:
                raise SyntaxError('Tecplot file ' + filename + ' missing variable titles\n')
            try:
                variable = variable.strip("\"").split("\", \"")
            except Exception as err:
                raise SyntaxError('Tecplot file  ' + filename + ' variable titles format error\n')

            # try phrase the two optional datum lines
            for x, line in enumerate(f):
                try:
                    repressuretemp = re.match(r"#PAtm\(Pa\) TAtm\(K\)= (.+)", line)
                    pressure_temp = repressuretemp.group(1).split(' ')
                    self.pressure = pressure_temp[0]
                    self.temperature = pressure_temp[1]
                    continue
                except:
                    try:
                        self.datum = re.match("#Datums= (.+)", line).group(1).split(' ')
                        # will throw error if there is not match
                        continue
                    except:
                        pass

                # phrase the zone title
                try:
                    self.zone = TPHeaderZone(re.match('Zone .+', line).group(0))
                    break
                except AttributeError:
                    raise SyntaxError('Tecplot file  ' + filename + ' missing zone data\n')
            if self.zone is None:
                warnings.warn('Tecplot file  ' + filename + ' missing zone details')
        self.data = pd.read_csv(filename, skiprows=x + 3, index_col=False, sep=r'\s+', names=variable)


    def write_tecplot(self, filename, Datum=False) -> None:
        """write the tecploptdata to a .dat file
        :param filename: including extension (.dat)
        does not return anything in python

        >> tvel.write_tecplot("Velocity.dat")
        """

        if self.data is None or self.zone is None:
            warnings.warn("data incomplete, try again")
            return False

        self.check_zone()  # raise warning if the zone details doesn't match the data.
        with open(filename, 'w') as f:
            try:
                f.write(f'Title = \"{self.title}\"\n')
            except:
                warnings.warn("data incomplete, try again")
            varstr = str(self.data.columns.to_list()).strip("[]").replace("\'", "\"")
            f.write(f'Variables = {varstr}\n')
            if Datum:
                # may raise Attribute error of the attributes are not present, they all have default values
                f.write(f'#PAtm(Pa) TAtm(K)= {self.pressure} {self.temperature}\n')
                f.write(f'#Datums= {" ".join(self.datum)}\n')


            f.write(f'{self.zone.to_string()}\n')  # need fix
            self.data.to_string(f, header=False, index=False, col_space=6)
            f.flush()

    def update_zone_1d(self):
        """update the zone detail such that i= the size of the dataframe"""
        self.zone.ni = self.data.shape[0]

    def check_zone(self) -> bool:
        """checks the zone detail matches the dataframe
        :return False if there is zone detail mismatch"""
        if (self.zone.ni * self.zone.nj * self.zone.nk != self.data.shape[0]):
            warnings.warn("Zone detail mismatch")
            return False
        return True

    def __repr__(self):
        buf = io.StringIO()
        buf.write(f"{self.title}\n")
        buf.write(f"{self.zone.__repr__()}\n")
        buf.write(self.data.__repr__())
        return buf.getvalue()


# deal with 3d data?
class SSWeather(TecplotData):
    def addtimestamp(self, startday='19990716', day='Day', time='Time (HHMM)'):
        """
        DSW SolarSim Weather file Specific Function
        create a timestamp column in the dataframe if the file have day and time column in the DSWSS format
        :argument day: column name for the day column
        :argument time: column name for the time column
        :argument startday: first day of the race
        """
        startday = pd.to_datetime(startday)
        self.data['DateTime'] = pd.to_datetime(
            self.data['Time (HHMM)'].astype(int).astype(str).str.pad(4, side='left', fillchar='0'), format='%H%M')
        self.data['DateTime'] = pd.to_datetime(startday.strftime('%Y%m%d') + self.data['DateTime'].dt.strftime('%H%M'))
        self.data['DateTime'] = self.data['DateTime'] + pd.to_timedelta(self.data['Day'] - 1, unit='D')


class SSHistory(TecplotData):

    def add_timestamp(self, startday='20191013'):
        """
        DSW SolarSim History file Specific Function
        create a timestamp column in the dataframe if the file have day and time column in the DSWSS format
        :argument startday: first day of the race
        """
        self.data.loc[:, 'Day'] = self.data['DDHHMMSS'].astype(int).astype(str).str.pad(8, fillchar='0').str[
                                  0:2].astype(int)
        startday = pd.to_datetime(startday)
        self.data.loc[:, 'DateTime'] = pd.to_datetime(
            self.data['DDHHMMSS'].astype(int).astype(str).str.pad(8, fillchar='0').str[2:8], format='%H%M%S')
        self.data.loc[:, 'DateTime'] = pd.to_datetime(
            startday.strftime('%Y%m%d') + self.data['DateTime'].dt.strftime('%H%M%S'))
        self.data.loc[:, 'DateTime'] = self.data['DateTime'] + pd.to_timedelta(self.data['Day'] - 1, unit='D')

    def summary(self):
        """return a named tuple of summary"""
        """DoD to be determined"""
        raise SyntaxError("To be implemented")


class TPHeaderZone:
    """class for Tecplot zone details in the file header, inc the while line while init and details will be populated
    by regex as object attributes

    >>> TPHeaderZone('Zone T = "", I = 1, J = 1, K = 1, F = POINT')
    This line is also the default input if no string is inputed and the attributed can be changed later.
    """

    def __init__(self, zonestr='Zone T = " ", I = 1, J = 1, K = 1, F = POINT'):
        # Zone T = "Start Date & Time yyyymmdd hh mm ss 20210429 17 6 0", I=1979, J=1, K=1, F=POINT
        try:
            zonematch = re.compile('ZoneT="(.*)"(,ZONETYPE=(.*))?,I=(.+),J=(.+),K=(.+),(F=(.+))?')
            mtch = zonematch.match(zonestr.replace(" ", ""))
            self.zonetitle = str(re.search(r'"(.*)"',zonestr).group(1))
            self.zonetype = str(mtch.group(3))
            self.ni = int(mtch.group(4))
            self.nj = int(mtch.group(5))
            self.nk = int(mtch.group(6))
            self.F = str(mtch.group(8))

            # zone title phrasing often flakey so extra catch here
            assert self.zonetitle is not None, "zone title phrasing failed."
        except AttributeError:
            raise SyntaxError(f'Bad zone title format: {zonestr}')
    def to_string(self) -> str:
        '''    use of exporting in .dat, return the zone line as a str for writing directly into the file.
        :return: a str complied from the obj attributes as the zone line in the header
        '''

        output = f'Zone T = "{self.zonetitle}"'
        output = output + f', I = {int(self.ni)}, J = {int(self.nj)}, K = {int(self.nk)}, F = {self.F}'
        return output

    def __repr__(self):
        return self.to_string()


class DSWinput:
    """class for DSW input file such as LogVolts.in or SolarSim.in"""

    def __init__(self, filename=None):
        self.lines = ''
        if filename is not None:
            self.filename = filename
            self.readfile(filename)
        else:
            self.filename = None

    def readfile(self, filename):
        with open(filename) as f:
            self.lines = f.readlines()

    def get_value(self, param):
        for l in self.lines:
            if param in l:
                mtch = re.match(r".*=\s*(\S*)\s*", l)
                return mtch.group(1)
            else:
                raise ValueError("param not in input file")

    def set_value(self, param, value):
        """set the value of the parameter"""
        for i, l in enumerate(self.lines):
            if param in l:
                mtch = re.match(r".*=\s*(\S*)\s*", l)
                l.replace(mtch(1), value)
                self.lines[i] = l
                return 1
            else:
                raise ValueError("param not in input file")

    def write_input(self, filename):
        with open(filename, "w") as f:
            f.writelines(self.lines)
        return 1




if __name__ == "__main__":
    df = SSHistory(r"E:\solar_car_race_strategy\SolarSim\1.Const-Vel\History_70.0.dat")
    df.to_ATLAS(filename=r'E:\solar_car_race_strategy\S5\ExampleDataSource\ConstV70.s5')
