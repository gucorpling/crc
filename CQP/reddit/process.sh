# > out/RC_*.sgml
mkdir out
python get_reddit.py

# out/RC_*.sgml > processed_reddit/RC_*.sgml
mkdir processed_reddit
python postprocess.py

# processed_reddit/RC_*.sgml > final_reddit/RC_*_ss.sgml
mkdir final_reddit
INFILE_DIR="processed_reddit"
for FILE in $INFILE_DIR/*.sgml;
do
	FILENAME=${FILE##*/};
	FILENAME=${FILENAME%.*};
	echo "Process ${FILENAME} ...";
	OUT_DIR="final_reddit/${FILENAME}_ss.sgml";
	# echo $FILE;
	# echo $OUT_DIR;
	perl ssplit.pl -s SENT $FILE > $OUT_DIR;
done
