### gfmodules-nvi-referral-manager

Run the referral manager via:

```bash
$ docker compose up -d
```

Then you can access the referral manager at http://localhost:8511 and the swagger documentation at http://localhost:8511/docs.

URA number can be configured in the app.conf file, which is automatically generated on the first run.


# Docker container builds

There are two ways to build a docker container from this application. The first is the default mode created with:

    make container-build

This will build a docker container that will run its migrations to the database specified in app.conf.

The second mode is a "standalone" mode, where it will not run migrations, and where you must explicitly specify
an app.conf mount.

    make container-build-sa

Both containers only differ in their init script and the default version usually will mount its own local src directory
into the container's /src dir.

    docker run -ti --rm -p 8511:8511 \
      --mount type=bind,source=./app.conf.autopilot,target=/src/app.conf \
      gfmodules-nvi-referral-manager-app 
