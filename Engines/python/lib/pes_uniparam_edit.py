#! /usr/bin/env python3

import os
import sys

from .utils import uniparam

def listFiles(filename):
	if not os.path.isdir(filename):
		return [filename]
	else:
		entries = []
		for entry in os.listdir(filename):
			if entry in ['.', '..']:
				continue
			fullEntry = os.path.join(filename, entry)
			if os.path.isfile(fullEntry):
				entries.append(fullEntry)
		return entries

def main(uniparamFile, addedFiles, deletedFiles, outputFile, allowOverwrite):
	activeUniparamFile = uniparam.UniformParameterFile()
	try:
		activeUniparamFile.readFile(uniparamFile)
	except Exception as e:
		print("Error reading UniformParameter file: %s" % e)
		return True

	changes = {}
	for filename in addedFiles:
		effectiveFilename = filename
		if '/' in effectiveFilename:
			effectiveFilename = effectiveFilename[effectiveFilename.rfind('/') + 1:]
		if '\\' in effectiveFilename:
			effectiveFilename = effectiveFilename[effectiveFilename.rfind('\\') + 1:]

		if effectiveFilename in changes:
			print("Cannot make conflicting edits for file '%s'" % filename)
			return True

		inputFile = open(filename, 'rb')
		content = inputFile.read()
		inputFile.close()
		changes[effectiveFilename] = content

	for filename in deletedFiles:
		effectiveFilename = filename
		if '/' in effectiveFilename:
			effectiveFilename = effectiveFilename[effectiveFilename.rfind('/') + 1:]
		if '\\' in effectiveFilename:
			effectiveFilename = effectiveFilename[effectiveFilename.rfind('\\') + 1:]

		if effectiveFilename in changes:
			print("Cannot make conflicting edits for file '%s'" % filename)
			return True

		changes[effectiveFilename] = None

	for filename in changes:
		if changes[filename] is None:
			if filename in activeUniparamFile.entries:
				del activeUniparamFile.entries[filename]
		else:
			activeUniparamFile.entries[filename] = changes[filename]

	if outputFile is None:
		effectiveOutputFile = uniparamFile
	else:
		effectiveOutputFile = outputFile
		if not allowOverwrite and os.path.exists(effectiveOutputFile):
			print("Output file '%s' already exists, not overwriting" % effectiveOutputFile)
			return True

	activeUniparamFile.writeFile(effectiveOutputFile)

	return False

def usage():
	print("pes-uniparam-edit -- Edit the contents of a PES UniformParameters file")
	print("Usage:")
	print("  pes-uniparam-edit <UniformParameters file> [packed filename]...")
	print("  pes-uniparam-edit <UniformParameters file> -d [packed filename]...")
	print("Options:")
	print("  -a, --add                  Add or replace packed files to UniformParameters file (default)")
	print("  -d, --delete               Delete packed files from UniformParameters file")
	print("  -o, --output <FILE>        Save modified UniformParameters file as <FILE>")
	print("  -r, --allow-replace        Allow overwriting existing files; default without -o")
	print("  -h, --help                 Display this help")
	sys.exit()


if __name__ == "__main__":
	addMode = True
	allowOverwrite = False
	uniparamFile = None
	addedFiles = []
	deletedFiles = []
	outputFile = None

	index = 1
	while index < len(sys.argv):
		arg = sys.argv[index]
		index += 1
		if arg in ['-a', '--add']:
			addMode = True
		elif arg in ['-d', '--delete']:
			addMode = False
		elif arg in ['-o', '--output']:
			if index >= len(sys.argv):
				usage()
			if outputFile is not None:
				usage()
			outputFile = sys.argv[index]
			index += 1
		elif arg in ['-r', '--allow-replace']:
			allowOverwrite = True
		elif arg[0:1] == '-':
			usage()
		elif uniparamFile is None:
			uniparamFile = arg
		else:
			if addMode:
				addedFiles += listFiles(arg)
			else:
				deletedFiles += listFiles(arg)

	if uniparamFile is None:
		usage()

	main(uniparamFile, addedFiles, deletedFiles, outputFile, allowOverwrite)
