import mimetypes
import sys
import os

if sys.version_info.major == 2:
	import urllib2 as urllib
	urllib.request = urllib
elif sys.version_info.major == 3:
	import urllib
	import urllib.request

# Constants

# Files are transferred in chunks of this size.
# A larger size will probably be faster, but
# it will also use more memory.
BUFFER_SIZE = 1024 * 8


# Internal globals

# Each element must be a dict of resource keys referencing the response
# handlers for those resources.

# Response handlers should call set_response() on the response to
# set the response code, and set_content() to set the content type.
response_handlers  =  {"GET":{}, "POST":{}, "DELETE":{}}

# Filters are functions that take a request and return a response
# handler if the request matches or None otherwise.  Filters should
# be very fast, to minimize response latency.
#
# Filters are primarily intended to capture malicious requests,
# so that they can be handled differently from legitimate traffic.
#
# Filters should be used carefully, both to minimize response
# latency and to avoid false positives that could negtively impact
# the experience of legitimate users.
response_filters = []


# Functions

# These will populate the response handlers for requests.
# Currently, other request types can be added manually by adding the
# appropriate request type to response_handers and populating it with
# a dict.
def initGet(handlers):
	global response_handlers
	response_handlers["GET"]  = handlers.index

def initPost(handlers):
	global response_handlers
	response_handlers["POST"] = handlers.index


# These will add handlers for the appropriate request methods.
# Use these with care, as new handlers can overwrite old ones
# if there are naming conflicts.
def addGet(handlers):
	global response_handlers
	response_handlers["GET"] = \
	        dict(list(response_handlers["GET"].items()) + list(handlers.index.items()))

def addPost(handlers):
	global response_handlers
	response_handlers["POST"] = \
	        dict(list(response_handlers["POST"].items()) + list(handlers.index.items()))

def addDelete(handlers):
	global response_handlers
	response_handlers["DELETE"] = \
	        dict(list(response_handlers["DELETE"].items()) + list(handlers.index.items()))

def addFilter(filters):
	global response_filters
	response_filters = response_filters + filters.index



def filter_request(request):
	global response_filters

	triggered_filter = None
	for filter in response_filters:
		triggered_filter = filter(request)
		if triggered_filter is not None:
			return triggered_filter


# Creates and returns the appropriate response type for the request
def getresponse(request):
	global response_handlers
	# Get the resource name
	resource = request.path.strip("/").split("?", 1)[0].split("/", 1)[0]


	# Filter request
	triggered_filter = filter_request(request)
	if triggered_filter is not None:
		return triggered_filter(request)


	# Check if the first path element is a valid resource
	if resource in response_handlers[request.command]:
		# If so, generate a resource response
		# Note that resources will shadow directories with the
		# same name.
		return ResourceResponse(request)
	else:
		# Otherwise assume it is a file request
		return FileResponse(request)



# Class definitions

# Do not use this abstract class.  Instead inherit or use one of the
# other included responses.
class Response(object):
	# request = BaseHTTPServer.RequestHandler
	def __init__(self, request):
		self.request  = request
		self.response = 200		# Default value
		self.content  = 'text/html'	# Default value
		self.extra_headers = {}

	def set_response(self, code):
		if code in self.request.responses:
			self.response = code
		else:
			# Throw some kind of exception here
			pass

	def set_content(self, contenttype):
		self.content = contenttype

	def set_extra_header(self, header, value):
		self.extra_headers[header] = value

	# Override this!
	# This should send the headers and write the data
	# to the output stream (self.request.wfile.write())
	def send(self):
		pass

	# Send error page
	# send() function should return directly after calling this,
	# to avoid trying to send anything else
	# Set reponse code before calling this
	def send_error(self):
		error_text = self.request.responses[self.response][0]

		data  = "<!DOCTYPE html>"	# HTML5
		data += "<html><head><title>"
		data += error_text
		data += "</title></head>"
		data += "<body>"
		data += "<pre>"
		data += str(self.response) + ": " + error_text
		data += "</pre>"
		data += "</body>"
		data += "</html>"


		# Send HTTP header data
		self.request.send_response(self.response)
		self.request.send_header('Content-Type', 'text/html')
		self.request.send_header('Content-Length', len(data))
		for k, v in self.extra_headers.items():
			self.request.send_header(k, v)
		self.request.end_headers()

		# Send the data
		self.request.wfile.write(bytes(data, encoding="utf-8"))

	

