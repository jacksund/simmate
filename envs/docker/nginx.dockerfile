
FROM nginx:stable-alpine

# Replace default config with our custom one
RUN rm /etc/nginx/conf.d/default.conf
COPY envs/configs/nginx.conf /etc/nginx/conf.d

# NOTE: the static files served for the website are made over in the simmate 
# dockerfile and passed to this image via a volume.
