# ERDDAP Compliance

A wrapper for the [IOOS Compliance Checker](https://github.com/ioos/compliance-checker/) that scans all datasets in an ERDDAP server and produces a report for each dataset.

By default, it is assumed that all datasets will be checked.  Users can specify an explicit list of datasets to be ignored.  Alternatively, a regular expression can be used to select the datasets to be ignored.

```
usage: cc_erddap.py [-h] [-s STANDARDS] [-e EXCLUDE] [--exclude_regex] [-f FORMAT] [-o OUTPUT_DIR] [-t TIME_OFFSET] [--timeout TIMEOUT] [-v VERBOSE] [--disable_ssl_verify]
                    [--download_local] [--work WORK]
                    erddap_server

positional arguments:
  erddap_server         The URL of an ERDDAP instance e.g. https://www.server.com/erddap/

optional arguments:
  -h, --help            show this help message and exit
  -s STANDARDS, --standards STANDARDS
                        What Compliance Checker standards each dataset should be checked 
                        against. Multiple standards may be specified as a CSV string. A 
                        full list of acceptable may be gathered by running the command 
                        "compliance-checker --list-tests". Default: cf:1.6

  -e EXCLUDE, --exclude EXCLUDE
                        List of datasets to exclude from compliance checker, 
                        default: allDatasets

  --exclude_regex       Use regular expressions to filter list of datasets to exclude

  -f FORMAT, --format FORMAT
                        Set the output format [text,html,json,json_new], default: text

  -o OUTPUT_DIR, --output_dir OUTPUT_DIR
                        Where reports should be written to. If not specified output 
                        will be printed to screen.

  -t TIME_OFFSET, --time_offset TIME_OFFSET
                        A python Timedelta string that specifies the time range of data 
                        to retrieve from each dataset. This is to reduce the size of 
                        netCDF files being queried from the ERDDAP server, since 
                        metadata compliance is what's being audited and not the actual 
                        data, we only need 1 or more records to get a valid netCDF file.
                        Default: 1day

  --timeout TIMEOUT     Number of seconds to wait for a response from the ERDDAP server 
                        when downloading a sample of a dataset locally

  -v VERBOSE, --verbose VERBOSE
                        Passes the desired verbosity flag to the compliance checker 
                        library. Acceptable Values: 0, 1, 2. The higher the value, the 
                        more verbose the output. Default: 0

  --disable_ssl_verify  Disables the SSL verify check of the target server, this is 
                        insecure and potentially dangerous, do not use this option 
                        unless you trust the destination server and understand why the 
                        certificate on that server may be causing issues.

  --download_local      Download NetCDF file samples and process them locally rather
                        than on-the-fly from the ERDDAP server.

  --work WORK           Specify the temporary working directory for downloaded sample 
                        files.
```
