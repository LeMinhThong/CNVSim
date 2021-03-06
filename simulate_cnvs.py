from __future__ import print_function
import argparse
import random
import sys
import os
import time

def reference(filename, chr):
	"""
		Input:
			filename: the name of reference genome fasta file
			chr: name of the chromosome
		Output: 
			list of strings for the given chromosome.
	"""
	out = []
	ref = open(filename)
	count = 0
	print("Copying chromesome {} from {}".format(chr, filename))
	while True:
		count += 1
		if count % 10000000 == 0:
			print("\treading line {:10} ...".format(count))
		line = ref.readline().strip()
		if line == '>' + chr or line == '':
			break
	if len(line) == 0:
		return []
	while True:
		count += 1
		if count % 10000000 == 0:
			print("\tReading line {} ...".format(count))
		line = ref.readline().strip()
		if line.startswith('>') or line == '':
			break
		out.append(line)
	print("Completed. There are {} lines in chromosome {}.".format(len(out), chr))
	return out

def outfile_fa(filename, ref1, ref2):
	"""
		filename: String  -> the output fasta filename
		ref1, ref2: list of String
	"""
	f = open(filename, 'w')
	f.write('>chr1_1\n')
	size1 = len(ref1)
	for i in range(size1):
		if (i+1)%1000000 == 0:
			print("Writing [{}/{}] ref1 to output fasta.".format(i+1, size1))
		f.write(ref1[i]+'\n')
	f.write('>chr1_2\n')
	size2 = len(ref2)
	for i in range(size2):
		if (i+1)%1000000 == 0:
			print("Writing [{}/{}] ref2 to output fasta.".format(i+1, size2))
		f.write(ref2[i]+'\n')
	f.close()

def outfile_pos(filename, SVs, ref_line_length):
	"""
		filename: String -> name of the output file for positions of SVs
		SV: list of breakpoints
		ref_line_segment: int -> number character per line in ref_genome fasta files
	"""
	f = open(filename, 'w')
	L = ref_line_length
	for cnv in SVs:
		ploidy = "Homogeneous" if cnv.isHomogeneous else "Heterozygous"
		if cnv.svtype == 'del':
			cnv_type = "deletion"
		elif cnv.svtype == 'inv':
			cnv_type = "inversion"
		else:
			if cnv.end - cnv.start == cnv.jump_length:
				cnv_type = "tandem repeat"
			elif cnv.isInvert:
				cnv_type = "inverted duplication"
			else:
				cnv_type = "interspersed duplication"
		f.write("chr1    {:12}    {:12}    {:5}    ".format(cnv.start*L, cnv.end*L, L*(cnv.end - cnv.start)))
		f.write("type= {}     {:12}     isInvert= {:5}     jump_length= {:6}    {}\n".format(cnv.svtype, ploidy, cnv.isInvert, cnv.jump_length*L, cnv_type))
	f.close()


class CNV:
	""" Copy number variations: deletion, inversion, tandem repeat, inverted duplication, interspersed duplication"""
	def __init__(self, start, end, isHomogeneous, svtype, isInvert=False, jump_length=0):
		self.start = start
		self.end = end
		self.svtype = svtype  # 'del', 'inv', 'dup'
		self.isInvert = isInvert
		self.jump_length = jump_length # if = +-(end - start), it is tandem repeat, if positive, the duplication is on the right (start + jump),if negative, (start+jump)
		self.isHomogeneous = isHomogeneous

def quality(ref):
	size = len(ref) * len(ref[0])
	Ncount = sum([line.count('N') + line.count('n') for line in ref])
	return 1.0 - 1.0 * Ncount / size

