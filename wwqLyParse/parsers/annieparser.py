#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# author wwqgtxx <wwqgtxx@gmail.com>


import urllib.request, io, os, sys, json, re, math, subprocess, traceback, logging, sysconfig

try:
    from ..common import *
except Exception as e:
    from common import *

__MODULE_CLASS_NAMES__ = ["AnnieParser"]
try:
    try:
        from . import yougetparser
    except Exception as e:
        import yougetparser


    class AnnieParser(yougetparser.YouGetParser):

        un_supports = yougetparser.YouGetParser.un_supports  # + ['www.iqiyi.com']
        bin = None
        name = "Annie解析"

        def _get_py_bin(self):
            if sysconfig.get_platform() == "win-amd64":
                py_bin = get_real_path('./annie/annie64.exe')
            else:
                py_bin = get_real_path('./annie/annie32.exe')
            return py_bin

        def _make_arg(self, url, _format=None, use_info=False, password=None, *k, **kk):
            # arg = self._make_proxy_arg()
            arg = []
            # NOTE ignore __default__ format
            if _format and (_format != '__default__'):
                arg += ['-f', _format]
                arg += ['-j', url]
            else:
                if use_info:
                    arg += ['-i', url]
                else:
                    arg += ['-j', url]
            return arg

        # try parse json
        def _try_parse_json(self, raw_text):
            if "annie doesn't support this URL right now, but it will try to download it directly" in raw_text:
                return {}
            return super(AnnieParser, self)._try_parse_json(raw_text)

        def _try_parse_info(self, raw_text):
            """
    type1:
    ```
 Site:      哔哩哔哩 bilibili.com
 Title:     【莓机会了】甜到虐哭的13集单集MAD「我现在什么都不想干,更不想看14集」
 Type:      video
 Streams:   # All available quality
     [64]  -------------------
     Quality:         高清 720P
     Size:            36.34 MiB (38103214 Bytes)
     # download with: annie -f 64 "URL"

     [default]  -------------------
     Quality:         高清 1080P
     Size:            51.88 MiB (54403767 Bytes)
     # download with: annie -f default "URL"

     [15]  -------------------
     Quality:         流畅 360P
     Size:            7.33 MiB (7686124 Bytes)
     # download with: annie -f 15 "URL"

     [32]  -------------------
     Quality:         清晰 480P
     Size:            19.09 MiB (20015712 Bytes)
     # download with: annie -f 32 "URL"
    ```
            :param raw_text:
            :return:
            """
            if "annie doesn't support this URL right now, but it will try to download it directly" in raw_text:
                return {}
            data_array = raw_text.splitlines()
            info = {"site": "", "title": "", "streams": {}}
            last_format_dict = None
            for item in data_array:
                item = str(item.strip()).lower()
                if not item:
                    continue
                site = self._get_item_from_str(item, "site:")
                if site:
                    info["site"] = site
                title = self._get_item_from_str(item, "title:")
                if title:
                    info["title"] = title
                format = self._get_item_from_str(item, "[")
                if format:
                    format = format.split(']')[0]
                    last_format_dict = {
                        "container": "",
                        "video_profile": "",
                        "size": ""
                    }
                    info["streams"][format] = last_format_dict
                container = self._get_item_from_str(item, "container:")
                if container:
                    last_format_dict["container"] = container
                video_profile = self._get_item_from_str(item, "quality:")
                if video_profile:
                    last_format_dict["video_profile"] = video_profile
                size = self._get_item_from_str(item, "size:")
                if size:
                    size_array = size.split("(", 1)
                    if len(size_array) == 2:
                        size = size_array[1].strip(" bytes)")
                        try:
                            size = int(size)
                        except ValueError:
                            pass
                    last_format_dict["size"] = size
            logging.info(info)
            return info

        # parse for parse_url
        def _parse_parse_url(self, raw, _format):
            stream = raw['Formats'].get(_format, None)
            if stream is None:
                for item in raw['Formats'].keys():
                    if str(item).lower() == str(_format).lower():
                        stream = raw['Formats'][item]
            urls = stream['URLs']
            out = []
            for u in urls:
                one = {'protocol': 'http', 'args': {}, 'urls': u['URL']}
                out.append(one)
            return out

        def _parse_parse(self, raw):
            out = {'type': 'formats', 'name': raw['Title'] + '_' + raw['Site'], 'data': []}
            stream = []
            for _format, s in raw['Formats'].items():
                s['_format'] = _format
                s['video_profile'] = s['Quality']
                s['size'] = s['Size']
                s['container'] = ""
                stream.append(s)
            # sort stream by size
            try:
                stream.sort(key=lambda x: x['Size'], reverse=False)
            except KeyError:
                pass
            for i in range(len(stream)):
                stream[i]['_id'] = i
            try:
                stream.sort(key=lambda x: x['Size'], reverse=True)
            except KeyError:
                pass

            # process each stream
            for s in stream:
                one = {}
                label, code, size, ext = self._make_label(s)
                one['label'] = label
                one['code'] = code
                one['ext'] = ext
                one['size'] = size
                try:
                    download = self._parse_parse_url(raw, s['_format'])
                    one['download'] = download
                except KeyError:
                    pass
                out['data'].append(one)
            out["caption"] = self.name
            out['sorted'] = True
            return out

        def parse(self, url, *k, **kk):
            out = self._parse(url, *k, **kk)
            if "bilibili" in url:
                for item in out['data']:
                    if isinstance(item, dict):
                        download = item.get("download", None)
                        if download:
                            for item2 in download:
                                if isinstance(item2, dict):
                                    args = item2.get("args", None)
                                    if args and isinstance(args, dict):
                                        referer = args.get('Referer', None)
                                        if not referer:
                                            args['Referer'] = url
                                    else:
                                        item2["args"] = {'Referer': url}
            return out

        def parse_url(self, url, label, min=None, max=None, *k, **kk):
            out = self._parse_url(url, label, min, max, *k, **kk)
            if "iqiyi" in url:
                for item in out:
                    item["unfixIp"] = True
            if "bilibili" in url:
                for item in out:
                    if isinstance(item, dict):
                        args = item.get("args", None)
                        if args and isinstance(args, dict):
                            referer = args.get('Referer', None)
                            if not referer:
                                args['Referer'] = url
                        else:
                            item["args"] = {'Referer': url}
            return out

        def get_version(self):
            try:
                stdout, stderr = self._run(['-v'], False)
                return stdout.split(',')[0]
            except Exception as e:
                logging.exception("get version error")
            return ""

except:
    logging.exception("can't load yougetparser.py,it need to be super class")
    __MODULE_CLASS_NAMES__ = []
