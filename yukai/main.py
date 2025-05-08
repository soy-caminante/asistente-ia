import  argparse


from    dataclasses                         import  dataclass
from    ia.iaserver.booter                  import  Booter      as  IAServerBooter
from    indexer.booter                      import  Booter      as  IndexerBooter
from    pmanager.booter                     import  Booter      as  ClientBooter
#--------------------------------------------------------------------------------------------------

@dataclass
class MainArgs:
    system:     str

    def is_web(self):       return self.system  == "web"
    def is_indexer(self):   return self.system  == "indexer"
    def is_cmanager(self):  return self.system  == "clientes"
    def is_iaserver(self):  return self.system  == "iaserver"
#--------------------------------------------------------------------------------------------------

def load_args() -> MainArgs:
    parser = argparse.ArgumentParser(description="YUKAI: Herramienta de atención hospitalaria")
    parser.add_argument('--system', help    = 'Sistema', 
                                    choices = [ 'indexer', 'web', 'clientes', 'iaserver' ],    
                                    required= True)
    args    = parser.parse_known_args()
    pargs   = vars(args[0])
    return MainArgs(pargs["system"])
#--------------------------------------------------------------------------------------------------

def main():
    try:
        cmd_args = load_args()
        if cmd_args.is_web():
            pass
        elif cmd_args.is_indexer():
            IndexerBooter().run()
        elif cmd_args.is_cmanager():
            ClientBooter().run()
        elif cmd_args.is_iaserver():
            IAServerBooter().run()

    except Exception as ex:
        print("Error en la línea de comadnos")
        print(ex)
#--------------------------------------------------------------------------------------------------

main()