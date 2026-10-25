import sys
from loguru import logger
from ..config import settings


def setup_logger():
    """Configure loguru logging format and output destinations."""
    logger.remove()
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )
    logger.add(sys.stdout, format=log_format, level=settings.log_level)
    
    # Also log to file
    log_file = settings.base_dir / "logs" / "taobao_crawler_{time:YYYY-MM-DD}.log"
    logger.add(str(log_file), rotation="10 MB", retention="7 days", level="DEBUG", encoding="utf-8")
    return logger
