from fastapi import FastAPI, Query

app = FastAPI()


@app.get("/")
def root():
    return {"message": "YouTube Transcript API is up and running!"}
