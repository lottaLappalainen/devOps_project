FROM nginx:1.27-alpine

RUN apk update && apk add --no-cache apache2-utils bash python3 py3-pip

COPY nginx.conf /etc/nginx/nginx.conf
COPY conf.d /etc/nginx/conf.d

COPY version.conf /etc/nginx/version.conf

COPY html /usr/share/nginx/html

RUN htpasswd -bc /etc/nginx/.htpasswd admin 1234

COPY switch.sh /switch.sh
COPY discard.sh /discard.sh
RUN chmod +x /switch.sh /discard.sh

COPY control.py /control.py
RUN chmod +x /control.py

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]
