gff-sql
=======

GFF is text-based format for storing genomic information. Over the years, there
have been multiple flavors. This document focuses on GFF3 and more specifically
how one models genes in GFF3. It is critical that one understands the
relationships among genes, transcripts, exons, introns, coding sequences, and
untranslated regions.

## Genes in GFF3 ##

The following text-graphic displays an example genomic region.

```
          0        100       200       300       400       500       600
genome    |----:----|----:----|----:----|----:----|----:----|----:----|----
tx-1       [___]----[_____====]---------[=========]---------[=====____]
tx-2                   [____==]---------[=====____]
```

- Exons are indicated by square brackets `[]`
- Coding parts of exons have `==` in interior
- Non-coding parts of exons (UTRs) have `__` in interior
- Introns are demarcated wtih `--` symbols

This gene has 2 transcripts, tx-1 and tx-2. tx-1 has 4 exons and 3 introns. The
first exons is completely untranslated. tx-1 has 2 exons and 1 intron. It has a
different transcription start and translation start which lead to a protein in
a different reading frame (hence the different cds end).

GFF3 is officially specified here:
https://github.com/The-Sequence-Ontology/Specifications/blob/master/gff3.md

Here is a quick summary.

1. seqid: generally the name of a chromosome.
2. type: the category of the feature, such as exon or intron
3. source: how the feature was identified (possibly the name of a program)
4. start: a 1-based coordinate
5. end: a coordinate larger than start and less than seqid length
6. score: a numeric value (or `.` for unknown)
7. strand: generally either `+` or `-` (or `.` for unknown)
8. phase: coding sequence offset (or `.` for unknown)
9. attributes: we are focused on ID and Parent

In GFF3, each feature is described on its own line. Intron and UTR features are
often not shown because they can be inferred.

- Introns are always between exons
- Untranslated regions are exon regions before and after coding sequences

```
          0        100       200       300       400       500       600
genome    |----:----|----:----|----:----|----:----|----:----|----:----|----
gene       [                                                          ]
tx-1       [                                                          ]
exon-1-1   [   ]
exon-1-2            [         ]
exon-1-3                                [         ]
exon-1-4                                                    [         ]
intron-1-1      <-->           <------->           <------->
intron-1-2                     <------->
intron-1-3                                         <------->
cds-1-1                   [   ]
cds-1-2                                 [         ]
cds-1-3                                                     [    ]
utr5-1-1   <--->
utr5-1-2            <---->
utr3-1-1                                                          <--->
exon-2-1               [      ]
exon-2-2                                [         ]
intron-2-1                     <------->
cds-2-1                     [ ]
cds-2-2                                 [     ]
utr5-2-1                <-->
utr3-2-1                                       <-->
```

A GFF3 representation of this genomic region would look similar to this:

```
chr1  gene  korf   10  600  .  +  .  ID=gene-X
chr1  mRNA  korf   10  600  .  +  .  ID=tx-1;Parent=gene-x
chr1  exon  korf   10   50  .  +  .  Parent=tx-1
chr1  exon  korf  100  200  .  +  .  Parent=tx-1
chr1  exon  korf  300  400  .  +  .  Parent=tx-1
chr1  exon  korf  500  600  .  +  .  Parent=tx-1
chr1  cds   korf  150  200  .  +  .  Parent=tx-1
chr1  cds   korf  300  400  .  +  .  Parent=tx-1
chr1  cds   korf  500  550  .  +  .  Parent=tx-1
chr1  mRNA  korf  130  400  .  +  .  ID=tx-2;Parent=gene-x
chr1  exon  korf  130  200  .  +  .  Parent=tx-2
chr1  exon  korf  300  400  .  +  .  Parent=tx-2
chr1  cds   korf  180  200  .  +  .  Parent=tx-2
chr1  cds   korf  300  370  .  +  .  Parent=tx-2
```

Genes are hierarchical entities. In GFF3, these relationships are indicated by
`ID=` and `Parent=` attributes.

- Genes contain transcripts
	- The start of a gene is the left-most transcript start
	- The end of a gene is the right-most transcript end
- mRNAs contain exons and coding sequences
	- The start of a transcript is the left-most exon start
	- The end of a transcript is the right-most exon end
	- Coding sequences are regions that code for protein

Note that introns and untranslated regions may not defined in the GFF but are
implicitly defined by exon and cds boundaries.

- tx-1 has introns at: 51-99, 201-299, 401-499
- tx-1 has 5'UTRs at: 10-50, 100-149
- tx-1 has a 3'UTR: 551-600
- tx-2 has an intron at: 201-299
- tx-2 has a 5'UTR at: 130-179
- tx-2 has a 3'UTR at: 371-400

## Genes in hierarchical formats ##

Some file formats are naturally hierarchical, such as JSON, YAML, or XML. These
file formats fit genes naturally. Below is one possible JSON representation of
the GFF above. Here, a genome object contains chromosome objects which contain
gene objects which contain mRNA objects which contain things like exons and
CDS.

