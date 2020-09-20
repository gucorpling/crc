use Getopt::Std;
binmode STDOUT;

my $usage;
{
$usage = <<"_USAGE_";
usage

ssplit [-s SENT] infile > outfile

_USAGE_
}

%opts = ();
getopts('hps:',\%opts) or die $usage;

if ($opts{h} || (@ARGV != 1)) {
    print $usage;
    exit;
}

if (!($sent_tag = $opts{s})) {
    $sent_tag = "SENT";
}

if ($opts{p}) {
    $sent_toks = 1;
}
else{
    $sent_toks = 0;
}


$sopen = 0;

while($line = <>) {
	

	if ($line =~ m /^[^<].*$/)
	{
		if ($sopen==0) { 
			print "<s>\n";
			$sopen = 1;
		}	
	}

	print $line;
	
		if ($line =~ m /\t$sent_tag/ || ($sent_toks=1 && $line =~ m/^[\.!\?](\t|$)/))
	{
		if ($sopen==1) { 
			print "</s>\n";
			$sopen = 0;
		}	
	}

}

if ($sopen==1) { 
	print "</s>\n";
	$sopen = 0;
}	
