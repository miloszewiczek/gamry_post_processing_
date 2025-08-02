import pathlib
import tomllib

def load_toml(filename):
    path = pathlib.Path(__file__).parent / filename
    with path.open(mode='rb') as fp:
        return tomllib.load(fp)

# Load both config and messages
config = load_toml("config.toml")
messages = load_toml("messages.toml")