zipflights
==========

Bradley Jacobs, Apr 2014

###Data analysis used in a web app for saving money on airline tickets.

####NOTE: This repo contains Python code that parses data for use with the web app Zipflights.  The app itself is located at in a separate [repo](https://github.com/BradAJ/zipflights-app).

Using pricing and routing data using data from the Bureau of Transportation Statistics [Origin and Destination Passenger Survey](http://www.transtats.bts.gov/Tables.asp?DB_ID=125) (compiled from 2012 Quarter 4 through 2013 Quarter 3).  I built a Python-Flask web app that identifies good-value domestic routes from a chosen origin airport.  The app allows a user to perform a month-long search of ticket prices from the targeted airports by querying [ITA Matrix](http://matrix.itasoftware.com).

The second section of the site is aimed at travelers with specific itineraries who want to fly non-stop.  Using the BTS data, I identified routes where itineraries that include a change of planes at a particular airport are often less expensive than those that terminate at that airport.  For example, a trip from San Francisco to Milwaukee that includes a change in Chicago will often cost less than the simple non-stop flight between San Francisco and Chicago.  A traveler can therefore, save money by buying a ticket to Milwaukee but only traveling as far as Chicago.  This is a practice known as Hidden-City Ticketing and it is frowned upon by the airline [(read more here)](http://www.boardingarea.com/viewfromthewing/2012/01/07/how-to-use-hidden-city-and-throwaway-ticketing-to-save-money-on-airfare/).  The app searches among target destinations that were identified with the BTS data to build Hidden-City itineraries and compares these with price for buying a simple round-trip ticket with non-stop outbound and return flights (again by querying the ITA Matrix).

###Code

Python code that compiles the BTS Quarterly Surveys [(download the zip files)](http://www.transtats.bts.gov/DL_SelectFields.asp?Table_ID=247&DB_Short_Name=Origin%20and%20Destination%20Survey) and for use in the web app is contained here:

zipflights_data_parsing.py

A script that writes dictionaries that are used by the web app by calling functions from this file is saved as:

zipflights_data_script.py

Copies of the dictionaries used in the web app are saved in the /app/static subdirectories of the [Zipflights-App repo](https://github.com/BradAJ/zipflights-app), the code there is Python-Flask for the website itself.