# randomly generated 'num_cnv' SVs
def generate_cnv(ref, num_cnv=1000):
	svtype = ['del', 'inv', 'invDup', 'interDup', 'tandem']
	svtypes = [(random.choice(svtype), random.randint(10, 200)) for _ in range(num_cnv)]
	ref_size = len(ref)
	bin_size = ref_size//num_cnv
	print("bin_size is {}".format(bin_size))
	offset = 1000
	start_positions = [random.randint(i*bin_size + offset, (i+1)*bin_size - offset) for i in range(num_cnv)]
	SVs = []
	for i in range(num_cnv):
		t, n = svtypes[i]
		l = start_positions[i]
		r = l + n
		isHomogeneous = random.choice([True, False])
		if quality(ref[l:r]) < 0.9:
			continue
		if t == 'del':
			SVs.append(CNV(l, r, isHomogeneous, t))
		elif t == 'inv':
			SVs.append(CNV(l, r, isHomogeneous, t, True, 0))
		elif t == 'invDup':
			side = random.choice([-1,1])
			jump_length = side * ((r-l) + random.randint(100, 1000))
			SVs.append(CNV(l, r, isHomogeneous, 'dup', True, jump_length))
		elif t == 'interDup':
			side = random.choice([-1,1])
			jump_length = side * ((r-l) + random.randint(100, 1000))
			SVs.append(CNV(l, r, isHomogeneous, 'dup', False, jump_length))
		elif t == 'tandem':
			jump_length = (r-l)
			SVs.append(CNV(l, r, isHomogeneous, 'dup', False, jump_length))
	print("Number of SVs actually simulated: {}".format(len(SVs)))
	return SVs

# how many SVs for each type?
def generate_cnv_specific(ref,deleltion=500,inversion=250,invdup=250,interdup=250,tandem=250):
	svtype = ['del', 'inv', 'invDup', 'interDup', 'tandem']
	svtype = deleltion * ['del'] + inversion * ['inv'] + invdup * ['invDup'] + interdup * ['interDup'] + tandem * ['tandem']
	num_cnv = len(svtype)
	#random.shuffle(svtype)  
	#svtypes = [(random.choice(svtype), random.randint(10, 200)) for _ in range(num_cnv)]
	svtypes = [(svtype[i], random.randint(10, 200)) for i in range(num_cnv)]
	random.shuffle(svtypes)
	SV_del = []
	SV_inv = []
	SV_invDup = []
	SV_interDup = []
	SV_tandem = []
	ref_size = len(ref)
	bin_size = ref_size//num_cnv
	print("bin_size is {} ".format(bin_size))
	offset = 1200
	start_positions = [random.randint(i*bin_size + offset, (i+1)*bin_size - 200 - offset) for i in range(num_cnv)]
	random.shuffle(start_positions)
	for i in range(num_cnv):
		t, n = svtypes[i]
		#l = random.randint(i*bin_size + offset, (i+1)*bin_size - 200 - offset)
		l = start_positions[i]
		r = l + n
		isHomogeneous = random.choice([True, False])
		print("quality {}. SV {} is {}".format(i, t, quality(ref[l:r])))
		if quality(ref[l:r]) < 0.9:
			continue
		if t == 'del' and len(SV_del) < 400:
			SV_del.append(CNV(l, r, isHomogeneous, t))
		elif t == 'inv' and len(SV_inv) < 200:
			SV_inv.append(CNV(l, r, isHomogeneous, t, True, 0))
		elif t == 'invDup' and len(SV_invDup) < 200:
			side = random.choice([-1,1])
			jump_length = side * ((r-l) + random.randint(100, 1000))
			SV_invDup.append(CNV(l, r, isHomogeneous, 'dup', True, jump_length))
		elif t == 'interDup' and len(SV_interDup) < 200:
			side = random.choice([-1,1])
			jump_length = side * ((r-l) + random.randint(100, 1000))
			SV_interDup.append(CNV(l, r, isHomogeneous, 'dup', False, jump_length))
		elif t == 'tandem' and len(SV_tandem) < 200:
			jump_length = (r-l)
			SV_tandem.append(CNV(l, r, isHomogeneous, 'dup', False, jump_length))
	print("Number of SVs actually simulated: del {} inv {} invDup {} interDup {} tandem {}".format(len(SV_del), len(SV_inv), len(SV_invDup), len(SV_interDup), len(SV_tandem)))
	SVs = SV_del + SV_inv + SV_invDup + SV_interDup + SV_tandem
	SVs.sort(key = lambda cnv: cnv.start)
	return SVs

