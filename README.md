rest.py
=======

Python REST Server

Update Note:
	rest.py has been updated to run in Python 3.  This has almost certainly broken Python 2 compatibility, and it is not reasonable at this time to try to maintain compatibility with Python 2.  If Python 2 compatibility is necessary, use commit 9ca02d6905030dbfb1db5acf4e4394b98fea8965.


Usage:

	Run from webroot:
		python rest.py
		./rest.py

	Run from anywhere:
		python rest.py --webroot /webroot

Hints:
	The program looks for a resources/ directory in webroot, and it loads
	REST resources from that location.  If no such directory exists, only
	static files in webroot and its subdirectories will be served.



An example REST site may be provided in the future.  Template resource files may
also eventually be added.
