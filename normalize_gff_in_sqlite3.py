# import argparse
import os
import sqlite3
import sys

def create_att_table(db, source_tbl):
	"""1st normal form: all features contain only one piece of data per row"""
	if os.path.exists(db):
		con = sqlite3.connect(db)
		cur = con.cursor()

		atts = {
				# "Alias" :                     '.',
				# "Dbxref" :                    '.',
				"ID" :                        '.',
				# "Name" :                      '.',
				# "Ontology_term" :             '.',
				"Parent" :                    '.'
				# "derived_computed_cyto" :     '.',
				# "derived_experimental_cyto" : '.',
				# "exonA" :                     '.',
				# "exonB" :                     '.',
				# "fullname" :                  '.',
				# "gbunit" :                    '.',
				# "read_count" :                '.'
			}
		"""if Parent or ID missing then att values in row should be null"""

		cur.execute('CREATE TABLE IF NOT EXISTS attributes(' +
					' TEXT, '.join(atts.keys()) + ' TEXT, ' +
					'type TEXT, start INT);'
				   )
		con.commit()

		cur.execute("SELECT COUNT(*) FROM " + source_tbl)
		row_count = cur.fetchone()[0]

		for i in range(row_count):
			cur.execute("SELECT type, start, att FROM " + source_tbl +
						   " LIMIT 1 OFFSET " + str(i) + ";")

			tp, strt, att = cur.fetchone()
			att_list = att.rstrip(';').split(';')

			# Updates atts with non-null values in current row
			for tv in att_list:
				tag, value = tv.split('=')
				if tag in atts.keys():
					atts[tag] = value

				# need to add code if adding columns dynamically is desired


			# 4 ?s are for 2 attributes (ID, Parent), type, and start
			insert_cmd = "INSERT INTO attributes values("
			insert_cmd += "?, " * len(atts) + "?, ?);"

			cur.execute(insert_cmd, tuple(atts.values()) + (tp, strt))

			if i%500 == 0:
				con.commit()
				print(i)

			atts = {
				# "Alias" :                     '.',
				# "Dbxref" :                    '.',
				"ID" :                        '.',
				# "Name" :                      '.',
				# "Ontology_term" :             '.',
				"Parent" :                    '.'
				# "derived_computed_cyto" :     '.',
				# "derived_experimental_cyto" : '.',
				# "exonA" :                     '.',
				# "exonB" :                     '.',
				# "fullname" :                  '.',
				# "gbunit" :                    '.',
				# "read_count" :                '.'
			}

		con.commit()
		remove_col(db, source_tbl, "att")
		remove_duplicates(db, source_tbl)
	else:
		sys.exit(f'aborting: database {db} does not exist')

def remove_col(db, tbl, col):
	if os.path.exists(db):
		con = sqlite3.connect(db)
		cur = con.cursor()
		cur.execute("ALTER TABLE " + tbl + " DROP COLUMN " + col + ";")
		con.commit()
	else:
		sys.exit(f'aborting: database {db} does not exist')

def remove_duplicates(db, tbl):
	if os.path.exists(db):
		con = sqlite3.connect(db)
		cur = con.cursor()
		cur.execute("CREATE TABLE Temp AS SELECT DISTINCT * FROM " + tbl + ";")
		cur.execute("DROP TABLE " + tbl + ";")
		cur.execute("ALTER TABLE Temp RENAME TO " + tbl + ";")
		con.commit()
	else:
		sys.exit(f'aborting: database {db} does not exist')


def normal_forms(db, k):
	if os.path.exists(db):
		con = sqlite3.connect(db)
		cur = con.cursor()
		cur.execute()
		con.commit()

		match k:
			case 2:
				# query to manually check how many distinct values in each column
				# sqlite3 db.db "select count(distinct seqid), count(distinct source), count(distinct type), count(distinct start), count(distinct end), count(distinct score), count(distinct strand), count(distinct phase) from tbl"
				"""
				Possibly NF2 schema


				CREATE TABLE attributes(ID TEXT, Parent TEXT, type TEXT, start INT);
				CREATE TABLE SCORES(
				  source TEXT,
				  start INT,
				  "end" INT,
				  score NUM
				);
				CREATE TABLE IF NOT EXISTS "dm1pct"(
				  source TEXT,
				  type TEXT,
				  start INT,
				  "end" INT,
				  phase TEXT
				);
				CREATE TABLE SEQID_STRAND(
				  seqid TEXT,
				  type TEXT,
				  start INT,
				  strand TEXT
				);
				"""
				print(k)
			case 3:
				print(k)
			case 4:
				print(k)
			case 5:
				print(k)
			case 6:
				print(k)
	else:
		sys.exit(f'aborting: database {db} does not exist')


dbname = "dm1pct.db"
table = "dm1pct"

create_att_table(dbname, table)

normal_forms(dbname, 2)