def generate_fa(ref, SVs):
	ref1 = []
	ref2 = []
	ref_size = len(ref)
	previous = 0
	for i, cnv in enumerate(SVs):
		left = min(cnv.start, cnv.start + cnv.jump_length)
		right = max(cnv.end, cnv.start + cnv.jump_length)
		ref1.extend(ref[previous:left])
		ref2.extend(ref[previous:left])
		def flip(c):
			if c.upper() == 'A':
				return 'T'
			elif c.upper() == 'T':
				return 'A'
			elif c.upper() == 'G':
				return 'C'
			elif c.upper() == 'C':
				return 'G'
			else:
				return c
		invert = lambda x: "".join([flip(c) for c in x][::-1])
		if cnv.svtype == 'del':
			change = []
		elif cnv.svtype == 'inv':
			change = [invert(line) for line in ref[cnv.start:cnv.end][::-1]]
		else:
			if cnv.jump_length == cnv.end - cnv.start:
				change = ref[cnv.start:cnv.end] * 2
			elif cnv.isInvert:
				if cnv.jump_length < 0:
					change = [invert(line) for line in ref[cnv.start:cnv.end][::-1]]
					change.extend(ref[left:cnv.end])
				else:
					change = ref[cnv.start:right]
					change.extend([invert(line) for line in ref[cnv.start:cnv.end][::-1]])
			else:
				if cnv.jump_length < 0:
					change = ref[cnv.start:cnv.end]
					change.extend(ref[left:cnv.end])
				else:
					change = ref[cnv.start:right]
					change.extend(ref[cnv.start:cnv.end])
		if cnv.isHomogeneous:
			ref1.extend(change)
			ref2.extend(change)
		else:
			ref1.extend(change)
			ref2.extend(ref[left:right])
		previous = right
	print("Finished generating the donor genome. Two copies of ref was generated. If cnv is heterozygous, only ref1 contains that cnv. If cnv is homogeneous, both ref1 and ref2 contain that cnv. \nref1 size: {}\nref2 size: {}".format(len(ref1), len(ref2)))
	return ref1, ref2
		
		
def build_bam_file(ref, fasta, basename, coverage):
	# gerenate fq files
	num_reads = 1000000*coverage
	fastq1 = basename + "_1.fq"
	fastq2 = basename + "_2.fq"
	command =  "wgsim/wgsim -d400 -N{} -1100 -2100 {} {} {}".format(num_reads, fasta, fastq1, fastq2)
	os.system(command)
	
	# generate sam file
	samfile = basename + "_{}x.sam".format(coverage)
	command = "bwa mem -M -t 20 -R \"@RG\\tID:1\\tPL:ILLUMINA\\tSM:cnv_1000_ref\" {} {} {} > {}".format(ref, fastq1, fastq2, samfile)
	os.system(command)
	
	# generate bam file
	unsorted_bam = basename + "_unsorted.bam"
	command = "samtools view -S -b {} > {}".format(samfile,unsorted_bam)  
	os.system(command)
	command = "samtools sort -o {} {}".format(basename + "_{}x.bam".format(coverage), unsorted_bam)
	os.system(command)
	command = "samtools index {}".format(basename + "_{}x.bam".format(coverage))
	os.system(command)
	os.system("rm {} {} {} {}".format(fastq1, fastq2, unsorted_bam, samfile))

def main():
	parser = argparse.ArgumentParser(description="CNVSim: simulating copy number variations in a exactly one chromesome of the given reference genome. Output is in the BAM file format.")
	parser.add_argument("ref", help="reference genome (fasta file), e.g. hg38.fa")
	parser.add_argument("n", type=int, help="number of variations, e.g. 1200")
	parser.add_argument("c", type=int, help="sequencing coverage, e.g. 10")
	parser.add_argument("--out", help="output directory, default is the current directory", default="./")
	parser.add_argument("--chr", help="name of the chromosome that will contain the CNVs, default = 'chr1'", default='chr1')
	args = parser.parse_args()

	ref = reference(args.ref, args.chr)

	if len(ref) == 0:
		print("There is no chromosome {} in {}".format(args.chr, args.ref))
		return

	ref_line_length = len(ref[0])
	SVs = generate_cnv(ref, args.n)
	ref1, ref2 = generate_fa(ref, SVs)
	print("Writing fasta data to files.")

	basename = args.out + "/cnv_{}".format(args.n)
	fasta = basename + "_ref.fa"
	outfile_fa(fasta, ref1, ref2)
	outfile_pos(basename + "_pos.txt", SVs, ref_line_length)

	build_bam_file(args.ref, fasta, basename, args.c)

if __name__ == '__main__':
	start = time.time()
	main()
	#build_bam_file("/home/fhormozd/thong/ReferenceGenomes/hg37/human_g1k_v37_gatk.fasta", "cnv1200-10x/cnv_1200_ref.fa", "cnv1200-{}x/cnv_1200".format(coverage), coverage)
	end = time.time()
	print("Simulation time: {} seconds".format(end-start))
