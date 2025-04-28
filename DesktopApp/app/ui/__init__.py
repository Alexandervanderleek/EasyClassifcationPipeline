"""
UI Package - User interface components
"""

from app.ui.main_window import MainWindow
from app.ui.setup_tab import SetupTab
from app.ui.collect_tab import CollectTab
from app.ui.train_tab import TrainTab
from app.ui.deploy_tab import DeployTab
from app.ui.devices_tab import DevicesTab
from app.ui.results_tab import ResultsTab

__all__ = [
    'MainWindow',
    'SetupTab',
    'CollectTab',
    'TrainTab',
    'DeployTab',
    'DevicesTab',
    'ResultsTab'
]