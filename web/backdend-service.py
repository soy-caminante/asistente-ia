from app.backend.ia.retrival    import DocumentRetrivalMngr

def main():
    def log_callback(info):
        print(info)
    mngr = DocumentRetrivalMngr("0001", log_fcn=log_callback)
    mngr.index_documents("/home/caminante/Documentos/proyectos/iA/web/data/src-docs/0001")
#--------------------------------------------------------------------------------------------------

main()
#--------------------------------------------------------------------------------------------------