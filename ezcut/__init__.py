try:
    from ._version import version as __version__
except ImportError:
    try:
        from importlib.metadata import version as _version

        __version__ = _version("ezcut")
    except Exception:
        __version__ = "0.0.0-dev"
