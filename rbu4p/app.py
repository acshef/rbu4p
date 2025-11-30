import datetime
import email.message
import json
import logging
import os
import pathlib
import shutil
import tempfile
import typing as t

import requests

from .const import *
from .endpoint import Endpoint
from .stack import Stack
from .util import groupby, is_interactive, str2bool

if t.TYPE_CHECKING:
    from _typeshed import StrOrBytesPath


class RBU4Portainer:
    api_url: str
    archive: t.Optional[str]
    dest: pathlib.Path
    token: str
    verify: t.Optional[bool]
    force: t.Optional[bool]
    on_bad_endpoint: t.Literal["skip", "halt"]

    log = logging.getLogger("rbu4p")

    def __init__(
        self,
        api_url: str,
        token: str,
        dest: "StrOrBytesPath",
        *,
        force: t.Optional[bool] = None,
        archive: t.Optional[str] = None,
        verify: t.Optional[bool] = None,
        on_bad_endpoint: t.Literal["skip", "halt"] = DEFAULT_ON_BAD_ENDPOINT,
    ):
        if archive is not None:
            supported_formats = dict(shutil.get_archive_formats())
            if archive not in supported_formats:
                raise ValueError(f"Unknown output archive format {archive!r}")

        self.api_url = api_url.rstrip("/")
        self.archive = archive
        self.dest = pathlib.Path(dest or f"rbu4p_{int(datetime.datetime.now().timestamp())}")
        self.token = token
        self.verify = verify
        self.force = None if force is None else bool(force)
        self.on_bad_endpoint = on_bad_endpoint

    def __call__(self) -> t.Optional[int]:
        with tempfile.TemporaryDirectory() as tempdir:
            self.write_backup(tempdir)
            _endpoints = self.get_endpoints()
            endpoints_good = list[Endpoint]()
            endpoints_bad = list[Endpoint]()
            for x in sorted(_endpoints, key=lambda x: x.name):
                if x.is_up:
                    endpoints_good.append(x)
                else:
                    endpoints_bad.append(x)

            if endpoints_bad:
                if self.on_bad_endpoint == "skip":
                    self.log.warning(
                        "The following endpoints will be skipped because they're in a bad state: "
                        + ", ".join(repr(x.name) for x in endpoints_bad)
                    )
                else:
                    self.log.critical(
                        "Stopping; the following endpoints are in a bad state: "
                        + ", ".join(repr(x.name) for x in endpoints_bad)
                    )
                    return -1

            lookup = {x.id: x for x in endpoints_good}
            stacks = self.get_stacks()

            for endpoint_id, _stacks in groupby(stacks, key=lambda x: x.endpoint_id):
                if endpoint_id not in lookup:
                    self.log.debug(f"{endpoint_id} not active, skipping")
                    continue

                _stacks = list(_stacks)

                lookup[endpoint_id].stacks = _stacks

            for endpoint in endpoints_good:
                self.log.info(f"Backing up endpoint {endpoint.id}: {endpoint.name}")
                endpoint_dir = pathlib.Path(tempdir, endpoint.name)
                os.makedirs(endpoint_dir)

                volumes = self.get_volumes(endpoint.id)
                self.log.info(f"    {len(volumes)} volume{'' if len(volumes) == 1 else 's'}")
                if volumes.get("Volumes"):
                    with open(endpoint_dir / "volumes.json", "w") as file:
                        json.dump(volumes, file, indent="    ")

                if endpoint.stacks:
                    self.log.info(
                        f"    {len(endpoint.stacks)} stack{'' if len(endpoint.stacks) == 1 else 's'}"
                    )
                    for stack in endpoint.stacks:
                        stack_dir = endpoint_dir / "stacks" / stack.name
                        os.makedirs(stack_dir)
                        with open(stack_dir / "docker-compose.yml", "wt") as file:
                            file.write(self.get_stack_file(stack.id))
                        if stack.env:
                            with open(stack_dir / ".env", "wt") as file:
                                for k, v in stack.env.items():
                                    file.write(f"{k}={v}\n")

            if not self.archive:
                return self.make_output_folder(tempdir)

            return self.make_output_archive(tempdir)

    def make_output_folder(self, tempdir: str):
        self.remove_or_die(self.dest)
        shutil.copytree(tempdir, self.dest)

    def make_output_archive(self, tempdir: str):
        temp_dest = pathlib.Path(tempdir, self.dest.stem)
        archive = shutil.make_archive(temp_dest, self.archive, tempdir, ".")
        archive_name = pathlib.Path(archive).name
        dest = pathlib.Path(self.dest.parent, archive_name)
        self.remove_or_die(dest)
        shutil.move(archive, dest)

    def remove_or_die(self, dest: pathlib.Path, /):
        if dest.exists():
            if self.force is None and is_interactive():
                overwrite = str2bool(input(f"Overwrite {dest}? [y/N]: "))
            else:
                overwrite = bool(self.force)

            if not overwrite:
                raise FileExistsError(str(dest))

            if dest.is_dir():
                shutil.rmtree(dest)
            else:
                os.remove(dest)

    def make_session(self):
        session = requests.Session()
        session.verify = self.verify
        session.headers["X-API-KEY"] = self.token

        return session

    def get_endpoints(self) -> list[Endpoint]:
        with self.make_session() as session:
            resp = session.get(f"{self.api_url}/endpoints")
            resp.raise_for_status()
            endpoints = resp.json()
            return [Endpoint(x) for x in endpoints]

    def get_stacks(self) -> list[Stack]:
        with self.make_session() as session:
            resp = session.get(f"{self.api_url}/stacks")
            resp.raise_for_status()
            stacks = resp.json()
            return [Stack(x) for x in stacks]

    def get_volumes(self, endpoint_id: int) -> dict:
        with self.make_session() as session:
            resp = session.get(f"{self.api_url}/endpoints/{endpoint_id}/docker/volumes")
            resp.raise_for_status()
            volumes = resp.json()
            return volumes

    def get_stack_file(self, stack_id: int) -> str:
        with self.make_session() as session:
            resp = session.get(f"{self.api_url}/stacks/{stack_id}/file")
            resp.raise_for_status()
            return resp.json()["StackFileContent"]

    def make_backup(self, password: str = "") -> requests.Response:
        with self.make_session() as session:
            resp = session.post(f"{self.api_url}/backup", json={"password": password}, stream=True)
            resp.raise_for_status()

            return resp

    def write_backup(self, tempdir: str, password: str = ""):
        resp = self.make_backup(password)
        if resp.headers.get("Content-Type") != "application/x-gzip":
            raise ValueError(f"Unknown backup MIME type {resp.headers.get('Content-Type')!r}")

        backup_name = "backup.tar.gz"
        if content_disposition := resp.headers.get("Content-Disposition"):
            _msg = email.message.EmailMessage()
            _msg["content-type"] = content_disposition
            params = _msg["content-type"].params
            if "filename" in params:
                backup_name = params["filename"]

        with open(pathlib.Path(tempdir, backup_name), "wb") as file:
            for data in resp.iter_content(None):
                file.write(data)
