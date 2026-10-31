# The live server: Ehud Shapiro's GLP repository at a pinned commit, with this
# repository's files (live/overlay) on top, and the site and the app page as
# its web directory.  One process runs every contract's platform on demand.
FROM dart:stable
ARG GLP_COMMIT=fa053838ec04adb433e64f44959bec780a2d9a12
RUN apt-get update && apt-get install -y --no-install-recommends git ca-certificates && rm -rf /var/lib/apt/lists/*
RUN git init /glp && cd /glp \
 && git remote add origin https://github.com/EShapiro2/GLP.git \
 && git fetch --depth 1 origin $GLP_COMMIT && git checkout FETCH_HEAD
COPY live/overlay/ /glp/
COPY index.html data.js /glp/live_server/web/
COPY stack/ /glp/live_server/web/stack/
COPY live/web/ /glp/live_server/web/
WORKDIR /glp/live_server
RUN dart pub get && dart compile exe bin/server.dart -o /glp/live_server/server
ENV GLP_ROOT=/glp PORT=10000
EXPOSE 10000
CMD ["/glp/live_server/server"]
