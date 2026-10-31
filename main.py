import uvicorn

from src.config import HOST, PORT, RELOAD

if __name__ == "__main__":
    print(f"\n🚀 DocAgent API -> http://{HOST}:{PORT}  (docs: http://{HOST}:{PORT}/docs)\n")
    uvicorn.run("src.endpoints:app", host=HOST, port=PORT, reload=RELOAD)
