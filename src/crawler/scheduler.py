"""APScheduler调度器"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class CrawlerScheduler:
    """爬虫调度器"""
    
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.jobs = {}
    
    def add_job(self, job_id: str, func, hours: int = 2):
        """添加一个爬虫任务"""
        trigger = IntervalTrigger(hours=hours)
        self.scheduler.add_job(
            func,
            trigger=trigger,
            id=job_id,
            name=job_id,
            replace_existing=True
        )
        self.jobs[job_id] = {"func": func, "hours": hours, "enabled": True}
        logger.info(f"添加爬虫任务: {job_id}, 间隔: {hours}小时")
    
    def remove_job(self, job_id: str):
        """移除一个爬虫任务"""
        if job_id in self.jobs:
            self.scheduler.remove_job(job_id)
            del self.jobs[job_id]
            logger.info(f"移除爬虫任务: {job_id}")
    
    def start(self):
        """启动调度器"""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("爬虫调度器已启动")
    
    def shutdown(self):
        """关闭调度器"""
        self.scheduler.shutdown()
        logger.info("爬虫调度器已关闭")
    
    def list_jobs(self):
        """列出所有任务"""
        return [
            {"job_id": k, "hours": v["hours"], "enabled": v["enabled"]}
            for k, v in self.jobs.items()
        ]
