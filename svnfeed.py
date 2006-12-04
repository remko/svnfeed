#!/usr/bin/env python

import os, xml, cgi, sys, optparse, re
from xml.dom import minidom


################################################################################
# Module information
################################################################################

__author__ = 'Remko Troncon'
__version__ = '0.1-dev'
__copyright__ = """
    Copyright (C) 2006  Remko Troncon

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, write to the Free Software
    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
    """

################################################################################
# Constants
################################################################################

PROGRAM_NAME = 'SVNFeed'
PROGRAM_URI = 'http://el-tramo.be/software/svnfeed'
PROGRAM_USAGESTRING = "usage: %prog [options] repository-uri"
PROGRAM_VERSIONSTRING = PROGRAM_NAME + ' ' + __version__ + '\nWritten by ' + __author__ + '\n' + 'For more information, please visit ' + PROGRAM_URI

ATOM_NS = 'http://www.w3.org/2005/Atom'

################################################################################
# Auxiliary functions
################################################################################

def node_text(node) :
    for child in node.childNodes :
	if child.nodeType == xml.dom.Node.TEXT_NODE :
	    return child.data
	
	
################################################################################
# Subversion functions
################################################################################
	
class SVNLogEntry :
    def __init__(self) :
	self.revision = -1
	self.author = ''
	self.date = ''
	self.msg = ''
	
def svn_entries(repo, nb_entries) :
    # Initialize SVN features
    use_limit = False

    # Determine the SVN version
    stream = os.popen('svn --version')
    if not stream : 
	return None
    version_string = stream.read()
    m = re.match(".*version (?P<major>\d+)\.(?P<minor>\d+).*", version_string)
    if m != None :
	version = int(m.group('major'))*100+int(m.group('minor'))
	if version >= 102 :
	    use_limit = True

    # Read the text
    svn_command = 'svn log --xml '
    if use_limit and nb_entries > 0 :
	svn_command += '--limit ' + str(nb_entries) + ' '
    stream = os.popen('svn log --xml ' + repo)
    if not stream :
	return None

    # Parse the document
    entries = []
    doc = minidom.parseString(stream.read())
    doc.normalize()
    for log_entry in doc.getElementsByTagName('logentry') :
	entry = SVNLogEntry()
	entry.revision = int(log_entry.getAttribute('revision'))
	for property_node in log_entry.childNodes :
	    if property_node.nodeType != xml.dom.Node.ELEMENT_NODE :
		continue

	    value = node_text(property_node)
	    if property_node.tagName == "author" :
		entry.author = value
	    elif property_node.tagName == "date" :
		entry.date = value
	    elif property_node.tagName == "msg" :
		entry.msg = value

	entries.append(entry)
	
    # Remove the oldest entries
    entries.sort(lambda x, y : cmp(y.revision, x.revision))
    if nb_entries > 0 :
	entries = entries[:nb_entries]

    return entries


################################################################################
# Feed generation
################################################################################

def generate_feed(title, repository, max_entries, uri) :
    # Retrieve the entries
    entries = svn_entries(repository, max_entries)

    # Create an atom feed
    doc = xml.dom.minidom.getDOMImplementation().createDocument(ATOM_NS, 'feed', None)
    doc.documentElement.setAttribute('xmlns',ATOM_NS)

    # Title
    if title :
	title_node = doc.createElement('title')
	title_node.appendChild(doc.createTextNode(title))
	doc.documentElement.appendChild(title_node)

    # ID
    id = doc.createElement('id')
    id.appendChild(doc.createTextNode(repository))
    doc.documentElement.appendChild(id)
    
    # Generator
    generator = doc.createElement('generator')
    generator.appendChild(doc.createTextNode(PROGRAM_NAME))
    generator.setAttribute('version', __version__)
    generator.setAttribute('uri', PROGRAM_URI)
    doc.documentElement.appendChild(generator)
    
    # Updated
    updated = doc.createElement('updated')
    updated.appendChild(doc.createTextNode(entries[len(entries)-1].date))
    doc.documentElement.appendChild(updated)
    
    # Entries
    for entry in entries :
	entry_node = doc.createElement('entry')
	
	# ID
	id_node = doc.createElement('id')
	id_node.appendChild(doc.createTextNode(repository + '#' + str(entry.revision)))
	entry_node.appendChild(id_node)

	# Updated
	updated_node = doc.createElement('updated')
	updated_node.appendChild(doc.createTextNode(entry.date))
	entry_node.appendChild(updated_node)

	# Title
	title_node = doc.createElement('title')
	title_node.appendChild(doc.createTextNode(entry.msg))
	entry_node.appendChild(title_node)

	# Authors
	author_node = doc.createElement('author')
	name_node = doc.createElement('name')
	name_node.appendChild(doc.createTextNode(entry.author))
	author_node.appendChild(name_node)
	entry_node.appendChild(author_node)

	# Alternate link
	if uri :
	    link_node = doc.createElement('link')
	    link_node.setAttribute('rel', 'alternate')
	    link_node.setAttribute('href', uri % { 'revision' : entry.revision })
	    entry_node.appendChild(link_node)

	# Content
	content_node = doc.createElement('content')
	content_node.setAttribute('type', 'text')
	content_node.appendChild(doc.createTextNode(entry.msg))
	entry_node.appendChild(content_node)
	
	doc.documentElement.appendChild(entry_node)

    #return doc.toprettyxml()
    return doc.toxml('utf-8')


def main() :
    # Parse the arguments
    parser = optparse.OptionParser(usage=PROGRAM_USAGESTRING, version=PROGRAM_VERSIONSTRING)
    parser.add_option('-t', '--title', metavar='TITLE', help='The title of the target feed', default='Feed for URI')
    parser.add_option('-f', '--file', metavar='FILE', help='File to output the feed to (stdout if omitted)')
    parser.add_option('', '--max-entries', metavar='ENTRIES', help='The maximum number of entries in the feed. Default: %default', type='int', default=10)
    parser.add_option('-u', '--uri', metavar='URI', help='Link to the web interface (e.g. \'http://example.com/%(revision)s\')')
    (options, args) = parser.parse_args()
    
    # Get the repository URI
    if len(args) != 1 :
	sys.exit('Repository URI missing')
    repository = args[0]
    
    feed = generate_feed(title = options.title, repository = repository, max_entries = options.max_entries, uri = options.uri)
    if feed and options.file :
	out = open(options.file, 'w')
	out.write(feed)
	out.close()
    else :
	print feed

if __name__ == "__main__" :
    main()
