class _Base:
    _raw_json: dict

    def __init__(self, o: dict, /):
        self._raw_json = o
