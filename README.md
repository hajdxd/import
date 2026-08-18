# Automated FTP data import

This script automates a "data import", which before was to download a file from an ftp server, unzip, change the... blah blah blah - takes a long time, you have to wait to connect to the ftp servers, its repetitive boring and annoying.

So i automated it :) It even sends an email everyday when the work is done!!!!

this was my first "serious" python script and will forever be one of my favorites 




## What this script does
- Sets up logging — creates a timestamped log file for the run (later archived into a monthly folder, named in Polish).
- Connects to FTP servers — loops through a list of configured brands, each with its own FTP server and file type/extension.
- Finds today's files — lists remote files starting with FA and filters for ones dated today.
- Downloads matching files — pulls each matching file down to a local folder.
- Unpacks ZIPs — extracts .zip downloads, then deletes the original archive.
- Renames & timestamps extracted files — renames extracted .txt files to the brand's target extension and sets their modification date to match the original FTP file date (skips/removes duplicates).
- Moves processed files — places the renamed files into the output folder.
- Sends an email report — after processing all brands, emails a summary (file count, execution time, start/end time) with the log file attached.
- Archives the log — moves the log into a dated monthly subfolder for record-keeping.
