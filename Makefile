backup:
	pg_dump dyzurmajster3 > dump-dyzurmajster3-`date +%F-%T`.sql
