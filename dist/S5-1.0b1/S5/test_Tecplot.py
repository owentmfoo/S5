import random
from datetime import datetime,timedelta
from io import StringIO
import S5.Tecplot as TP
import pandas as pd
import pytest

#TODO: add coverage form SSWeather

def test_tecplotdata_constructor():
    TestTecplotData = TP.TecplotData()
    assert isinstance(TestTecplotData, TP.TecplotData)
    assert isinstance(TestTecplotData.title, str)
    assert isinstance(TestTecplotData.pressure, int)
    assert isinstance(TestTecplotData.temperature, int)
    assert isinstance(TestTecplotData.datum, list)
    assert isinstance(TestTecplotData.zone, TP.TPHeaderZone)
    assert isinstance(TestTecplotData.data, pd.DataFrame)

def test_tecplotheaderzone_constructor():
    TestTPHeaderZone = TP.TPHeaderZone()
    assert type(TestTPHeaderZone.zonetitle) == str
    assert type(TestTPHeaderZone.ni) == int
    assert type(TestTPHeaderZone.nj) == int
    assert type(TestTPHeaderZone.nk) == int
    assert type(TestTPHeaderZone.F) == str


def test_read_tecplot_file(history_file):
    hist = TP.TecplotData(history_file)
    assert isinstance(hist.data, pd.DataFrame)


def test_bad_read_tecplot_file(history_tp):
    with pytest.raises(TypeError):
        hist = TP.TecplotData(history_tp)

def test_read_write(velocity_file, tmp_path):
    tp1 = TP.TecplotData(velocity_file)
    tp1.write_tecplot(tmp_path / "test1.dat")
    tp2 = TP.TecplotData(tmp_path / "test1.dat")
    tp2.write_tecplot(tmp_path / "test2.dat")
    with open(velocity_file) as original:
        org_lines = original.readlines()
    with open(tmp_path / "test1.dat") as write1:
        write1_lines = write1.readlines()
    with open(tmp_path / "test2.dat") as write2:
        write2_lines = write2.readlines()
    pd.testing.assert_frame_equal(tp1.data, tp2.data)
    assert org_lines == write1_lines
    assert org_lines == write2_lines

def test_read_write_with_datum(velocity_file, tmp_path):
    tp1 = TP.TecplotData(velocity_file)
    tp1.pressure = 125000
    tp1.temperature = 298
    tp1.datum = ['datum']
    tp1.write_tecplot(tmp_path / "test1.dat",Datum=True)
    tp2 = TP.TecplotData(tmp_path / "test1.dat")
    tp2.write_tecplot(tmp_path / "test2.dat",Datum=True)
    with open(velocity_file) as original:
        org_lines = original.readlines()
    with open(tmp_path / "test1.dat") as write1:
        write1_lines = write1.readlines()
    with open(tmp_path / "test2.dat") as write2:
        write2_lines = write2.readlines()
    pd.testing.assert_frame_equal(tp1.data, tp2.data)
    assert write1_lines == write2_lines


def test_read_bad_var_title(tmp_path):
    filepath = tmp_path / "badvel.dat"
    with open(filepath, 'w') as file:
        file.write("""Title = "Velocity file generated by S5.HPC"
Distance (km), TargetVel (km/h)
Zone T = "", I = 2, J = 1, K = 1, F = POINT
0   69.0
3030  0 """)
    with pytest.raises(SyntaxError):
        fail = TP.TecplotData(filepath)


def test_read_bad_zone_title(tmp_path):
    filepath = tmp_path / "badvel.dat"
    with open(filepath, 'w') as file:
        file.write("""Title = "Velocity file generated by S5.HPC"
Variables = "Distance (km)", "TargetVel (km/h)"
Zone T = "", I = 
0   69.0
3030  0 """)
    with pytest.raises(SyntaxError):
        fail = TP.TecplotData(filepath)
        print(fail.zone)


def test_hist_tp(history_tp):
    assert history_tp.zone.ni == 2
    assert "CarVel(km/h)" in history_tp.data.columns
    assert "BatteryCharge(%)" in history_tp.data.columns
    assert history_tp.check_zone()


def test_check_zone(history_tp):
    history_tp.data = pd.concat([history_tp.data, history_tp.data])
    with pytest.warns(UserWarning) as record:
        assert history_tp.check_zone() == False
    assert record[0].message.args[0] == "Zone detail mismatch"


def test_headerzone_to_string():
    zone_str = 'Zone T = "", I = 3, J = 1, K = 1, F = POINT'
    tpheader = TP.TPHeaderZone(zone_str)
    assert tpheader.zonetitle == ""
    assert tpheader.ni == 3
    assert tpheader.nj == 1
    assert tpheader.nk == 1
    assert tpheader.to_string() == zone_str


def test_print_headerzone(capsys):
    zone_str = 'Zone T = "", I = 3, J = 1, K = 1, F = POINT'
    tpheader = TP.TPHeaderZone(zone_str)
    print(tpheader)
    assert capsys.readouterr().out == zone_str+'\n'

