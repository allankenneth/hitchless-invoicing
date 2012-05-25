|_  o _|_ _ |_  |  _  _  _ 
| | |  |_(_ | | | (/__> _> 
 o __     _  o  _  o __ (_|
 | | |\_/(_) | (_  | | |__|


My invoicing system written in Python against Google App Engine and the Google Calendar API. This is a learning project for me, and it's not complete, though it is close to useable. It was written to scratch an itch and provide myself with a simple web-based invoicing system that logged time and create invoices from it. While it is quite flexible with minor tweaking, it is focussed on the single-person freelancer workflow/usecase.

While this runs on Google App Engine, this project is designed to run on an individual's App Engine account as a stand-alone version. You download the code, alter the config files, and deploy it to whatever yourinvoicing.appspot.com instance you choose. As such, you are in control of your own data usage.
 
It was developed with a "mobile-first" mindset, but it doesn't rely on gestures and thus no framework dependency other than basic jQuery.


