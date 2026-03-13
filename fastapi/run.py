import builtins
from pydantic import SecretStr
builtins.SecretStr = SecretStr

import uvicorn
import pydantic
import fastapi_mail.config

setattr(fastapi_mail.config, 'SecretStr', SecretStr)

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
