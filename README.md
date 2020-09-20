# crc
Corpus Resource Coordinator work

## Fall 2020

### CQP reddit 2018 July to 2020 September

- Rebuild the corpus
	1. Save the page https://www.reddit.com/r/ListOfSubreddits/wiki/listofsubreddits in ./CQP/reddit/ to get a list of subreddits
	2. Install [Perl](https://www.perl.org/get.html)
	3. Download [TreeTagger](https://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/) in ./CQP/reddit/ttagger
	4. `pip install requirements.txt `
	5. run `process.sh`