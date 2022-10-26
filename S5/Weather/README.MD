# S5.Weahter
<p> Subpackage to create weather input files for SolarSim</p>

##readgrib
convert grib files from [era5_land](https://confluence.ecmwf.int/display/CKB/How+to+download+ERA5) (and [Met Office Weather Datahub](https://metoffice.apiconnect.ibmcloud.com/metoffice/production/) in the future)</p>
<p>requires extra package:</p>
<li>xarray </li>
<li>cfgrib </li>
<li> ecCodes</li>

###usage
`from_era5(stationfile, gribfile, start_date, end_date, outfile, Solar)` 

stationfile: file path to .dat file with station details.\
gribfile: file path to grib file to be used\
start_date: datetime object with timezone specified\
end_date: datetime object with timezone specified\
outfile: file path and name to create output file\
Solar: bool, default Ture. False to disable irradiance output (all 0)\
return: None, weather file will be created and stored at location specified by outfile


>`tz = pytz.timezone('Australia/Darwin')`\
`start_date = datetime.datetime(2020, 9, 14, 8, 0, tzinfo=tz)`\
`end_date = datetime.datetime(2020, 9, 15, 23, 0, tzinfo=tz)`
>
>`from_era5('Weather/Station.dat', 'ExampleDataSource/ERA5-Land-test.grib', start_date, end_date,"Weather-era5.dat", Solar=False)`

##multisource
compile a single weather file from multiple datasource for different parameters. 
Calls function in `Atm.py` and `Solar.py` to import relevant data. 

##SolCastHistoric

Requires the CSVs from SolCast and a "road file" to give the
corresponding race distance. Run the script in the same folder as all the CSVs or change the variable csv_location
