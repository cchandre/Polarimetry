from datetime import date

version = "2.2"
status = "beta"

dict_versions = {"2.1": "December 5, 2022", "2.2": "January 9, 2023"}

if status == "beta":
    version_date = date.today().strftime("%B %d, %Y")
else:
    version_date = dict_versions[version]

