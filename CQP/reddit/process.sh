# > out/RC_*.sgml
# python get_reddit.py

# generate metadata
# python gen_meta.py

# out/RC_*.sgml > processed_reddit/RC_*.sgml
# python postprocess.py

# processed_reddit/RC_*.sgml > final_reddit/RC_*_ss.sgml
INFILE_DIR="data/processed_reddit"
for FILE in $INFILE_DIR/*.sgml;
do
	FILENAME=${FILE##*/};
	FILENAME=${FILENAME%.*};
	echo "Process ${FILENAME} ...";
	OUT_DIR="data/final_reddit/${FILENAME}_ss.sgml";
	# echo $FILE;
	# echo $OUT_DIR;
	perl ssplit.pl -s SENT $FILE > $OUT_DIR;
done

#python merge.py