import time

# Filters are for pre-filtering requests, before they
# are sent to response handlers.  These should never
# be used to prevent an attacker from accessing a valid
# resource that shouldn't be publically accessible.  If
# a sensitive resource is publically accessible on your
# site, you should be ashamed of yourself.  Repent or
# find a job you are competent at.
#
# The purpose of filters is to identify malicious traffic
# and do something about it.



index = []


# Filter traffic from blocked IP addresses
#
# When other filters capture malicious traffic,
# their IP address can be added to the list of
# blocked IPs by calling block_IP().
# This filter will block all traffic from that
# IP address regardless of whether it triggers
# other filters or not.
blocked_ips = []

# This is the block duration in hours.  This
# should not be set too long, as most IP
# addresses are dynamically allocated, and
# a blocked address could get reassigned to
# a legitimate user.  In most cases, blocking
# for any amount of time up to 24 hours is
# probably reasonable, but longer is risky.
block_duration = 24

# Each request causes the blocked IPs list to
# to be fully iterated through.  If it gets
# too big, that would cause significant lag on
# legitimate traffic.  This could be leveraged
# with a DDOS attack intentionally triggering
# other filters from a large number of IPs.
# The size of the list must be limited to
# prevent this.  If this size is exceeded, the
# oldest blocks will be expired early.  Don't
# set this too high, otherwise vulnerability
# to DDOS increases.  block_duration could be
# reduced to allow for more blocks at a time,
# but this wouldn't help against multiple short
# burst DDOS attacks that keep the buffer full.
max_blocked_ips = 100


# Call this to block an IP address.  This is not
# a filter but a utility function for ip_filter().
def block_IP(ip_address):
	global blocked_ips, max_blocked_ips

	blocked_ips.append((ip_address, time.time()))

	while len(blocked_ips) > max_blocked_ips:
		blocked_ips.pop(-1)


# Filter requests from blocked IP addresses
def ip_filter(request):
	global blocked_ips

	def ip_filter_response(response):
		responsecode = 403 # Forbidden
		content = "text/plain;charset=utf-8"
		result = "403 Forbidden"

	client_address = request.client_address[0]
	for i in range(len(blocked_ips)):
		if blocked_ips[i][0] == client_address:
			now = time.time()
			if now - blocked_ips[i][1] < block_duration * 3600:
				return ip_filter_response
			else:
				blocked_ips.pop(i)

	return None
index.append(ip_filter)


# Filter attempts to gain shell access
def shell_search(request):
	terms = [
		"which+bash",
	]

	def shell_search_response(response):
		responsecode = 403 # Forbidden
		content = "text/plain;charset=utf-8"
		result = "403 Forbidden"

	for term in terms:
		if term in request.path:
			block_IP(request.client_address[0])
			return shell_search_response

	return None
index.append(shell_search)


# Filter attempts to access admin sites,
# like PHP MyAdmin
def admin_probe(request):
	terms = [
		"phpunit",
		"phpMyAdmin",
		"phpmyadmin",
	]

	def admin_probe_response(response):
		responsecode = 403 # Forbidden
		content = "text/plain;charset=utf-8"
		result = "403 Forbidden"

	for term in terms:
		if term in request.path:
			block_IP(request.client_address[0])
			return admin_probe_response

	return None
index.append(admin_probe)


# Filter probes of request methods
#
# If your site never uses a valid method
# anywhere, like DELETE, this can be used
# to filter requests that cannot have come
# from your site.  This can also filter
# requests where the method field contains
# header data for a completely different
# protocol that is a clear attack attempt.
def method_probe(request):
	terms = [
		"SSH-2.0-Go",
	]

	def method_probe_response(response):
		responsecode = 403 # Forbidden
		content = "text/plain;charset=utf-8"
		result = "403 Forbidden"

	for term in terms:
		if term == request.command:
			block_IP(request.client_address[0])
			return method_probe_response

	return None
index.append(method_probe)

