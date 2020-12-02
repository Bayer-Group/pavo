
def init_routes():
    """load all submodules to register routes"""
    import pado_visualize.routes.index
    import pado_visualize.routes.qpzip
    import pado_visualize.routes.seadragon
    import pado_visualize.routes.thumbnail
    import pado_visualize.routes.wsickr