# TODO: improve this?
def test_print_tpdata(history_file):
    hist = TP.TecplotData(history_file)
    print(hist)

def test_history_read(history_file):
    hist = TP.SSHistory(history_file)
    assert isinstance(hist,TP.SSHistory)
    assert isinstance(hist.data,pd.DataFrame)
    assert isinstance(hist.title,str)
    assert isinstance(hist.zone,TP.TPHeaderZone)


@pytest.mark.parametrize('count',[random.randint(0,604800) for i in range(5)])
def test_history_add_timestamp(history_file,count):
    hist = TP.SSHistory(history_file)
    hist.data = hist.data.iloc[[1,-1],:]
    hist.update_zone_1d()
    now = datetime.now()
    baseline = datetime(now.year,now.month,now.day,now.hour,now.minute,now.second)
    correct_datetime = [baseline, baseline + timedelta(seconds=count)]
    hist.data['DDHHMMSS'] = [int(str((entry.day-baseline.day+1))+entry.strftime('%H%M%S')) for entry in correct_datetime]
    hist.add_timestamp(startday=now.strftime('%Y%m%d'))
    print(correct_datetime)
    print((hist.data["DateTime"]))
    print(timedelta(seconds=count))
    pd.testing.assert_series_equal(hist.data['DateTime'],pd.Series(correct_datetime,name='DateTime'),
                                   check_index=False)

@pytest.fixture()
def history_df():
    """Returns a dataframe with contents in a typical history file."""
    data = StringIO(
        """
,DayAndTime(s),DDHHMMSS,DrivingTime(s),DrivingTime(h),Distance(km),Distance(miles),Lap,DistanceWithinLap(km),Driving,ArrayOn,ArrayOnStand,CarVel(m/s),CarVel(km/h),CarVel(mph),DynamicPressure(Pa),YawAngle(deg),CdA(m2),HeadWind(m/s),ArrayTemperature(C),DirectSun(W/m2),HorizontalIrradiance(W/m2),NCellsShaded,CellByCellMaximumPower(W),ArrayToMPPTPower(W),Solar/InputPower(W),InclinePower(W),RollingPower(W),AeroPower(W),ControllerPowerIn(W),BatteryPowerOut(W),DriveThrust (N),TotalDriveThrust (N),BatteryCharge(%),BatteryVoltage(V),AverageCarVel(km/h)
1,30661.0,1083101.0,61.0,0.016944,0.802607,0.498717,1.0,0.802607,1.0,1.0,0.0,13.47748,48.518929,30.148265,102.775217,-1.252507,0.089827,-0.923724,39.135721,606.142353,459.473542,0.0,392.027754,389.525592,383.655066,-308.514421,288.320592,130.86279,-2730.853217,-3114.508283,-172.831318,2682.350359,98.060268,147.220824,47.366959
4383,473304.0,6112824.0,156099.0,43.360833,3021.003466,1877.164525,1.0,3021.003466,0.0,0.0,0.0,0.0,0.0,0.0,102.418701,-18.949807,0.030297,-1.076916,39.44,976.0,974.470154,0.0,828.315124,821.549708,809.627381,471.516589,272.191252,41.52339,0.0,-809.627381,0.0,5960567.050945,64.347506,132.884993,69.67125
        """)
    df = pd.read_csv(data)
    return df


@pytest.fixture()
def history_tp(history_df):
    """Return a TecplotData object containing contents in a typical history file."""
    history_tp = TP.TecplotData()
    history_tp.data = history_df
    history_tp.zone.ni = history_df.shape[0]
    return history_tp


@pytest.fixture(scope="session")
def velocity_file(tmp_path_factory):
    """Returns a velocity file."""
    filepath = tmp_path_factory.mktemp("data") / "vel.dat"
    with open(filepath, 'w') as file:
        file.write("""Title = "Velocity file generated by S5.HPC"
Variables = "Distance (km)", "TargetVel (km/h)"
Zone T = " ", I = 2, J = 1, K = 1, F = POINT
     0   69.0
  3030   69.0""")
    return filepath


