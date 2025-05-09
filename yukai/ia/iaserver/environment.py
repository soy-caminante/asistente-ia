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
    db_host             : str
    db_user             : str
    db_password         : str
    db_name             : str
    run_db_on_start     : bool
    
    _low_cpu_mem_usage  : bool
    _ia_cache_dir       : pathlib.Path
    _db_docker_file     : pathlib.Path
    _log                : Logger = PrivateAttr(default=None)
    #----------------------------------------------------------------------------------------------
    
    @property
    def log(self): return self._log
    #----------------------------------------------------------------------------------------------

    @property
    def db_docker_file(self):  return self._db_docker_file
    #----------------------------------------------------------------------------------------------

    @property
    def ia_cache_dir(self):  return self._ia_cache_dir
    #----------------------------------------------------------------------------------------------

    @property
    def low_cpu_mem_usage(self): return self._low_cpu_mem_usage
    #----------------------------------------------------------------------------------------------

    class Config:
        extra = "ignore"
    #----------------------------------------------------------------------------------------------

    @model_validator(mode="after")
    def post_init(self) -> Environment:
        (self.runtime / "logs").mkdir(parents=True, exist_ok=True)
        self._log       = Logger().setup("iaserver", self.runtime / "logs", True)

        self._db_docker_file    = self.runtime / f"docker/docker-compose.yml"
        self._ia_cache_dir      = self.runtime / f"cache"

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
            self._low_cpu_mem_usage = True
        else:
            self._low_cpu_mem_usage = False

        if isinstance(self.test, str):
            self.test = self.test.lower() == "on" or self.test.lower() == "true" or self.test.lower() == "enabled"

        return self
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------