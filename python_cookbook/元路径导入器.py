# urlimport.py
import sys
import importlib.abc
import importlib.util
from urllib.request import urlopen
from urllib.error import HTTPError, URLError
from html.parser import HTMLParser

# 调试日志配置
import logging
log = logging.getLogger(__name__)

# 获取给定 URL 中的所有链接
def _get_links(url):
    class LinkParser(HTMLParser):
        def handle_starttag(self, tag, attrs):
            if tag == 'a':
                attrs = dict(attrs)
                links.add(attrs.get('href', '').rstrip('/'))
    links = set()
    try:
        log.debug('从 %s 获取链接' % url)
        u = urlopen(url)
        parser = LinkParser()
        parser.feed(u.read().decode('utf-8'))
    except Exception as e:
        log.debug('无法获取链接: %s' % e)
    log.debug('链接: %r' % links)
    return links

# 定义 URL 元路径查找器，继承自 MetaPathFinder
class UrlMetaFinder(importlib.abc.MetaPathFinder):
    def __init__(self, baseurl):
        self._baseurl = baseurl
        self._links = {}
        self._loaders = {baseurl: UrlModuleLoader(baseurl)}

    def find_spec(self, fullname, path=None, target=None):
        log.debug('查找模块规范: fullname=%r, path=%r', fullname, path)
        if path is None:
            baseurl = self._baseurl
        else:
            if not path[0].startswith(self._baseurl):
                return None
            baseurl = path[0]
        parts = fullname.split('.')
        basename = parts[-1]
        log.debug('查找模块规范: baseurl=%r, basename=%r', baseurl, basename)

        if basename not in self._links:
            self._links[baseurl] = _get_links(baseurl)

        # 检查是否是包
        if basename in self._links[baseurl]:
            log.debug('查找模块规范: 尝试包 %r', fullname)
            fullurl = self._baseurl + '/' + basename
            loader = UrlPackageLoader(fullurl)
            spec = importlib.util.spec_from_loader(fullname, loader, origin=fullurl, is_package=True)
            return spec
        # 检查普通模块
        filename = basename + '.py'
        if filename in self._links[baseurl]:
            log.debug('查找模块规范: 找到模块 %r', fullname)
            loader = self._loaders[baseurl]
            spec = importlib.util.spec_from_loader(fullname, loader, origin=loader.get_filename(fullname))
            return spec
        log.debug('查找模块规范: 未找到 %r', fullname)
        return None

    def invalidate_caches(self):
        log.debug('清除链接缓存')
        self._links.clear()

# 定义 URL 模块加载器，继承自 SourceLoader
class UrlModuleLoader(importlib.abc.SourceLoader):
    def __init__(self, baseurl):
        self._baseurl = baseurl
        self._source_cache = {}

    def get_filename(self, fullname):
        return self._baseurl + '/' + fullname.split('.')[-1] + '.py'

    def get_data(self, path):
        log.debug('获取数据: %r', path)
        try:
            with urlopen(path) as u:
                return u.read()
        except (HTTPError, URLError) as e:
            log.debug('获取数据失败: %s', e)
            raise ImportError(f"无法加载 {path}")

    def get_source(self, fullname):
        filename = self.get_filename(fullname)
        log.debug('加载器: 读取 %r', filename)
        if filename in self._source_cache:
            log.debug('加载器: 已缓存 %r', filename)
            return self._source_cache[filename]
        try:
            source = self.get_data(filename).decode('utf-8')
            log.debug('加载器: %r 已加载', filename)
            self._source_cache[filename] = source
            return source
        except (HTTPError, URLError) as e:
            log.debug('加载器: %r 加载失败. %s', filename, e)
            raise ImportError(f"无法加载 {filename}")

    def get_code(self, fullname):
        src = self.get_source(fullname)
        return compile(src, self.get_filename(fullname), 'exec')

    def create_module(self, spec):
        mod = sys.modules.setdefault(spec.name, importlib.util.module_from_spec(spec))
        mod.__file__ = self.get_filename(spec.name)
        mod.__loader__ = self
        mod.__package__ = spec.name.rpartition('.')[0]
        return mod

    def exec_module(self, module):
        code = self.get_code(module.__spec__.name)
        exec(code, module.__dict__)

    def is_package(self, fullname):
        return False

# 定义 URL 包加载器，继承自 UrlModuleLoader
class UrlPackageLoader(UrlModuleLoader):
    def get_filename(self, fullname):
        return self._baseurl + '/' + '__init__.py'

    def create_module(self, spec):
        mod = super().create_module(spec)
        mod.__path__ = [self._baseurl]
        mod.__package__ = spec.name
        return mod

    def is_package(self, fullname):
        return True

# 定义 URL 路径查找器，继承自 PathEntryFinder
class UrlPathFinder(importlib.abc.PathEntryFinder):
    def __init__(self, baseurl):
        self._links = None
        self._loader = UrlModuleLoader(baseurl)
        self._baseurl = baseurl

    def find_spec(self, fullname, target=None):
        log.debug('查找路径规范: %r', fullname)
        parts = fullname.split('.')
        basename = parts[-1]
        if self._links is None:
            self._links = _get_links(self._baseurl)

        if basename in self._links:
            log.debug('查找路径规范: 尝试包 %r', fullname)
            fullurl = self._baseurl + '/' + basename
            loader = UrlPackageLoader(fullurl)
            spec = importlib.util.spec_from_loader(fullname, loader, origin=fullurl, is_package=True)
            return spec

        filename = basename + '.py'
        if filename in self._links:
            log.debug('查找路径规范: 找到模块 %r', fullname)
            loader = self._loader
            spec = importlib.util.spec_from_loader(fullname, loader, origin=loader.get_filename(fullname))
            return spec
        log.debug('查找路径规范: 未找到 %r', fullname)
        return None

    def invalidate_caches(self):
        log.debug('清除链接缓存')
        self._links = None

# 工具函数：安装和卸载 Meta 查找器
_installed_meta_cache = {}

def install_meta(address):
    if address not in _installed_meta_cache:
        finder = UrlMetaFinder(address)
        _installed_meta_cache[address] = finder
        sys.meta_path.append(finder)
        log.debug('%r 已安装到 sys.meta_path', finder)

def remove_meta(address):
    if address in _installed_meta_cache:
        finder = _installed_meta_cache.pop(address)
        sys.meta_path.remove(finder)
        log.debug('%r 已从 sys.meta_path 移除', finder)

# 检查路径是否是 URL
_url_path_cache = {}

def handle_url(path):
    if path.startswith(('http://', 'https://')):
        log.debug('处理路径? %s. [是]', path)
        if path in _url_path_cache:
            finder = _url_path_cache[path]
        else:
            finder = UrlPathFinder(path)
            _url_path_cache[path] = finder
        return finder
    else:
        log.debug('处理路径? %s. [否]', path)
        return None

def install_path_hook():
    sys.path_hooks.append(handle_url)
    sys.path_importer_cache.clear()
    log.debug('安装 handle_url')

def remove_path_hook():
    sys.path_hooks.remove(handle_url)
    sys.path_importer_cache.clear()
    log.debug('移除 handle_url')