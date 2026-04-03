import importlib.metadata

try:
    __version__ = importlib.metadata.version("ezcut")
except importlib.metadata.PackageNotFoundError:
    __version__ = "0.4.0"
