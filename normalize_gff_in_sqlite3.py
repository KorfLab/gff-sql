# import argparse
import os
import sqlite3
import sys
from itertools import combinations

def create_tbl(db, tbl, cl_list):
	if os.path.exists(db):
		con = sqlite3.connect(db)
		cur = con.cursor()
		cur.execute('CREATE TABLE IF NOT EXISTS attributes(' +
					'? TEXT, ' * len(cl_list)  + ' TEXT);',
					tuple(cl_list)
				   )
		con.commit()

	else:
		sys.exit(f'aborting: database {db} does not exist')

def create_att_table(db, source_tbl):
	"""1st normal form: all features contain only one piece of data per row"""
	if os.path.exists(db):
		con = sqlite3.connect(db)
		cur = con.cursor()

		cur.execute('SELECT name FROM sqlite_master WHERE type=?;', ('table',))
		tbl_list = [tpl[0] for tpl in cur.fetchall()]
		con.commit()
		if 'attributes' in tbl_list:
			print(f'attributes table already exists in {db}')
			con.close()
			return

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

def rank_col_uniqueness(db, tbl):
	if os.path.exists(db):
		con = sqlite3.connect(db)
		cur = con.cursor()

		# get list of column names in tbl
		cur.execute('pragma table_info(' + tbl + ');')
		table_info = cur.fetchall()
		col_names = [row[1] for row in table_info]

		# print(col_names)

		sorted_col_names = []
		uniq_vals = {}
		for cl in col_names:
			cur.execute('select count(*) from(select distinct ' + cl +
						' from ' + tbl + ');'
					   )
			uniq_vals[cl] = cur.fetchone()[0]
			# print(uniq_vals)
			# Insert column name into sorted_col_names based on how many
			# unique values that column has.
			# As each unique-value-count is generated, it's compared to all
			# counts of columns with higher counts. (can be optimized)

			col_name_len = len(sorted_col_names)
			if col_name_len == 0: sorted_col_names.append(cl)
			else:
				for idx in range(col_name_len):
					if uniq_vals[sorted_col_names[idx]] < uniq_vals[cl]:
						sorted_col_names.insert(idx, cl)
						break
					elif idx == col_name_len - 1:
						sorted_col_names.append(cl)

		# print(uniq_vals)

		# Sorted_col_names is now a list of column names where the
		# unique-value-count corresponding to any name is >= the counts of
		# column names which follow.
		return sorted_col_names
	else:
		sys.exit(f'aborting: database {db} does not exist')

def identify_tbl_key(db, tbl):
	if os.path.exists(db):
		con = sqlite3.connect(db)
		cur = con.cursor()
		cur.execute(f'select count(*) from {tbl};')
		row_count = cur.fetchone()[0]

		# cl_names = rank_col_uniqueness(db, tbl)
		cur.execute('pragma table_info(' + tbl + ');')
		table_info = cur.fetchall()
		cl_names = [row[1] for row in table_info]
		cl_names_len = len(cl_names)
		con.commit()

		key = []
		# for name in cl_names:
		# 	key.append(name)
		# 	cur.execute('select count(*) from(select distinct ' +
		# 				', '.join(key) + f' from {tbl})'
		# 			   )
		# 	if cur.fetchone()[0] == row_count: break
		# 	con.commit()

		for i in range(1, cl_names_len + 1):
			for cand_key in combinations(cl_names, i):
				# print(', '.join(cand_key))
				cur.execute('select count(*) from(select distinct ' +
							', '.join(cand_key) + f' from {tbl})'
						   )
				if cur.fetchone()[0] == row_count:
					key = list(cand_key)
					con.commit()
					break
				con.commit()
			if key != []: break

		return key
	else:
		sys.exit(f'aborting: database {db} does not exist')

def normal_forms(db, k, main_tbl=0):
	if os.path.exists(db):
		con = sqlite3.connect(db)
		cur = con.cursor()
		if main_tbl == 0: main_tbl = db.replace('.db', '')

		match k:
			case 1:
				create_att_table(db, main_tbl)
			case 2:
				cur.execute('SELECT name FROM sqlite_master WHERE type=?;',
							('table',)
						   )
				tbl_list = [tpl[0] for tpl in cur.fetchall()]
				con.commit()

				for tbl in tbl_list:
					print('')
					print(tbl + ':', rank_col_uniqueness(db, tbl))
					key = identify_tbl_key(db, tbl)

					cur.execute('pragma table_info(' + tbl + ');')
					table_info = cur.fetchall()
					cl_names = [row[1] for row in table_info]
					con.commit()
					not_key = [col for col in cl_names if col not in key]

					print(' '*(len(tbl)-len('key')) + 'key:', key)
					print(' '*(len(tbl)-len('not_key')) + 'not_key:', not_key)

					subkeys = {}
					if len(not_key) != 1:
						for col in not_key:
							subkeys[col] = key
							for i in range(1, len(key) + 1):
								for subkey in combinations(key, i):
									sql_cmd = ['select count(*) from(',
												   f'select count(distinct {col})',
												   f' from {tbl} group by ',
												   ', '.join(subkey),
												   ' having count(distinct ',
												   f'{col}) > 1',
											   ');'
											  ]
									sql_cmd = ''.join(sql_cmd)
									# print(sql_cmd)

									cur.execute(sql_cmd)
									con.commit()
									if cur.fetchone()[0] == 0:
										subkeys[col] = list(subkey)
										break
								if subkeys[col] != key:
									print(col, ":", subkeys[col])
									break

					# print(' ' * (len(tbl + ': ') - len('key: ')) + 'key: ', key)

				# get column name list from most to least unique values
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
				"""
				most recent schema

				CREATE TABLE IF NOT EXISTS "ATTRIBUTES_BACKUP"(ID TEXT, Parent TEXT, type TEXT, start INT);
				CREATE TABLE IF NOT EXISTS "SCORES_BACKUP"(
				  source TEXT,
				  start INT,
				  "end" INT,
				  score NUM
				);
				CREATE TABLE IF NOT EXISTS "DM1PCT_BACKUP"(
				  source TEXT,
				  type TEXT,
				  start INT,
				  "end" INT,
				  phase TEXT
				);
				CREATE TABLE IF NOT EXISTS "SEQID_STRAND_BACKUP"(
				  seqid TEXT,
				  type TEXT,
				  start INT,
				  strand TEXT
				);
				CREATE TABLE attributes(ID TEXT, Parent TEXT, type TEXT, start INT);
				CREATE TABLE IF NOT EXISTS "dm1pct"(
				  seqid TEXT,
				  source TEXT,
				  type TEXT,
				  start INT,
				  "end" INT,
				  score NUM,
				  strand TEXT,
				  phase TEXT
				);
				"""
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
# main_table = "dm1pct"

# create_att_table(dbname, table)

normal_forms(dbname, 1)
normal_forms(dbname, 2)
# tbl = "attributes"



# print(rank_col_uniqueness(dbname, main_table))

