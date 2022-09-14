# parkrun-milestone-detector
A Python web scrapper for detecting upcoming milestones of Parkrun participants of given location

Requires Python 3.8+.

The script downloads and processes last several (5 by default) results' tables of given Parkrun location
and generates a list of people with 1 missing event to achieve a milestone.
The script DOES NOT DETECT volunteering milestones.

Adjust config in `main.py` to use the script in your location.
