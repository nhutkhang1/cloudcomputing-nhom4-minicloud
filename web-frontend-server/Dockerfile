# Serve the static website and blog with Nginx.
# Run nginx-prometheus-exporter to expose metrics on port 80 at /metrics.
FROM nginx/nginx-prometheus-exporter:1.5.3 AS exporter

FROM nginx:stable-alpine
RUN rm -f /etc/nginx/conf.d/default.conf
COPY --from=exporter /usr/bin/nginx-prometheus-exporter /usr/local/bin/nginx-prometheus-exporter
COPY conf.default /etc/nginx/conf.d/default.conf
COPY 40-metrics-exporter.sh /docker-entrypoint.d/40-metrics-exporter.sh
COPY html/ /usr/share/nginx/html/
RUN chmod -R 755 /usr/share/nginx/html \
 && chmod +x /docker-entrypoint.d/40-metrics-exporter.sh
EXPOSE 80
CMD ["nginx","-g","daemon off;"]
