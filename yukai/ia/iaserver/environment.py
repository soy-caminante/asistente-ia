from    __future__                      import  annotations

import  pathlib

from    logger                          import  Logger
from    pydantic                        import  BaseModel, PrivateAttr, model_validator
from    typing                          import  Optional
from    ia.modelloader                  import  Quatization
#--------------------------------------------------------------------------------------------------

class Environment(BaseModel):
    runtime             : pathlib.Path   
    test                : Optional[bool|str] = False
    web_port            : int
    workers_num         : int
    max_requests        : int
    model_name          : str
    quantization        : str|Quatization
    db_port             : int
    db_name             : str
    
    _db_docker_file     : pathlib.Path
    _log                : Logger = PrivateAttr(default=None)
    #----------------------------------------------------------------------------------------------
    
    @property
    def log(self): return self._log
    #----------------------------------------------------------------------------------------------

    @property
    def db_docker_file(self):  return self._db_docker_file
    #----------------------------------------------------------------------------------------------

    class Config:
        extra = "ignore"
    #----------------------------------------------------------------------------------------------

    @model_validator(mode="after")
    def post_init(self) -> Environment:
        (self.runtime / "logs").mkdir(parents=True, exist_ok=True)
        self._log       = Logger().setup("iaserver", self.runtime / "logs", True)

        self._db_docker_file = self.runtime / f"docker/docker-compose.yml"

        if "4b" in self.quantization.lower() or "b4" in self.quantization.lower():
            self.quantization = Quatization.B4
        elif "16" in self.quantization.lower():
            self.quantization = Quatization.FP16
        elif "32" in self.quantization.lower():
            self.quantization = Quatization.FP32
        else:
            raise Exception(f"Quntization no permitida {self.quantization}")
        
        if self.test:
            self.quantization = Quatization.FP32

        if isinstance(self.test, str):
            self.test = self.test.lower() == "on" or self.test.lower() == "true" or self.test.lower() == "enabled"

        return self
    #----------------------------------------------------------------------------------------------

#--------------------------------------------------------------------------------------------------