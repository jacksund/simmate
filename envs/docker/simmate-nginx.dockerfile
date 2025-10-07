
FROM public.ecr.aws/nginx/nginx:stable-alpine

# Replace the default configuration file with our own
RUN rm /etc/nginx/conf.d/default.conf
COPY envs/configs/nginx.conf /etc/nginx/conf.d

# NOTE: the static files that we need to serve are
# made in 'web_server.dockerfile' and passed to this
# image via a volume. The connection is made inside
# the docker-compose.yml
