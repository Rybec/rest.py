rest.py
=======

Python REST Server

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
