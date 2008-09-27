#
# CDDL HEADER START
#
# The contents of this file are subject to the terms of the
# Common Development and Distribution License (the "License").
# You may not use this file except in compliance with the License.
#
# You can obtain a copy of the license at usr/src/OPENSOLARIS.LICENSE
# or http://www.opensolaris.org/os/licensing.
# See the License for the specific language governing permissions
# and limitations under the License.
#
# When distributing Covered Code, include this CDDL HEADER in each
# file and include the License file at usr/src/OPENSOLARIS.LICENSE.
# If applicable, add the following below this CDDL HEADER, with the
# fields enclosed by brackets "[]" replaced with your own identifying
# information: Portions Copyright [yyyy] [name of copyright owner]
#
# CDDL HEADER END
#
# Copyright 2007 Sun Microsystems, Inc.  All rights reserved.
# Use is subject to license terms.
#

import os
import errno
import osol_install.install_utils
from subprocess import *
import fnmatch


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def get_manifest_value(manifest_obj, path, is_key=False):
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	""" Read the value of the path specified.
	This returns only the first value of the list.

	Args:
	   manifest_obj: Manifest object (could be ManifestServ or
		ManifestRead object)
	   path: path to read
	   is_key: Set to True if the path is to be interpreted as a key

	Returns:
	   the first value found (as a string) if there is at least
		one value to retrieve.
	   None: if no value found

	Raises:
	   None
	"""

	node_list = manifest_obj.get_values(path, is_key)
	if (len(node_list) > 0):
		return str(node_list[0])
	return None

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def get_manifest_list(manifest_obj, path, is_key=False):
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	""" Create a list of the values of the path specified.

	Args:
	   manifest_obj: Manifest object (could be ManifestServ or
		ManifestRead object)
	   path: path to read from
	   is_key: Set to True if the path is to be interpreted as a key

	Returns:
	   A list of values.
	   An empty list is returned if no values are found.

	Raises:
	   None
	"""

	node_list = manifest_obj.get_values(path, is_key)

	for i in (range(len(node_list))):
		node_list[i] = str(node_list[i])
	return node_list 

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def create_tmpdir():
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	""" Create a temporary directory in /tmp/distro_tool.<pid>
	Returns: directory created
		None on error
	Raises:
		None
	"""
	dir_name = os.path.join('/tmp', 'distro_tool.' + str(os.getpid()))

	try:
		os.makedirs(dir_name)
	except OSError:
		pass

	return dir_name 

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def cleanup_dir(mntpt):
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	"""Remove all files and directories underneath the mount point.
	Any errors are ignored since they aren't fatal.

	Input:
	   mntpt: mount point to remove files and directories from

	Returns:
	   None

	Raises:
	   None
	"""

	for root, dirs, files in os.walk(mntpt, topdown=False):
		for name in files:
			try:
				os.unlink(os.path.join(root,name))
			except:
				pass

		for dir in dirs:
			try:
				os.rmdir(os.path.join(root,dir))
			except:
				pass

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def cleanup_tmpdir(mntpt):
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	"""Remove all files and directories and the mount point.
	Any errors are ignored since they aren't fatal.

	Input:
	   mntpt: mount point to remove files and directories from

	Returns:
	   None

	Raises:
	   None
	"""


	cleanup_dir(mntpt);
	try:
		os.rmdir(mntpt)
	except:
		pass