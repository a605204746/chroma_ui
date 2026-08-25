from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass
class WindowConfig:
    title: str             = "App"
    icon: str              = ""
    width: int             = 0
    height: int            = 0
    min_width: int         = 200
    min_height: int        = 100
    resizable: bool        = True
    frameless: bool        = False
    easy_drag: bool        = True
    on_top: bool           = False
    confirm_close: bool    = False
    minimized: bool        = False
    maximized: bool        = False
    fullscreen: bool       = False
    background_color: str  = "#FFFFFF"
    transparent: bool      = False
    remember_geometry: bool = True


@dataclass
class DatabaseConfig:
    path: str = "data/app.db"


@dataclass
class LoggingConfig:
    level: str     = "INFO"
    path: str      = "data/logs/app.log"
    rotation: str  = "10 MB"
    retention: str = "7 days"


@dataclass
class AppConfig:
    window:   WindowConfig   = field(default_factory=WindowConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    logging:  LoggingConfig  = field(default_factory=LoggingConfig)

    def __post_init__(self) -> None:
        from .paths import resource, userdata
        if self.logging.path and not os.path.isabs(self.logging.path):
            self.logging.path = userdata(self.logging.path)
        if self.database.path and not os.path.isabs(self.database.path):
            self.database.path = userdata(self.database.path)
        if self.window.icon and not os.path.isabs(self.window.icon):
            self.window.icon = resource(self.window.icon)
