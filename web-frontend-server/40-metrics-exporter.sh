#!/bin/sh
/usr/local/bin/nginx-prometheus-exporter \
  --nginx.scrape-uri=http://127.0.0.1:8088/stub_status \
  --web.listen-address=127.0.0.1:9113 >/dev/null 2>&1 &
