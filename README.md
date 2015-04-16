zipflights
==========

Bradley Jacobs, Apr 2014

###Data driven web app for saving money on airline tickets.
============
#####Unfortunately as of December 2014 the method for querying flights used here no longer works.  The service used for querying live flight data, ITA Software (owned by Google), has changed their protocol and made it infeasible to continue scraping their site.  ITA was one of the last sites where it was possible to automate airfare searches for free.  I believe it may be still be possible to query ITA using methods similar to the ones posted here, but developing these is not currently the best use of my time (feel free to drop me a line if you want more detail on this).  Hence, this repo is maintained for archival purposes only.  
=============


Using pricing and routing data using data from the Bureau of Transportation Statistics (BTS) [Origin and Destination Passenger Survey](http://www.transtats.bts.gov/Tables.asp?DB_ID=125) (compiled from 2012 Quarter 4 through 2013 Quarter 3).  I built a Python-Flask web app that identifies good-value domestic routes from a chosen origin airport.  The app allows a user to perform a month-long search of ticket prices from the targeted airports by querying [ITA Matrix](http://matrix.itasoftware.com).

The second section of the site is aimed at travelers with specific itineraries who want to fly non-stop.  Using the BTS data, I identified routes where itineraries that include a change of planes at a particular airport are often less expensive than those that terminate at that airport.  For example, a trip from San Francisco to Milwaukee that includes a change in Chicago will often cost less than the simple non-stop flight between San Francisco and Chicago.  A traveler can, therefore, save money by buying a ticket to Milwaukee but only traveling as far as Chicago.  This is a practice known as Hidden-City Ticketing and it is frowned upon by the airlines [(read more here)](http://www.boardingarea.com/viewfromthewing/2012/01/07/how-to-use-hidden-city-and-throwaway-ticketing-to-save-money-on-airfare/).  The app searches among target destinations that were identified with the BTS data to build Hidden-City itineraries and compares these with price for buying a simple round-trip ticket with non-stop outbound and return flights (again by querying the ITA Matrix).

###Data Analysis Code:

Python code that compiles the BTS Quarterly Surveys [(download the zip files)](http://www.transtats.bts.gov/DL_SelectFields.asp?Table_ID=247&DB_Short_Name=Origin%20and%20Destination%20Survey) for use in the web app is contained here:

zipflights_data_parsing.py

A script that writes dictionaries that are used by the web app by calling functions from this file is saved as:

zipflights_data_script.py

Copies of the dictionaries used in the web app are saved in the /app/static subdirectories of the [web app](https://github.com/BradAJ/zipflights/tree/master/web_app).

###App Code:

Within the web_app directory is the Python-Flask code for the website.  Changing the python path to your local path in run.py and then running this file from the command line should be sufficient to launch a server so that the site can be accessed locally through a web browser.

Note that the app fetches live airline pricing data by querying [ITA Matrix](http://matrix.itasoftware.com).  Like any airline ticket search this can take a significant amount of time (up to 30 sec), during which time the app will not be responsive (your browser's status bar will say something like: "waiting for zipflights.co").  Please be patient.

