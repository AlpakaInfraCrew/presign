# <div align="center">🦙 presign ✍️</div>

> **<div align="center">singup software for alpaca and other fluffy animals</div>**

## Installation (Docker)

We provide a dockerfile for easy setup. To build it, run

```shell
docker build -f image/Dockerfile -t presign:latest .
```

Now copy `docker_env.example` to `docker_env` and change the settings.
After that you can start the image by running

```shell
mkdir data_volume
docker run -it -p 8002:8000 --env-file docker_env --mount type=bind,source="$(pwd)"/data_volume,target=/app/data presign:latest
```

Now access `http://localhost:8002/control` with the superuser credentials specifies in `docker_env`

## Installation (Manual)

Install python and typescript (`tsc`). Then run

```shell
poetry install
```

to install the python dependencies

## License

<!--Presign is published under a [TODO] license.-->

The files `presign/base/static/Server_says_no.gif` and `presign/base/static/Server_says_no.png` are CC-BY-SA 4.0 lavalaempchen.

Parts of the code in this repository are taken from / based on other projects. Their licenses apply to the relevant parts of the code. The parts from other projects are:

- `presign/static/vendored` contains files vendored from other projects. They are licensed under the terms written in the `LICENSE` or `LICENSE.md` in the respective directory.
- Some files in `presign/base/templates/mail/` are based on the [Cerberus fluid template](https://github.com/TedGoas/Cerberus/blob/main/cerberus-fluid.html). These files contain a line marking them as such
