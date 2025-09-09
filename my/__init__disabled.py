import os

config_dir = os.environ["XDG_CONFIG_HOME"]
repos_dir = os.environ["REPOS"]

__path__[:] = [
    os.path.join(config_dir, "my", "my"),
    os.path.join(repos_dir, "HPI-personal", "my"),
    os.path.join(repos_dir, "HPI", "my"),
    os.path.join(repos_dir, "HPI-karlicoss", "src", "my"),
]
