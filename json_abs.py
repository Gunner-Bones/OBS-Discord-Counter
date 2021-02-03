import json
import os


def j_create(name, data=None):
	infile = open(name, 'w')
	if data:
		json.dump(data, infile)
	infile.close()


def j_read(name):
	infile = open(name, 'r')
	data = {}
	try:
		data = json.load(infile)
	except json.decoder.JSONDecodeError:
		pass
	infile.close()
	return data


def j_value(name, key):
	data = j_read(name)
	return data[key]


def j_overwrite(name, data):
	outfile = open(name, 'w')
	outfile.truncate()
	json.dump(data, outfile)
	outfile.close()


def j_update(name, key, new):
	data = j_read(name)
	data[key] = new
	j_overwrite(name, data)


def j_delete(name):
	os.remove(name)
