# If you want to use camoufox, do this.
#
# """
# Load Camoufox in Scrapy.
#
# AsyncCamoufox is an async context manager that yields a Browser directly
# , or a persistent BrowserContext when passed persistent_context=True
# and a user_data_dir.
#
# https://github.com/scrapy-plugins/scrapy-playwright/blob/v0.0.48/docs/pluggable-browser-providers.md#example-camoufox
# """
#
# from contextlib import AsyncExitStack
# from scrapy_playwright.handler import Config, PERSISTENT_CONTEXT_PATH_KEY
#
#
# class CamoufoxBrowserProvider:
#     def __init__(self, config: Config) -> None:
#         self.config = config
#         self.stack = AsyncExitStack()
#
#     async def start(self) -> None:
#         pass
#
#     async def launch_browser(self):
#         from camoufox.async_api import AsyncCamoufox
#
#         return await self.stack.enter_async_context(
#             AsyncCamoufox(**self.config.launch_options)
#         )
#
#     async def launch_persistent_context(self, context_kwargs: dict):
#         from camoufox.async_api import AsyncCamoufox
#
#         return await self.stack.enter_async_context(
#             AsyncCamoufox(
#                 persistent_context=True,
#                 user_data_dir=context_kwargs[PERSISTENT_CONTEXT_PATH_KEY],
#                 **self.config.launch_options,
#             )
#         )
#
#     async def close(self) -> None:
#         await self.stack.aclose()
