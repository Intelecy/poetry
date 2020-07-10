import pytest

from poetry.__version__ import __version__
from poetry.core.packages.package import Package
from poetry.factory import Factory
from poetry.repositories.installed_repository import InstalledRepository
from poetry.repositories.pool import Pool
from poetry.utils.env import EnvManager


@pytest.fixture()
def tester(command_tester_factory):
    return command_tester_factory("plugin add")


@pytest.fixture()
def installed():
    repository = InstalledRepository()

    repository.add_package(Package("poetry", __version__))

    return repository


def configure_sources_factory(repo):
    def _configure_sources(poetry, sources, config, io):
        pool = Pool()
        pool.add_repository(repo)
        poetry.set_pool(pool)

    return _configure_sources


def test_add_no_constraint(app, repo, tester, env, installed, mocker):
    mocker.patch.object(EnvManager, "get_system_env", return_value=env)
    mocker.patch.object(InstalledRepository, "load", return_value=installed)
    mocker.patch.object(
        Factory, "configure_sources", side_effect=configure_sources_factory(repo)
    )

    repo.add_package(Package("poetry-plugin", "0.1.0"))

    tester.execute("poetry-plugin")

    expected = """\
Using version ^0.1.0 for poetry-plugin
Updating dependencies
Resolving dependencies...

Writing lock file

Package operations: 1 install, 0 updates, 0 removals

  • Installing poetry-plugin (0.1.0)
"""

    assert tester.io.fetch_output() == expected

    update_command = app.find("update")
    assert update_command.poetry.file.parent == env.path
    assert update_command.poetry.locker.lock.parent == env.path
    assert update_command.poetry.locker.lock.exists()

    content = update_command.poetry.file.read()["tool"]["poetry"]
    assert "poetry-plugin" in content["dependencies"]
    assert content["dependencies"]["poetry-plugin"] == "^0.1.0"


def test_add_with_constraint(app, repo, tester, env, installed, mocker):
    mocker.patch.object(EnvManager, "get_system_env", return_value=env)
    mocker.patch.object(InstalledRepository, "load", return_value=installed)
    mocker.patch.object(
        Factory, "configure_sources", side_effect=configure_sources_factory(repo)
    )

    repo.add_package(Package("poetry-plugin", "0.1.0"))
    repo.add_package(Package("poetry-plugin", "0.2.0"))

    tester.execute("poetry-plugin@^0.2.0")

    expected = """\
Updating dependencies
Resolving dependencies...

Writing lock file

Package operations: 1 install, 0 updates, 0 removals

  • Installing poetry-plugin (0.2.0)
"""

    assert tester.io.fetch_output() == expected

    update_command = app.find("update")
    assert update_command.poetry.file.parent == env.path
    assert update_command.poetry.locker.lock.parent == env.path

    content = update_command.poetry.file.read()["tool"]["poetry"]
    assert "poetry-plugin" in content["dependencies"]
    assert content["dependencies"]["poetry-plugin"] == "^0.2.0"


def test_add_with_git_constraint(app, repo, tester, env, installed, mocker):
    mocker.patch.object(EnvManager, "get_system_env", return_value=env)
    mocker.patch.object(InstalledRepository, "load", return_value=installed)
    mocker.patch.object(
        Factory, "configure_sources", side_effect=configure_sources_factory(repo)
    )

    repo.add_package(Package("pendulum", "2.0.5"))

    tester.execute("git+https://github.com/demo/poetry-plugin.git")

    expected = """\
Updating dependencies
Resolving dependencies...

Writing lock file

Package operations: 2 installs, 0 updates, 0 removals

  • Installing pendulum (2.0.5)
  • Installing poetry-plugin (0.1.2 9cf87a2)
"""

    assert tester.io.fetch_output() == expected

    update_command = app.find("update")
    assert update_command.poetry.file.parent == env.path
    assert update_command.poetry.locker.lock.parent == env.path

    content = update_command.poetry.file.read()["tool"]["poetry"]
    assert "poetry-plugin" in content["dependencies"]
    assert content["dependencies"]["poetry-plugin"] == {
        "git": "https://github.com/demo/poetry-plugin.git",
        "rev": "master",
    }


def test_add_with_git_constraint_with_extras(app, repo, tester, env, installed, mocker):
    mocker.patch.object(EnvManager, "get_system_env", return_value=env)
    mocker.patch.object(InstalledRepository, "load", return_value=installed)
    mocker.patch.object(
        Factory, "configure_sources", side_effect=configure_sources_factory(repo)
    )

    repo.add_package(Package("pendulum", "2.0.5"))
    repo.add_package(Package("tomlkit", "0.7.0"))

    tester.execute("git+https://github.com/demo/poetry-plugin.git[foo]")

    expected = """\
Updating dependencies
Resolving dependencies...

Writing lock file

Package operations: 3 installs, 0 updates, 0 removals

  • Installing pendulum (2.0.5)
  • Installing tomlkit (0.7.0)
  • Installing poetry-plugin (0.1.2 9cf87a2)
"""

    assert tester.io.fetch_output() == expected

    update_command = app.find("update")
    assert update_command.poetry.file.parent == env.path
    assert update_command.poetry.locker.lock.parent == env.path

    content = update_command.poetry.file.read()["tool"]["poetry"]
    assert "poetry-plugin" in content["dependencies"]
    assert content["dependencies"]["poetry-plugin"] == {
        "git": "https://github.com/demo/poetry-plugin.git",
        "rev": "master",
        "extras": ["foo"],
    }
