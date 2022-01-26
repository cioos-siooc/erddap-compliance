# ERDDAP Compliance

A wrapper for the [IOOS Compliance Checker](https://github.com/ioos/compliance-checker/) that scans all datasets in an ERDDAP server and produces a report for each dataset.

By default, it is assumed that all datasets will be checked.  Users can specify an explicit list of datasets to be ignored.  Alternatively, a regular expression can be used to select the datasets to be ignored.

```
usage: cc_erddap.py [-h] [-s STANDARDS] [-e EXCLUDE] [--exclude_regex]
                    [-f FORMAT] [-o OUTPUT_DIR] [-t TIME_OFFSET] [-v VERBOSE]
                    erddap_server

positional arguments:
  erddap_server         The URL of an ERDDAP instance e.g.
                        https://www.server.com/erddap/

optional arguments:
  -h, --help            show this help message and exit
  -s STANDARDS, --standards STANDARDS
                        What Compliance Checker standards each dataset should
                        be checked against. Multiple standards may be
                        specified as a CSV string. A full list of acceptable
                        values may be gathered by running the command
                        "compliance-checker --list-tests". Default: cf:1.6
  -e EXCLUDE, --exclude EXCLUDE
                        List of datasets to exclude from compliance checker,
                        default: allDatasets
  --exclude_regex       Use regular expressions to filter list of datasets to
                        exclude
  -f FORMAT, --format FORMAT
                        Set the output format [text,html,json,json_new],
                        default: text
  -o OUTPUT_DIR, --output_dir OUTPUT_DIR
                        Where reports should be written to. If not specified
                        output will be printed to screen.
  -t TIME_OFFSET, --time_offset TIME_OFFSET
                        How many seconds from maxTime (UTC) should a dataset
                        be queried. This is to reduce the size of netCDF files
                        being queried from the ERDDAP server, since metadata
                        compliance is what's being audited and not the actual
                        data, we only need 1 or more records to get a valid
                        netCDF file. Default: 5
  -v VERBOSE, --verbose VERBOSE
                        Passes the desired verbosity flag to the compliance
                        checker library. Acceptable Values: 0, 1, 2. The
                        higher the value, the more verbose the output.
                        Default: 0
```
