import pandas as pd
import re
import warnings
import io


class TecplotData:
    # TODO: split into tecplot base class and DSW supercalss?
    def __init__(self, filename=None):
        self.title = 'Title'
        self.pressure = 'Pressure'
        self.temperature = 'Temperature'
        self.datum = 'Datum'
        self.zone = TPHeaderZone()
        self.data = pd.DataFrame()
        if filename is not None:
            self.filename = filename
            self.readfile(filename)
        else:
            self.filename = None

    def readfile(self, filename) -> None:
        """populate the class attributes from the file, data is available in self.data as pandas.dataframe
        :param filename: file name of .dat file
        :return: None, data are stored as attributes in the class object.

        >> tvel.readfile("Velocity.dat")
        """
        '''
        ToDo:
        * deal with 3d data
        '''
        self.filename = filename
        with open(filename) as f:
            try:
                self.title = re.match('Title = (.+)', f.readline()).group(1).strip("\"")
            except AttributeError:
                warnings.warn('Tecplot file ' + filename + ' missing title')

            try:
                variable = re.match('Variables = (.+)', f.readline()).group(1)
            except AttributeError:
                warnings.warn('Tecplot file ' + filename + ' missing variable titles')
            try:
                variable = variable.strip("\"").split("\", \"")
            except:
                warnings.warn('Tecplot file  ' + filename + ' variable titles format error')
            for x, line in enumerate(f):

                try:
                    repressuretemp = re.match("#PAtm\(Pa\) TAtm\(K\)= (.+)", line)
                    pressure_temp = repressuretemp.group(1).split(' ')
                    self.pressure = pressure_temp[0]
                    self.temperature = pressure_temp[1]
                except:
                    try:
                        self.datum = re.match("#Datums= (.+)", line).group(1).split(' ')
                        # will throw error if there is not match
                    except:
                        pass

                if not re.match('Zone .+', line) is None:
                    self.zone = TPHeaderZone(re.match('Zone .+', line).group(0))
                    break
            if self.zone is None:
                warnings.warn('Tecplot file  ' + filename + ' missing zone details')
        self.data = pd.read_csv(filename, skiprows=x + 3, index_col=False, sep='\s+', names=variable)

    def to_multiindex(self, remove_originalcols=False, filename=None) -> None:
        """reindex to multi index by identifying the I and J columns
        :param remove_originalcols: False by default, remove the columns that have been used as index, but may make writing back to .dat more difficult
        :return: 
        """
        # TODO: is this really the best way to deal with 3d data?
        if self.zone.nj == 1:
            print(f'j=1, multiindex not supported.')
        else:
            # identify di-axis
            icol = self.data.loc[:, self.data.nunique() == int(self.zone.ni)].columns
            if len(icol) == 0:
                warnings.warn(
                    f"Warning in reading {filename}.\nZone data and data mismatch, no column with {self.zone.ni} unique items. I-axis not found.")
            elif len(icol) != 1:
                warnings.warn(
                    f"Warning in reading {filename}.\nMultiple variables can be the di-axis, choosing {icol[0]} as the I-axis.")
                icol = icol[0]
            jcol = self.data.loc[:, self.data.nunique() == int(self.zone.nj)].columns
            jcol = jcol.difference(icol)
            if len(jcol) == 0:
                warnings.warn(
                    f"Warning in reading {filename}.\nZone data and data mismatch, no column with {self.zone.ni} unique items. J-axis not found.")
            elif len(jcol) != 1:
                warnings.warn(
                    f"Warning in reading {filename}.\nMultiple variables can be the di-axis, choosing {icol[0]} as the J-axis.")

            assert not icol.equals(
                jcol), f"Error in reading 3d data from {filename}, failed to identify unique di,j-axis"
            index = pd.MultiIndex.from_frame(self.data.loc[:, icol.append(jcol)])
            self.data.set_index(index, inplace=True)
            # left the 2 axis in the dataframe in place as well to have options, but should really use the index
            if remove_originalcols:
                self.data.pop(icol.append(jcol))

    def write_tecplot(self, filename,Datum = False) -> None:
        """write the tecploptdata to a .dat file
        :param filename: including extension (.dat)
        does not return anything in python

        >> tvel.write_tecplot("Velocity.dat")
        """

        if self.data is None or self.zone is None:
            warnings.warn("data incomplete, try again")
            return False
        with open(filename, 'w') as f:
            try:
                f.write(f'Title = \"{self.title}\"\n')
            except:
                warnings.warn("data incomplete, try again")
            varstr = str(self.data.columns.to_list()).strip("[]").replace("\'", "\"")
            f.write(f'Variables = {varstr}\n')
            if Datum:
                try:
                    f.write(f'# PAtm(Pa) TAtm(K)= {self.pressure} {self.temperature}\n')
                except:
                    pass
                try:
                    f.write(f'#Datums= {self.datum}\n')
                except:
                    pass
            f.write(f'{self.zone.to_string()}\n')  # need fix
            self.data.to_string(f, header=False, index=False, col_space=6)
            f.flush()

    def __repr__(self):
        buf = io.StringIO()
        buf.write(f"{self.title}\n")
        buf.write(f"{self.zone.__repr__()}\n")
        buf.write(self.data.__repr__())
        return buf.getvalue()

# deal with 3d data?
class SSWeather(TecplotData):
    def addtimestamp(self, startday='19990716',day='Day', time='Time (HHMM)'):
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
    def add_timestamp(self, startday = '20191013'):
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


class TPHeaderZone:
    """class for Tecplot zone details in the file header, inc the while line while init and details will be populated
    by regex as object attributes

    >>> TPHeaderZone('Zone T = "", I = 1, J = 1, K = 1, F = POINT')
    This line is also the default input if no string is inputed and the attributed can be changed later.
    """

    def __init__(self, zonestr='Zone T = " ", I = 1, J = 1, K = 1, F = POINT'):
        # Zone T = "Start Date & Time yyyymmdd hh mm ss 20210429 17 6 0", I=1979, J=1, K=1, F=POINT
        zonematch = re.compile('ZoneT="(.*)"(,ZONETYPE=(.*))?,I=(.+),J=(.+),K=(.+),(F=(.+))?')
        mtch = zonematch.match(zonestr.replace(" ", ""))
        self.zonetitle = str(mtch.group(1))
        self.zonetype = str(mtch.group(3))
        self.ni = int(mtch.group(4))
        self.nj = int(mtch.group(5))
        self.nk = int(mtch.group(6))
        self.F = str(mtch.group(8))
        if self.zonetitle == '':
            self.zonetitle = ' '

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
    def readfile(self,filename):
        with open(filename) as f:
            self.lines = f.readlines()
    def get_value(self,param):
        for l in self.lines:
            if param in l:
                mtch = re.match(".*=\s*(\S*)\s*", l)
                return mtch.group(1)
            else:
                raise ValueError("param not in input file")
    def set_value(self,param,value):
        """set the value of the parameter"""
        for i,l in enumerate(self.lines):
            if param in l:
                mtch = re.match(".*=\s*(\S*)\s*", l)
                l.replace(mtch(1),value)
                self.lines[i] = l
                return 1
            else:
                raise ValueError("param not in input file")
    def write_input(self,filename):
        with open(filename,"w") as f:
            f.writelines(self.lines)
        return 1
