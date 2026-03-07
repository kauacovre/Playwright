jobs = {}


def update_job(job_id, **kwargs):
    jobs[job_id].update(kwargs)