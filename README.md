# [SVNFeed: Monitoring Subversion with RSS](http://el-tramo.be/software/svnfeed)

## About

SVNFeed is a Python script that creates RSS feeds of Subversion repository logs.

Beware that SVNFeed is still in alpha stage, and that it probably contains bugs. Feel free to report bugs or suggestions for improvement to me.


## Requirements

- Python >= 2.3.


## Usage

A feed is simply created by running the script and passing it the URI of the
repository to watch, optionally with a link that describes the log in more
detail. For example, to create a feed of the SVN repository of this script:

		./svnfeed.py --file=svnfeed.xml --title='SVNFeed SVN Feed'
--uri='http://websvn.el-tramo.be/listing.php?repname=SVNFeed&rev=%(revision)s' http://svn.el-tramo.be/svnfeed/

See the `-help` option of the script for more details on its usage.


## TODO

- Make more robust to invalid input
- It seems that Python encodes & to & in URIs, which confuses scripts like WebSVN
