#!/usr/bin/env python

import os, xml, cgi, sys
from xml.dom import minidom


################################################################################
# Constants
################################################################################

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
    # Read the text
    stream = os.popen('svn log --xml ' + repo)
    if stream == None :
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

    # ID
    id = doc.createElement('id')
    id.appendChild(doc.createTextNode(repository))
    doc.documentElement.appendChild(id)
    
    # Updated
    updated = doc.createElement('updated')
    updated.appendChild(doc.createTextNode(entries[len(entries)-1].date))
    doc.documentElement.appendChild(updated)
    
    # Title
    if title :
	title_node = doc.createElement('title')
	title_node.appendChild(doc.createTextNode(title))
	doc.documentElement.appendChild(title_node)

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
    repository = 'http://svn.jivesoftware.org/svn/repos/wildfire/trunk'
    title = 'Wildfire SVN repository'
    max_entries = 10
    filename = '/var/www/feeds/wildfire-svn.xml'

    feed = generate_feed(title = title, repository = repository, max_entries = max_entries, uri = '')
    if feed :
	out = open(filename, 'w')
	out.write(feed)
	out.close()

if __name__ == "__main__" :
    main()