```json
{
	"chromosomes": {
		"chr1": {
			"gene-x": {
				"start": 10,
				"end": 600,
				"strand": "+",
				"score": ".",
				"mRNAs": {
					"tx-1": {
						"start": 10,
						"end": 600,
						"strand": "+",
						"score": ".",
						"exons": [
							{"start": 10, "end": 50},
							{"start": 100, "end": 200},
							{"start": 300, "end": 400},
							{"start": 500, "end": 600}
						],
						"cds": [
							{"start": 150, "end": 200},
							{"start": 300, "end": 400},
							{"start": 500, "end": 550}
						]
					},
					"tx-2": {
						"start": 130,
						"end": 400,
						"strand": "+",
						"score": ".",
						"exons": [
							{"start": 130, "end": 200},
							{"start": 300, "end": 400}
						],
						"cds": [
							{"start": 180, "end": 200},
							{"start": 300, "end": 370}
						]
					]
				}
			}
		}
	}
}

```

## Genes in SQL - Denormalized ##

The simplest way to store hierarchical gene data in a relational database is to
store it in a single table, with no relationships. Historically, relational
database management systems (RDBMS) required one to specify the type of data
for each column. My favorite RDBMS is SQLite, and it doesn't require specifying
the columns, so I won't bother. This is a valid SQLite table schema.

```sql
CREATE TABLE feature(
	seqid,   -- chromosome name
	source,  -- free text
	type,    -- should match Sequence Ontology vocabulary
	beg,     -- int >= 1, I like to use "beg" rather than "start"
	end,     -- int >= beg
	score,   -- float or "."
	strand,  -- "+", "-", or "."
	phase,   -- 0, 1, 2, or "."
	fid,     -- feature id maps to ID=
	pid      -- parent id maps to Parent=
);
```

One can insert GFF3 line-by-line into this schema like this:

```sql
insert into feature values("chr1", "korf", "gene", 10, 600, ".", "+", ".", "gene-x", NULL);
insert into feature values("chr1", "korf", "mRNA", 10, 600, ".", "+", ".", "tx-1", "gene-X');
/* etc */
```

The problem is that getting genes out of the database requires some knowledge
of how everything is connected. For example, if you wanted to get the protein
sequences encoded by the transcripts for gene-X, you would have to do the
following:

- Get all of the transcripts that match the gene's id
- For each transcript id
	- Get all the cds that match the transcript's id
	- Put all of the cds in correct order
	- Retrieve the sequence for each cds
	- Stitch together the sequence corresponding to each cds
	- Translate the cds into protein

This task requires multiple queries to the database and some work outside SQL
to assemble the cds.

## Genes in SQL - Normalized ##

Seqid Table

| UID | Name |
|:---:|:-----|
| Ch1 | chr1 |

Type Table - is this even needed?

| UID | Name |
|:---:|:-----|
| Ty1 | gene |
| Ty2 | mRNA |
| Ty3 | exon |
| Ty4 | cds  |

Source Table - needs to be added to exon and CDS

| UID | Name     |
|:---:|:---------|
| So1 | korf     |
| So2 | inferred |

GeneID Table

| UID | Name   |
|:---:|:-------|
| Ge1 | gene-x |

TranscriptID Table

| UID | Name   |
|:---:|:-------|
| Tx1 | tx-1   |
| Tx2 | tx-2   |

Exon Table

| UID | Beg | End | S | E | P | Src |
|:---:|----:|----:|:-:|:-:|:-:|:---:|
| Ex1 |  10 |  50 | + | . | . | korf|
| Ex2 | 100 | 200 | + | . | . | korf|
| Ex3 | 300 | 400 | + | . | . | korf|
| Ex4 | 500 | 600 | + | . | . | korf|
| Ex5 | 130 | 200 | + | . | . | korf|

CDS Table

| UID | Beg | End | S | E | P | Src |
|:---:|----:|----:|:-:|:-:|:-:|:---:|
| Cd1 | 150 | 200 | + | . | . | korf|
| Cd2 | 300 | 400 | + | . | . | korf|
| Cd3 | 500 | 550 | + | . | . | korf|
| Cd4 | 180 | 200 | + | . | . | korf|
| Cd5 | 300 | 370 | + | . | . | korf|

Exon Aggregate Table

| EID | Exons | Order |
|:---:|:-----:|:-----:|
| EA1 |  Ex1  |   1   |
| EA1 |  Ex2  |   2   |
| EA1 |  EX3  |   3   |
| EA2 |  Ex5  |   1   |
| EA2 |  EX3  |   2   |

CDS Aggregate Table

| CID | CDSs | Order |
|:---:|:----:|:-----:|
| CA1 | Cd1  |   1   |
| CA1 | Cd2  |   2   |
| CA1 | Cd3  |   3   |
| CA2 | Cd4  |   1   |
| CA2 | Cd5  |   2   |

mRNA Table

| UID | Exons | CDSs |
|:---:|:-----:|:----:|
|  M1 |  EA1  |  CA1 |
|  M2 |  EA2  |  CA2 |

Gene Table

| UID | mRNA  |
|:---:|:-----:|
|  G1 |   M1  |
|  G1 |   M2  |
