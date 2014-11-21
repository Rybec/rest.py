#!/usr/bin/env python

import BaseHTTPServer
from SocketServer import ThreadingMixIn # Could use ForkingMixIn to multiprocess, but don't
from os import curdir, sep, chdir, getcwd, path
import sys
import imp

import responder

# These are files that should be in webroot/resources/
gethandlers  = ["gethandlers.py"]
posthandlers = ["posthandlers.py"]

# This should probably be converted to a config file, or a section
# in a config file.  (In fact, maybe all of the modules should be
# listed in a config file.  This might make dynamically loading
# them easier.)
shadowhandlers = ["shadowhandlers.py"]

INDEX = "/index.html"

def init():
	global gethandlers
	global posthandlers
	global shadowhandler

	sys.path.append('resources')

	if not path.isdir('resources'):
		print "No resources directory found, serving only static content"
		print "Note that this means shadowing is disabled"
		return

	# Add the shadow handlers first to allow the
	# get and post handlers to overwrite if necessary
	for handler in shadowhandlers:
		name = handler.split('.')[0]
		mod = imp.load_source(name, "resources/" + handler)
		responder.addGet(mod)
		responder.addPost(mod)

	for handler in gethandlers:
		name = handler.split('.')[0]
		resource = imp.load_source(name, "resources/" + handler)
		responder.addGet(resource)

	for handler in posthandlers:
		name = handler.split('.')[0]
		resource = imp.load_source(name, "resources/" + handler)
		responder.addPost(resource)


# We need two types of response object, probably in an external
# module (so that resource handler modules can import them).
# One will be a dynamically generated response, the other
# will be exclusively for file data.  The dynamic response
# will include a string of data to output, while the file
# response will contain a filename to stream data from (so we
# do not have to load the entire file into memory).  Using
# polymorphism, we may be able to include a generator for
# the output that will handle the streaming transparently.

class RequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
	# GET request handler
	def do_GET(self):
		if self.path == '/':
			self.path = INDEX

		response = responder.getresponse(self)
		response.send()

		return


	# POST request handler
	def do_POST(self):
		# Parse the POST form data
# This code will need to go in the POST resource handlers.
#		form = cgi.FieldStorage(
#			fp      = self.rfile,	# This is where the form data is passed in
#			headers = self.headers,
#			environ = {'REQUEST_METHOD':'POST',
#			           'CONTENT_TYPE':self.headers['Content-Type'],
#			}
#		)

		response = responder.getresponse(self)
		response.send()


# This needs to go in a mock POST resource handler.
		# Just for fun, we are going to return the parsed form data
#		for key in form.keys():
#			self.wfile.write('\t%s = %s\n' % (key, form[key].value))

		return


class ThreadedHTTPServer(ThreadingMixIn, BaseHTTPServer.HTTPServer):
	'''
	    Threaded HTTP Server
	    Seriously, this is all it takes!
	'''

def run():
	httpd = ThreadedHTTPServer(("localhost", 8000), RequestHandler)

	# If we run this in a separate thread, then we can
	# run some kind of command line interface in the
	# main thread.  Note that to avoid threading
	# related issues, we will need to kill the server	
	# and restart it for certain kinds of changes (like
	# reloading modules).
	httpd.serve_forever()

if __name__ == "__main__":
	if "--webroot" in sys.argv:
		try:
			webroot = sys.argv[sys.argv.index("--webroot") + 1]
			chdir(webroot)
		except:
			print "\tInvalid directory"
			print "\tExample: python webserver.py --webroot /var/www\n"
			
			exit()


		print "Using directory " + getcwd() + " as webroot\n"

	else:
		print "This must be run from webroot (the location you want static"
		print "files to be served from), or it must use the --webroot switch"
		print "to explicitly set the webroot.\n"

		print "Using current directory, " + getcwd() + " as webroot"

	init()

# Eventually run this in another thread, and present
# a command line interface for controlling the web
# server.  (Or even present the CLI without starting
# the web server, and give the user the chance to
# configure before starting it.
	run()
