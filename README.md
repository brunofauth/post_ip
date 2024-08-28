# Description

This CLI app periodically queries for your external IP and uploads it to a 
google drive file, so that you always know your machine's IP, no matter where 
you are and no matter how many times your ISP tries to screw you up, without 
having to pay for a static external IP or some kind of hostname or whatever.


# Configuration

The following environment variables may be used to configure this app:

- `POSTIP_TOKEN`: path to a file containing the oauth2 token. Defaults to:
    - `$XDG_CACHE_HOME/post-ip/token.json` if `$XDG_CACHE_HOME` is set
    - `$HOME/.cache/post-ip/token.json` otherwise

- `POSTIP_LASTIP`: path to a file containing the latest fetched value for your 
  IP address. Defaults to:
    - `$XDG_CACHE_HOME/post-ip/last_ip` if `$XDG_CACHE_HOME` is set
    - `$HOME/.cache/post-ip/last_ip` otherwise

- `POSTIP_CREDENTIALS`: path to a file containing credentials for your instance 
  of this App. You can get credentials 
  [here](https://console.cloud.google.com/apis/credentials) after creating a 
  google cloud app [here](https://console.cloud.google.com/welcome). Defaults 
  to
    - `$XDG_CONFIG_HOME/post-ip/credentials.json` if `$XDG_CONFIG_HOME` is set
    - `$HOME/.config/post-ip/last_ip` otherwise
    - These credentials can, more securely, be supplied through a command 
      passed to the `--credentials_cmd` CLI option (see below).


# CLI options

```sh
usage: poetry run -m post_ip [-h] [-v] [-c CMD]

options:
  -h, --help
        show this help message and exit

  -v, --verbose
        This may be passed up to 2 times, to increase verbosity level

  -c --credentials_command CMD
        Instead of looking at the habitual places, use this command to get credentials
```


# Using a CLI command to securely pass credentials

```sh
# assuming you're using the 'pass' password manager
poetry run -m post_ip \
    -c "pass my_creds/post_ip"
```
