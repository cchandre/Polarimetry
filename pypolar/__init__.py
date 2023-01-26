from datetime import date

__version__ = "2.3"
status = ""

dict_versions = {"2.1": "December 5, 2022", "2.2": "January 22, 2023", "2.3": "January 26, 2023"}

if status == "beta":
    __version_date__ = date.today().strftime("%B %d, %Y")
else:
    __version_date__ = dict_versions[__version__]
