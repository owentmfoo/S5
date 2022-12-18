import os
import pathlib
from typing import Union

import pandas as pd
import re
import warnings
import io


class TecplotData:
    """
    Class to represent a Tecplot File
    """

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

    def readfile(self, filename: Union[str, os.PathLike]) -> None:
        """
        Read the file and load populate self.data with the contents.
        Args:
            filename: Path to datafile in Tecplot format.

        Returns:
            None, data from the file is loaded into the instance as the self.data attribute

        Examples:
            TecplotData.readfile("Velocity.dat")
        """
        '''
        This will act as the base class for specific filed (e.g. History, Weather, Motor)
        '''
        if not (isinstance(filename, os.PathLike) or isinstance(filename, str)):
            raise TypeError("filename should either be string or os.PathLike")
        if isinstance(filename, pathlib.Path):
            filename = str(filename)
        self.filename = filename
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
            variable = variable.strip("\"").split("\", \"")

            # try phrase the two optional datum lines
            for x, line in enumerate(f):
                try:
                    repressuretemp = re.match(r"#PAtm\(Pa\) TAtm\(K\)= (.+)", line)
                    pressure_temp = repressuretemp.group(1).split(' ')
                    self.pressure = pressure_temp[0]
                    self.temperature = pressure_temp[1]
                    continue
                except AttributeError:
                    try:
                        self.datum = re.match("#Datums= (.+)", line).group(1).split(' ')
                        # will throw error if there is not match
                        continue
                    except AttributeError:
                        pass

                # phrase the zone title
                try:
                    self.zone = TPHeaderZone(re.match('Zone .+', line).group(0))
                    break
                except AttributeError:
                    raise SyntaxError('Tecplot file  ' + filename + ' missing zone data\n')
        self.data = pd.read_csv(filename, skiprows=x + 3, index_col=False, sep=r'\s+', names=variable)

    def write_tecplot(self, filename, Datum=False) -> None:
        """write the TecplotData to a .dat file
        :param Datum: If DSW datum lines are written, default false
        :param filename: including extension (.dat)
        does not return anything in python

        >>> TecplotData.write_tecplot("Velocity.dat")
        """

        if self.data is None or self.zone is None or self.data.size == 0:
            raise AttributeError(f"No valid data found in export for {filename}")

        self.check_zone()  # raise warning if the zone details doesn't match the data.
        with open(filename, 'w') as f:
            f.write(f'Title = \"{self.title}\"\n')
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
        """update the zone detail such that i = the size of the dataframe in self.data
        >>> TecplotData.update_zone_1d()"""
        self.zone.ni = self.data.shape[0]

    def check_zone(self) -> bool:
        """checks the zone detail matches the dataframe
        :return bool: False if there is zone detail mismatch
        >>> TecplotData.check_zone()"""
        if self.zone.ni * self.zone.nj * self.zone.nk != self.data.shape[0]:
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
    """Class that represents a SolarSim Weather file"""

    def add_timestamp(self, startday: str, day: str = 'Day', time: str = 'Time (HHMM)') -> None:
        """Use the 'Day' and 'Time (HHMM)' columns to create a 'DateTime' column.

        Args:
            startday: First day of the race in the format 'DDMMYYYY'.
            day: Column name for the day column, default 'Day'.
            time: Column name for the time column, default 'Time (HHMM)'.

        Returns:
            None, modifies the self.data and adds a new column named 'DateTime'.

        Examples:
            >>> SSWeather.add_timestamp(startday='13102019')
            >>> SSWeather.add_timestamp(startday='13102019', day = 'Day', time = 'Time (HHMM)')
        """
        startday = pd.to_datetime(startday)
        self.data['DateTime'] = pd.to_datetime(
            self.data[time].astype(int).astype(str).str.pad(4, side='left', fillchar='0'), format='%H%M')
        self.data['DateTime'] = pd.to_datetime(startday.strftime('%Y%m%d') + self.data['DateTime'].dt.strftime('%H%M'))
        self.data['DateTime'] = self.data['DateTime'] + pd.to_timedelta(self.data[day] - 1, unit='D')

    def add_day_time_cols(self):
        """
        Creates the 'Day' and 'Time' columns ina weather file when the dataframe is indexed by datetime.
        """
        # Check if the index is a DateTime index first before using it to create the dat and time columns.
        if not isinstance(self.data.index, pd.DatetimeIndex):
            raise TypeError("Data index should be pd.DateTimeIndex.")
        self.data.loc[:, 'Day'] = self.data.index.day - self.data.index.day[0] + 1  # convert to day of race, 1 indexed
        self.data.loc[:, 'Time (HHMM)'] = self.data.index.strftime("%H%M")

    def check_rectangular(self):
        """Checks if the weather file is a fully rectangular grid in space and time.

        Sometimes measurements are taken at slightly different time at each station.
        For example: 3 minute past the hour at Darwin but 6 minute past the hour at Coober Pedy.
        The means that although there may be the same amount of points at both location, there are double the amount
        of unique DateTime in the file, messing up the j index value in the zone data.
        """
        if self.zone.nj != self.data['Distance (km)'].nunique():
            warnings.warn('Zone data nj (Distance) mismatch.')
        if self.zone.ni != (
                self.data['Time (HHMM)'].astype(str) + self.data['Day'].astype(str)).nunique():
            warnings.warn('Zone data ni (Time) mismatch.')


