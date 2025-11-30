# Rudimentary Backup Utility for Portainer

Will make a backup with the following data:

- A backup file using Portainer's own snapshot feature
- A folder for each endpoint/environment:
  - A `volumes.json` for each endpoint (if there are any volumes defined)
  - A `stacks` folder for each endpoint (if there are any stacks defined)
    - A folder for each stack
      - The `docker-compose.yml` for the stack
      - A `.env` file of the environment variables (if any are set)

## CLI Usage

```shell
> python -m rbu4p [-?] [-V] [-v] [-u URL] [-t TOKEN] [-d FILEPATH] [-a {,bztar,gztar,tar,xztar,zip}] [-k] [-f]
```

| Argument                  | Env var                 | Argument | Description                                                                                                                            |
| ------------------------- | ----------------------- | :------: | -------------------------------------------------------------------------------------------------------------------------------------- |
| `--help`                  |                         |          | Show the help message and exit                                                                                                         |
| `--version`, `-V`         |                         |          | Show the program's version number and exit                                                                                             |
| `--verbose`, `-v`         |                         |          | Verbosity. Pass once for error/warnings, twice for info, three times for debugging just rbu4p, four times for debugging everything     |
| `--url`, `-u`             | `RBU4P_URL`             |  string  | **Required.** Portainer API URL                                                                                                        |
| `--token`, `-t`           | `RBU4P_TOKEN`           |  string  | **Required.** Portainer access token                                                                                                   |
| `--destination`, `-d`     | `RBU4P_DESTINATION`     |  string  | **Required.** Destination output (without file suffix)                                                                                 |
| `--archive`, `-a`         | `RBU4P_ARCHIVE`         |  string  | Archive format (or none/empty string for a folder). Typical values are bztar, gztar, tar, xztar, and zip                               |
| `--insecure`, `-k`        | `RBU4P_INSECURE`        | boolean  | Allow insecure server connections                                                                                                      |
| `--force`, `-f`           | `RBU4P_FORCE`           | boolean  | Whether to overwrite the destination file/folder. If unset, the default is to ask if in an interactive terminal, and to fail otherwise |
| `--on-bad-endpoint`, `-e` | `RBU4P_ON_BAD_ENDPOINT` |  string  | When encountering a bad endpoint, choose whether to `skip` it or `halt` entirely. Default is `skip`.                                   |

## Real-world usage

This can be included as part of a docker compose, using a cronjob for periodic backup.

_TODO: Include an example_
