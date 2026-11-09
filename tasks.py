from invoke import task
from invoke.context import Context


@task
def c(c: Context):
    c.run("ruff check . --fix")


@task
def f(c: Context):
    c.run("ruff format .")


@task
def t(c: Context):
    c.run("ty check .")


@task
def api(c: Context):
    c.run("uvicorn app.api.server:app --reload")
