# nanomine-xml-human-validation
Human validation tool for non-spectra data in xml files in NanoMine. This tool is developed specifically for boosting the NanoMine manual validation efficiency. To run the tool, install Python 2.7 and the required packages, run human_valid.py and type in the directory of the folder that contains all the xml files you'd like to check, and two reports will be generated in that folder.

Code base: Python 2.7

Package requirement:

    lxml==3.7.3
    glob                  (Python standard library)
    collections           (Python standard library)
    uuid                  (Python standard library)
    csv                   (Python standard library)

A brief report and a full report will be generated as csv files. For spectra data, please refer to https://github.com/bingyinh/nanomine-xml-viz-validation.