class SSHistory(TecplotData):
    """Class that represents SolarSim History file"""

    def add_timestamp(self, startday='20191013', datetime_col='DDHHMMSS'):
        """
        DSW SolarSim History file Specific Function
        create a timestamp column in the dataframe if the file have day and time column in the DSWSS format
        :argument startday: first day of the race
        :argument datetime_col: column name for the timestamp
        >>> SSHistory.add_timestamp(startday='13102019')
        """
        self.data.loc[:, 'Day'] = self.data[datetime_col].astype(int).astype(str).str.pad(8, fillchar='0').str[
                                  0:2].astype(int)
        startday = pd.to_datetime(startday)
        self.data.loc[:, 'DateTime'] = pd.to_datetime(
            self.data[datetime_col].astype(int).astype(str).str.pad(8, fillchar='0').str[2:8], format='%H%M%S')
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
            self.zonetitle = str(re.search(r'"(.*)"', zonestr).group(1))
            self.zonetype = str(mtch.group(3))
            self.ni = int(mtch.group(4))
            self.nj = int(mtch.group(5))
            self.nk = int(mtch.group(6))
            self.F = str(mtch.group(8))

            # zone title phrasing often flakey so extra catch here
            assert self.zonetitle is not None, "zone title phrasing failed."
        except SyntaxError:
            raise SyntaxError(f'Bad zone title format: {zonestr}')

    def to_string(self) -> str:
        """    use of exporting in .dat, return the zone line as a str for writing directly into the file.
        :returns: a str complied from the obj attributes as the zone line in the header
        >>> TPHeaderZone.to_string()
        """

        output = f'Zone T = "{self.zonetitle}"'
        output = output + f', I = {int(self.ni)}, J = {int(self.nj)}, K = {int(self.nk)}, F = {self.F}'
        return output

    def __repr__(self):
        return self.to_string()


class DSWinput:
    """class for DSW input file such as LogVolts.in or SolarSim.in
    >>> SScontrol = DSWinput('SolarSim.in')"""

    def __init__(self, filename: str = None):
        self.lines = ['']
        if filename is not None:
            self.filename = filename
            self.readfile(filename)
        else:
            self.filename = None

    def readfile(self, filename: str):
        """Read in the input file
        :param filename: file name of the file to read in
        >>> SScontrol = DSWinput.readfile('SolarSim.in')"""
        with open(filename) as f:
            self.lines = f.readlines()

    def get_value(self, param: str):
        """get the values of the parameter
        :param param: name of the parameter to get the value of
        >>> SScontrol = DSWinput.readfile('SolarSim.in')
        >>> SScontrol.get_value('RoadFile')"""
        for l in self.lines:
            l = l.strip()
            if param in l:
                mtch = re.search(r'(?<==).+', l)
                return mtch.group(0).strip()
        raise ValueError("param not in input file")

    def set_value(self, param: str, value: Union[str, float]):
        """set the value of the parameter
        :param param: name of the parameter to set the value off
        :param value: the value to set the parameter to
        >>> SScontrol = DSWinput.readfile('SolarSim.in')
        >>> SScontrol.set_value('RadoFile','RoadWSC.dat')"""
        value = str(value)
        for i, l in enumerate(self.lines):
            if param in l:
                mtch = re.search(r'(?<==).+', l)
                l = l.replace(mtch.group(0).strip(), value)
                self.lines[i] = l
                return 1
        raise ValueError("param not in input file")

    def write_input(self, filename: str):
        """write input file to a file
        :param filename: the name of the output file
        >>> SScontrol = DSWinput.readfile('SolarSim.in')
        >>> SScontrol.write_input('SolarSim.in')
        """
        with open(filename, "w") as f:
            f.writelines(self.lines)
        return 1

    def format(self, sysformat: str):
        r"""reformat the input file, changing path refrence to either windows (\) or linux(/)
        :param sysformat: system to format to ('lin' , 'win')
        >>> SScontrol = DSWinput.readfile('SolarSim.in')
        >>> SScontrol.format('lin',)
        >>> SScontrol.format('win',)"""
        sysformat = sysformat.lower()
        lines = self.lines
        if sysformat not in ['win', 'dos', 'unix', 'linux', 'lin', 'windows']:
            raise SyntaxError(f"{sysformat} is not a valid format")
        if sysformat in ['win', 'dox', 'windows']:
            for i, line in enumerate(lines):
                lines[i] = line.replace(r"/", r"\\")
        if sysformat in ['unix', 'linux', 'lin']:
            for i, line in enumerate(lines):
                lines[i] = line.replace(r"\\", r"/")
        self.lines = lines


if __name__ == "__main__":  # pragma: no cover
    df = SSHistory(r"E:\solar_car_race_strategy\SolarSim\1.Const-Vel\History_70.0.dat")
