# Сторонние включения в CPython

`Doc/license.rst` (ревизия 9c0cfb141c236c902954841bb6cca407f86e1eeb), §«Licenses and
Acknowledgements for Incorporated Software» (строки 298+): перечислены включённые
компоненты с собственными лицензиями — Mersenne Twister, Sockets, Cookie management,
Execution tracing, UUencode/UUdecode, XML-RPC, test_epoll, Select kqueue, SipHash24,
strtod/dtoa, OpenSSL, expat, libffi, zlib, cfuhash, libmpdec, W3C C14N test suite,
mimalloc, asyncio, GUS, Zstandard bindings, profiling module, Pixi packages,
Unicode Character Database.

Практический вывод для Syllanix: примеры и текст `Doc/tutorial/*` и `Doc/reference/*`,
написанные командой CPython, — PSF-2.0 (совместимо с переработкой при сохранении
уведомления). Данные и код из перечисленных сторонних компонентов **нельзя** брать
без отдельной проверки их лицензии.