@pytest.fixture(scope="session")
def history_file(tmp_path_factory):
    """Returns a velocity file."""
    filepath = tmp_path_factory.mktemp("data") / "hist.dat"
    with open(filepath, 'w') as file:
        file.write("""Title = "SolarSim4.1"
Variables = "DayAndTime(s)", "DDHHMMSS", "DrivingTime(s)", "DrivingTime(h)", "Distance(km)", "Distance(miles)", "Lap", "DistanceWithinLap(km)", "Driving", "ArrayOn", "ArrayOnStand", "CarVel(m/s)", "CarVel(km/h)", "CarVel(mph)", "DynamicPressure(Pa)", "YawAngle(deg)", "CdA(m2)", "HeadWind(m/s)", "ArrayTemperature(C)", "DirectSun(W/m2)", "HorizontalIrradiance(W/m2)", "NCellsShaded", "CellByCellMaximumPower(W)", "ArrayToMPPTPower(W)", "Solar/InputPower(W)", "InclinePower(W)", "RollingPower(W)", "AeroPower(W)", "ControllerPowerIn(W)", "BatteryPowerOut(W)", "DriveThrust (N)", "TotalDriveThrust (N)", "BatteryCharge(%)", "BatteryVoltage(V)", "AverageCarVel(km/h)"
Zone T = " ", I = 10, J = 1, K = 1, F = POINT
 30601.0 1083001.0      1.0  0.000278    0.001638    0.001018    1.0    0.001638    1.0    1.0    0.0  3.275422 11.791518  7.326909   0.569631 -17.300000 0.030297 -0.942031 39.080000 615.200000 457.171073    0.0 390.395885 388.340498 382.440333    0.000000   0.000000   0.000000 3000.000000 2617.559667 888.249500 8.882495e+02 97.987910 143.016638  5.895759
 59821.0 1163701.0  27376.0  7.604444  511.156137  317.617698    1.0  511.156137    1.0    1.0    0.0 20.757361 74.726498 46.432893 221.699509   5.671909 0.081470 -0.719215 48.324746 335.660591 373.849550    0.0 306.872745 306.872745 302.254249 -577.985846 422.420023 375.105546  183.959717 -118.294532   7.877589 1.107080e+06 76.196406 136.272501 67.218078
125040.0 2104400.0  36750.0 10.208333  717.592859  445.891530    1.0  717.592859    1.0    1.0    0.0 20.376602 73.355768 45.581161 223.305093   9.882108 0.068484 -0.508657 59.591005 951.719644 981.082973    0.0 774.842663 774.842663 763.049333 -506.991325 413.878164 311.174814  414.620152 -348.429182  18.173771 1.494580e+06 80.477942 137.974195 70.294811
154320.0 2185200.0  57465.0 15.962500 1147.464720  713.001521    1.0 1147.464720    0.0    1.0    1.0  0.000000  0.000000  0.000000   4.774514 -71.917287 0.030297 -0.920364 32.724564   0.000000   0.000000    0.0   0.000000   0.000000   0.000000    0.000000   0.000000   0.000000    0.000000    0.000000   0.000000 2.232909e+06 69.909858 133.969623 71.885025
219480.0 3125800.0  73500.0 20.416667 1475.725071  916.973047    1.0 1475.725071    1.0    1.0    0.0 21.309829 76.715384 47.668730 211.119579  -9.222027 0.070011 -1.482796 59.088328 561.407539 906.350490    0.0 722.376832 721.941478 710.912783  131.892772 433.094665 314.717614 1095.851551  384.938769  45.786184 2.828570e+06 76.800418 136.097706 72.280412
284640.0 4070400.0  86175.0 23.937500 1701.374404 1057.185042    1.0 1701.374404    0.0    1.0    1.0  0.000000  0.000000  0.000000  18.492250  -9.618066 0.068121  5.592804 26.114600 334.923216 162.985511    0.0 373.877821 373.877821 368.401396    0.000000   0.000000   0.000000    0.000000 -368.401396   0.000000 3.200377e+06 80.009415 137.822263 71.075693
313920.0 4151200.0 110250.0 30.625000 2135.991908 1327.243838    1.0 2135.991908    1.0    1.0    0.0 21.128656 76.063163 47.263458 239.696061  -6.842639 0.080004 -0.773629 38.961926 109.283617 519.337175    0.0 443.235675 443.235675 436.678132 -802.334925 429.908984 405.315011   -7.896227 -444.574359  -0.331943 4.163602e+06 66.839076 133.366944 69.746675
379080.0 5091800.0 119565.0 33.212500 2299.806252 1429.033353    1.0 2299.806252    1.0    1.0    0.0 16.047007 57.769225 35.896132 261.499556   5.335498 0.081851  4.795457 23.719179  92.687404 286.364347   13.0 242.018749 242.018749 238.568804 -678.494624 326.553927 343.632390  -44.690154 -283.258957  -2.489768 4.514567e+06 74.381162 135.751031 69.245201
408300.0 5172500.0 143595.0 39.887500 2747.936650 1707.488672    1.0 2747.936650    0.0    1.0    1.0  0.000000  0.000000  0.000000   0.256718  11.256609 0.055803  0.643422 29.545079 628.369528 188.857999    0.0 580.491600 580.491600 572.299667   -0.000000   0.000000   0.000000    0.000000 -572.299667   0.000000 5.462797e+06 63.286463 132.371509 68.892175
473511.0 6113151.0 156306.0 43.418333 3021.008253 1877.167500    1.0 3021.008253    0.0    0.0    0.0  0.000000  0.000000  0.000000 110.928409 -18.292971 0.030297 -1.059618 39.440000 976.000000 975.906697    0.0 828.981039 822.428640 810.097058  450.001448 283.041843  46.766278    0.000000 -810.097058   0.000000 5.938930e+06 73.551400 135.859733 69.579093""")
    return filepath