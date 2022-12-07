#SolarSim Strategy Support Sofware (S5)

To install the package locally

> `python3 -m pip install .`

### Core package requirements
<li>pandas
<li> pytz
<li> matplotlib
<li> pvlib
<li> tqdm

To install the required core package
>`$ pip install --user -r requirements.txt`
### Extra pacakge requiried for Weather.readgrib
cfgrib, xarray and ecCodes are needed as well.
ecCodes cannot be installed just by pip 

To install ecCodes: 
either used conda<br />
> `$ conda install -c conda-forge eccodes`<br />

or you can install the official source distribution, follow the instructions [here](https://github.com/ecmwf/cfgrib) <br />

