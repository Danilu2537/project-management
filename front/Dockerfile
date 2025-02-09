FROM node as vite-app

WORKDIR /app/client

COPY package*.json ./

RUN ["npm", "i"]

COPY . .

RUN ["npm", "run", "build"]

FROM nginx:alpine

WORKDIR /usr/share/nginx/

RUN rm -rf html
RUN mkdir html

WORKDIR /

COPY ./nginx.conf /etc/nginx
COPY --from=vite-app ./app/client/dist /usr/share/nginx/html

EXPOSE 80

ENTRYPOINT ["nginx", "-g", "daemon off;"]
