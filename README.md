# <div align="center">🦙 presign ✍️</div>

> **<div align="center">singup software for alpaca and other fluffy animals</div>**

## Installation (Docker)

### Manual Build

We provide a dockerfile for easy setup. To build it, run

```shell
docker build -f image/Dockerfile -t presign:latest .
```

### Pull from GitHub

```shell
docker pull ghcr.io/alpakainfracrew/presign:main
```

Now copy `docker_env.example` to `docker_env` and change the settings.
After that you can start the image by running

```shell
mkdir data_volume
docker run -it -p 8002:8000 --env-file docker_env --mount type=bind,source="$(pwd)"/data_volume,target=/app/data presign:latest
```

Now access `http://localhost:8002/control` with the superuser credentials specifies in `docker_env`

### SystemD Unit

The file `pretix.service` can be moved to `/etc/systemd/system/` to start/stop the presign service via systemd.
**Please change the `<presign directory>` part to your presign location in the systemd file!**

To activate the SystemD Unit run the following commands after placing the file into `/etc/systemd/system/`:

```shell
systemctl daemon-reload
systemctl enable presign.service
systemctl start presign.service
```

## Installation (Manual)

Install python and typescript (`tsc`). Then run

```shell
poetry install
```

to install the python dependencies.

Then run

```shell
poetry run python manage.py import_text_defaults mail_texts.json status_texts.json
```

to import the default texts for mails and status.

Then run

```shell
poetry run python manage.py runserver
```

to start the development server.

## License

Presign is published under an [AGPLv3 license](./LICENSE) with the following exception:

The files `presign/base/static/Server_says_no.gif` and `presign/base/static/Server_says_no.png` are CC-BY-SA 4.0 lavalaempchen.

Parts of the code in this repository are taken from / based on other projects. Their licenses apply to the relevant parts of the code. The parts from other projects are:

- `presign/static/vendored` contains files vendored from other projects. They are licensed under the terms written in the `LICENSE` or `LICENSE.md` in the respective directory.
- Some files in `presign/base/templates/mail/` are based on the [Cerberus fluid template](https://github.com/TedGoas/Cerberus/blob/main/cerberus-fluid.html). These files contain a line marking them as such
