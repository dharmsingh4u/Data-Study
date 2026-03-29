from fastapi import FastAPI, Path
from typing import Annotated,Optional
from model import chat_class
from chat import workflow
app = FastAPI()
import uvicorn

@app.get("/")
def root():
    return {"message": "Welcome"}

@app.post("/generate_prompt/")

def generate(request :chat_class):
    #if 
    config = {"configurable": {"thread_id": request.thread_id}}
    stage ={'message':request.message}
    result=workflow.invoke(stage,config)
    return {'Result':result['message'][-1].content}
@app.post("/feedback/")
def feedback(request :chat_class):
    #if 
    config = {"configurable": {"thread_id": request.thread_id}}
    #stage ={'message':request.message}
    workflow.update_state(config,values={"feedack": request.feedack,"comment": request.comment})
    result =workflow.invoke(None,config)
    return {'Result':result['message'][-1].content}
#if __name__ == "__main__":
#    uvicorn.run(app, host='0.0.0.0', port=8080)

    