# For resource handling (not for file handling)
class ResourceResponse(Response):
	# Instance variables
	# resource = the first element of the path (for "/piano/xyz",
	#            this would be "piano")
	# query    = the query string, parsed into a dictionary if possible
	# subpath  = any elements of the path beyond the first

	def __init__(self, request):
		# Call parent constructor
		super(ResourceResponse, self).__init__(request)
		self.cookie   = {}

		# Parse the URL path

		# Split off the query string
		if "?" in self.request.path:
			self.resource, self.query = \
			        self.request.path.strip("/").split("?", 1)
			# Split the query string first at & and then split
			# expressions at = and put the result into a dictionary
			try:
				self.query = {urllib.parse.unquote_plus(key):urllib.parse.unquote_plus(value)
				              for key, value in [element.split("=")
				              for element in self.query.split("&")]}
			except Exception as e:
				# We will assume that the malformed query
				# string was intentional, and we will let
				# the application handle it
				self.query = urllib.parse.unquote_plus(self.query)
		else:
			self.resource = self.request.path.strip("/")
			self.query = None

		# Extract the base resource from the URL
		# Whatever is left is put in subpath for the user to manage
		if "/" in self.resource:
			self.resource, self.subpath = \
			        self.resource.split("/", 1)
		else:
			self.subpath = None

		# If this is a POST request, let's kindly parse the data if it is
		# form data.
		if request.command == "POST" and \
		   "Content-Type" in request.headers and \
		   "application/x-www-form-urlencoded" in request.headers["Content-Type"]:
			try:
				clength = int(request.headers["Content-Length"])

				self.postquery = request.rfile.read(clength)
				# Turn the form data into a dictionary
				self.postquery = {key:value
				                  for key, value in [element.split("=")
				                  for element in self.postquery.split("&")]}
			except:
				pass
		# If the POST data is JSON data, we will read it into
		# a string for the application.
		elif request.command == "POST" and \
		     "Content-Type" in request.headers and \
		     "application/json" in request.headers["Content-Type"]:

			clength = int(request.headers["Content-Length"])
			self.postjson = request.rfile.read(clength)


		# Ok, so we will handle cookies too...
		if "Cookie" in request.headers:
			request.cookie = request.headers["Cookie"]

			try:
				request.cookie = {key:value
				               for key, value in [element.split("=")
				               for element in request.cookie.split("; ")]}
			except:
				pass

	# This should generate the data, then send the header and then the data
	def send(self):
		global response_handlers
		data = ""
		try:
			data = response_handlers[self.request.command][self.resource](self)
		except KeyError:
			self.set_response(404)
			self.send_error()
			return
		except Exception as e:
			print(e)
			self.set_response(500)
			self.send_error()
			return

		# Send HTTP header data
		self.request.send_response(self.response)
		self.request.send_header('Content-Type', self.content)
		self.request.send_header('Content-Length', len(data))
		for k, v in self.extra_headers.items():
			self.request.send_header(k, v)
		self._send_cookies()
		self.request.end_headers()

		# Send the data
		if type(data) == str:
			self.request.wfile.write(bytes(data, encoding="UTF-8"))
		else:
			self.request.wfile.write(data)

	def _send_cookies(self):
		for k, v in self.cookie.items():
			cookie = str(k) + "=" + str(v)
			self.request.send_header('Set-Cookie', cookie)

# For file handling
class FileResponse(Response):
	# Instance variables
	# path = the cleaned file path


	def __init__(self, request):
		# Call parent constructor
		super(FileResponse, self).__init__(request)

		cwd = os.getcwd()

		# Trim any query string
		self.path = cwd + urllib.request.url2pathname(os.path.normpath(self.request.path.split("?", 1)[0]))

		# Find the MIME type and set the content
		(self.content, _) = mimetypes.guess_type(self.path)
		if not self.content:
			self.content = "application/octet-stream"

	# Send the file, or 
	def send(self):
		file_size = 0
		try:
			file_size = os.path.getsize(self.path)
		except OSError as e:
			data = ""
			if e.errno == 2:	# No such file...
				self.set_response(404)
				self.send_error()
			else:			# errno: 13, Permission denied
				print(e)
				self.set_response(403)
				self.send_error()
			# We will consider anything that is not 404 to be
			# Permission denied, even if it is some other
			# reason.  This will help avoid revealing information
			# that could be used to compromise security.
			return
		except Exception as e:
			print(e)
			# If it is not an OSError, it is probably an
			# internal server error
			self.set_response(500)
			self.send_error()
			return

		file = None
		try:
			file = open(self.path, 'rb')

			# Send HTTP header data
			self.request.send_response(self.response)
			self.request.send_header('Content-Type', self.content + "; charset=utf-8")
			self.request.send_header('Content-Length', file_size)
			self.request.end_headers()

			# Send the file data in chunks of BUFFER_SIZE
			buffer = file.read(BUFFER_SIZE)
			while buffer:
				self.request.wfile.write(buffer)
				buffer = file.read(BUFFER_SIZE)
		except IOError as e:
			data = ""
			if e.errno == 2:	# No such file...
				self.set_response(404)
				self.send_error()
			else:			# errno: 13, Permission denied
				print(e)
				self.set_response(403)
				self.send_error()
		except Exception as e:
			print(e)
			# We have already checked to make sure the file
			# exists and is readable.  If we fail now, it is
			# probably something else.
			self.set_response(500)
			self.send_error()
			return			
		finally:
			if file:
				file.close()
