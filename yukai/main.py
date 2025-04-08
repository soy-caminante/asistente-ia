import  argparse
import  pathlib
import  sys

from    dataclasses                         import  dataclass
from    indexer.booter                      import  Booter      as IndexerBooter
#--------------------------------------------------------------------------------------------------

@dataclass
class Args:
    system:     str
    cfg_file:   pathlib.Path
#--------------------------------------------------------------------------------------------------

def load_args() -> Args:
    parser = argparse.ArgumentParser(description="YUKAI: Herramienta de indexación de historiales clínicos")
    parser.add_argument('--system',  help='Sistema', choices=['indexer'],   required=True)
    parser.add_argument('--runtime', help='Directorio de ejecución',        required=True)
    pargs = vars(parser.parse_args())

    cfg_file    = pathlib.Path(pargs["runtime"])

    if not cfg_file.exists():
        print("El fichero de configuración no existe")
        sys.exit(-1)

    (cfg_file / "inbox").mkdir(parents=True, exist_ok=True)
    (cfg_file / "consolidated").mkdir(parents=True, exist_ok=True)
    (cfg_file / "indexes").mkdir(parents=True, exist_ok=True)
    (cfg_file / "logs").mkdir(parents=True, exist_ok=True)

    return Args(pargs["system"], cfg_file)
#--------------------------------------------------------------------------------------------------

def main():
    try:
        cmd_args = load_args()
        IndexerBooter().run(cmd_args.cfg_file)
    except Exception as ex:
        print("Error en la línea de comadnos")
        print(ex)
#--------------------------------------------------------------------------------------------------

main()