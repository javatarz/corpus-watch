from typing import Protocol

from corpus_watch.assets import mf as _mf


class AssetModule(Protocol):
    CODE: str
    NAME: str
    KIND: str


_REGISTRY: dict[str, AssetModule] = {
    _mf.CODE: _mf,
}


def all_asset_classes() -> list[dict[str, str]]:
    return [{"code": m.CODE, "name": m.NAME, "kind": m.KIND} for m in _REGISTRY.values()]
