from __future__ import annotations

import enum
import hashlib
import os
import shutil
from collections import OrderedDict
from functools import lru_cache
from pathlib import Path

from filelock import FileLock
from filelock import Timeout as FileLockTimeout
from pado.io.files import urlpathlike_to_fs_and_path
from pado.io.files import urlpathlike_to_string
from pado.types import UrlpathLike

# --- slide caching -----------------------------------------------------------


class CacheState(enum.Enum):
    MISS = enum.auto()
    CACHING = enum.auto()
    HIT = enum.auto


class LocalWholeSlideCache:
    """caches images locally"""

    def __init__(self, root: str | Path, maxsize: int = 100 * 2**30):
        self.root = os.fspath(root)
        os.makedirs(self.root, exist_ok=True)
        self.maxsize = int(maxsize)
        self._mapping: OrderedDict[str, str] = OrderedDict()

    @staticmethod
    def _make_hashable(urlpath: UrlpathLike) -> str | tuple[str, str]:
        if isinstance(urlpath, str):
            return urlpath
        elif isinstance(urlpath, os.PathLike):
            return os.fspath(urlpath)
        else:
            # noinspection PyProtectedMember
            return urlpath.path, urlpath.fs._fs_token

    @staticmethod
    @lru_cache
    def _lhash(urlpath: str | tuple[str, str]) -> str:
        """return a hash from an urlpath (used as base dir)"""
        # note: this needs to be a name that can be created as a directory
        if isinstance(urlpath, tuple):
            pth, fs_token = urlpath
            # noinspection PyProtectedMember
            s = hashlib.sha256(fs_token.encode())
            s.update(pth.encode())
            return s.hexdigest()
        else:
            s_urlpath = urlpathlike_to_string(urlpath).encode()
            return hashlib.sha256(s_urlpath).hexdigest()

    def _llock(self, lhash: str) -> str:
        """return the local lock filename"""
        return f"{os.path.join(self.root, lhash)}.lock"

    def _copy(self, urlpath: UrlpathLike, lhash: str | Path) -> str:
        """copy an urlpath to a local path"""
        fs, path = urlpathlike_to_fs_and_path(urlpath)
        lpath = os.path.join(self.root, lhash, path)

        if not (os.path.isfile(lpath) and os.stat(lpath).st_size == fs.size(path)):
            # todo: speed up for specific fs implementations
            #  - s3: s5cmd maybe
            #  - gs: gsutil with all options?
            fs.get_file(path, lpath)

        return lpath

    def get(self, urlpath: UrlpathLike, *, timeout: float = -1) -> str:
        """return a cached local path for an urlpath"""
        lhash = self._lhash(self._make_hashable(urlpath))
        try:
            lpath = self._mapping[lhash]
        except KeyError:
            lock = self._llock(lhash)
            try:
                with FileLock(lock, timeout=timeout):
                    lpath = self._copy(urlpath, lhash)
                    self._mapping[lhash] = lpath
            except FileLockTimeout:
                raise TimeoutError(lhash)
        else:
            self._mapping.move_to_end(lhash)
        return lpath

    def test(self, urlpath: UrlpathLike) -> CacheState:
        """return if urlpath in cache"""
        lhash = self._lhash(self._make_hashable(urlpath))
        if lhash in self._mapping:
            return CacheState.HIT
        else:
            lock = self._llock(lhash)
            try:
                with FileLock(lock, timeout=0):
                    pass
            except FileLockTimeout:
                return CacheState.CACHING
            else:
                return CacheState.MISS

    @property
    def size(self) -> int:
        """return the current size of the cache"""
        return sum(map(os.path.getsize, self._mapping.values()))

    def enforce_size_limit(self) -> None:
        """remove oldest files until size limit is enforced"""
        if self.maxsize < 0:
            return
        while self.size > self.maxsize:
            lhash, _ = self._mapping.popitem(last=False)
            pth = os.path.join(self.root, lhash)
            shutil.rmtree(pth, ignore_errors=True)
