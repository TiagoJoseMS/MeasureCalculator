def classFactory(iface):
    from .main_plugin import MeasureCalculatorPlugin
    return MeasureCalculatorPlugin(iface)