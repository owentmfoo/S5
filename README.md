# SolarSim Strategy Support Software (S5)

To install the package directly from GitHub:

```shell
pip install git+https://github.com/owentmfoo/S5
```

Optional dependencies:

* test
* grib
* aws

Dependencies will be installed automatically apart from ecCodes which requires
building with conda.

To install ecCodes:
Use conda

```shell
conda install -c conda-forge eccodes 
```

or you can install the official source distribution, follow the
instructions [here](https://github.com/ecmwf/cfgrib) <br />

## Legacy numpy 1 / pandas 1.5.3 support

As of `v1.0.b10`, S5 supports numpy 1.x and pandas >=1.5.0 (including 1.5.3).
From `v1.0.b11` onward, S5 requires numpy 2 and pandas >=2.2.2 — the two are
mutually incompatible, so numpy1/pandas1.5.3 support is frozen at `v1.0.b10`
and will not receive further updates.

Pipelines that still depend on numpy 1.x or pandas 1.5.3 should pin their
install to the frozen tag:

```shell
pip install git+https://github.com/owentmfoo/S5@v1.0.b10
```

