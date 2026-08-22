import os

from aiohttp import web


async def handle_ping(request):
    return web.Response(text="Mizi está viva.")


async def start_keep_alive_server():
    app = web.Application()
    app.router.add_get("/", handle_ping)

    runner = web.AppRunner(app)
    await runner.setup()

    port = int(os.getenv("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

    print(f"Servidor keep-alive escuchando en el puerto {port}")