#!/usr/bin/env python3
import argparse
import gzip
import os
import re
import sqlite3
import sys


def getfp(filename):
	"""Returns a file pointer for reading based on file name"""
	if   filename.endswith('.gz'):
		return gzip.open(filename, 'rt')
	elif filename == '-':
		return sys.stdin
	else:
		return open(filename)

def create_gff_database(db):
	"""create a new instance of database"""

	if not(os.path.exists(db)):# sys.exit(f'aborting: database {db} exists')
		con = sqlite3.connect(db)
		cur = con.cursor()
		con.commit()


def create_sql_table(db, table):
	"""create a new table in an existing database"""

	if os.path.exists(db):
		con = sqlite3.connect(db)
		cur = con.cursor()
		cur.execute('CREATE TABLE IF NOT EXISTS ' +	table + '(' +
					'seqid TEXT, ' +
					'source TEXT, ' +
					'type TEXT, ' +
					'start INTEGER, ' +
					'end INTEGER, ' +
					'score NUMERIC, ' +
					'strand TEXT, ' +
					'phase TEXT, ' +
					'att TEXT' +
					# 'id TEXT, ' +
					# 'pid TEXT' +
					');')
		con.commit()
	else:
		sys.exit(f'aborting: database {db} does not exist')

def populate_table(filename, db, table):
    # if os.path.exists(db): sys.exit(f'aborting: database {db} exists')
	con = sqlite3.connect(db)
	cur = con.cursor()

	fp = getfp(filename)

	row_count = 0
	# with open(db + "_inserts", "w") as insert_cmds_file:
	for line in fp:
		row_count += 1
		# print(row_count)

		if line.startswith('#'): continue
		fields = line.rstrip().split('\t')
		if len(fields) != 9: sys.exit('GFF3 requires 9 fields')
		# sid, src, typ, beg, end, scr, st, ph, att = fields

		att = fields[-1]
		info = {}
		for tv in att.rstrip(';').split(';'):
			tag, value = tv.split('=')
			info[tag] = value

		insert_command = "insert into " + table + " values('"

		if "'" in att:
			insert_command += "', '".join(fields[:8])
			insert_command += "', ?);"

			# if "ID" in info:
			# 	insert_command += ", '" + info["ID"] + "'"
			# else:
			# 	insert_command += ", '.'"

			# if "Parent" in info:
			# 	insert_command += ", '" + info["Parent"] + "');"
			# else:
			# 	insert_command += ", '.');"
			# print(type(att))
			cur.execute(insert_command, (att,))
			con.commit()
			continue
		else:
			insert_command += "', '".join(fields)

		# if "ID" in info:
		# 	insert_command += "', '" + info["ID"]
		# else:
		# 	insert_command += "', '."

		# if "Parent" in info:
		# 	insert_command += "', '" + info["Parent"] + "');"
		# else:
		# 	insert_command += "', '.');"

		insert_command += "');"
		# insert_cmds_file.write(insert_command)
		cur.execute(insert_command)
		if row_count % 300 == 0:
			con.commit()
			print(row_count)#, '  ', insert_command[:20], ' ... ', insert_command[-20:])#, '     field 9: ', fields[8:9])
	con.commit()
	return 0
		# self ID in attributes
		# here its a transcript ID

def empty_sql_table(db, table):
	if os.path.exists(db):# sys.exit(f'aborting: database {db} exists')
		con = sqlite3.connect(db)
		cur = con.cursor()
		cur.execute('DELETE from ' + table + ';')
		con.commit()
	else:
		sys.exit(f'aborting: database {db} does not exist')


gff_file = "dm1pct.gff3.gz"
dbname = "dm1pct.db"
table = "dm1pct"



create_gff_database(dbname)
create_sql_table(dbname, table)

empty_sql_table(dbname, table)

populate_table(gff_file, dbname, table)
















