import uvicorn

if __name__ == "__main__":
    uvicorn.run("app:app", reload=True, port=8000, host="127.0.0.1")
