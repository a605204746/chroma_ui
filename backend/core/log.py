import os
import sys

from loguru import logger

from .config import LoggingConfig


def setup_logging(cfg: LoggingConfig) -> None:
    """根据 LoggingConfig 初始化 loguru：控制台 + 轮转文件。"""
    logger.remove()

    logger.level("DEBUG",    color="<dim><white>")
    logger.level("INFO",     color="<bold><cyan>")
    logger.level("SUCCESS",  color="<bold><green>")
    logger.level("WARNING",  color="<bold><yellow>")
    logger.level("ERROR",    color="<bold><red>")
    logger.level("CRITICAL", color="<bold><fg #ff0000>")

    if sys.stderr is not None:
        logger.add(
            sys.stderr,
            level=cfg.level,
            format=(
                "<green>{time:HH:mm:ss}</green> | "
                "<level>{level: <8}</level> | "
                "<cyan>{name}</cyan>:<cyan>{line}</cyan> - "
                "<level>{message}</level>"
            ),
            colorize=True,
        )

    os.makedirs(os.path.dirname(os.path.abspath(cfg.path)), exist_ok=True)
    logger.add(
        cfg.path,
        level=cfg.level,
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{line} - {message}",
        rotation=cfg.rotation,
        retention=cfg.retention,
        encoding="utf-8",
        enqueue=True,
    )
