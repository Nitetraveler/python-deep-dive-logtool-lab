# logtool

Streaming analysis of Apache/Nginx combined-format access logs (plain or gzip).

    logtool summary data/access.log
    logtool top data/access.log --by path -n 3
    logtool errors data/access.log --min-status 500 -f json
