---
title: "Dependency Injection in Python with Protocol and dependency-injector"
emoji: "🐍"
type: "tech"
topics: ["python", "dependency-injection", "testing", "typing"]
---

## Introduction

I like keeping data access behind a repository and passing that repository into a service. When I tried this in Python, I found that `typing.Protocol` could describe the interface without requiring every implementation to inherit from a shared base class.

In this article, I'll combine a `Protocol` with `dependency-injector`, build a small in-memory example, and test the service with both a mock and a handwritten repository fixture.

This is an English adaptation of my [Japanese article on Zenn](https://zenn.dev/ara_ta3/articles/python-protocol-getting-started). The [original example code](https://gist.github.com/ara-ta3/e668cd1d90daefe52b95de36c7e29485) is also available.

The examples below use Python 3.10 or later.

## Protocol and dependency injection have different jobs

A `Protocol` describes the methods and attributes a type needs to provide. A compatible class does not need to explicitly inherit from it. This is called **structural subtyping**; it reminds me of interfaces in Go.

Type checkers can check whether an implementation matches that contract. Python does not enforce type annotations at runtime, and a `Protocol` does not automatically create or inject dependencies.

Constructor injection passes the repository into the service. The `dependency-injector` container assembles those objects using the providers we configure explicitly.

The flow is:

```text
Container creates repository
    -> passes repository into UserService
        -> service calls fetch() and put()
```

## Define the repository interface

Create `main.py` and start with the data classes and protocol:

```python
from dataclasses import dataclass
from typing import Protocol


@dataclass
class UserDetail:
    name: str
    email: str


@dataclass
class User:
    id: int
    detail: UserDetail


class UserRepositoryProtocol(Protocol):
    def fetch(self, user_id: int) -> User | None:
        ...

    def put(self, data: User | UserDetail) -> User:
        ...
```

In this example, `put()` creates a user when it receives `UserDetail`, and saves an existing user when it receives `User`. This keeps the same small interface as the original experiment.

## Implement the service

Append this class to `main.py`:

```python
class UserService:
    def __init__(self, user_repository: UserRepositoryProtocol):
        self._user_repository = user_repository

    def create_user(self, detail: UserDetail) -> User:
        return self._user_repository.put(detail)

    def update_user(self, user_id: int, detail: UserDetail) -> User | None:
        user = self._user_repository.fetch(user_id)
        if user is None:
            return None

        user.detail.name = detail.name
        user.detail.email = detail.email
        return self._user_repository.put(user)
```

The service only needs `fetch()` and `put()`. It does not need to know whether the repository uses memory, a database, or a test fixture.

## Implement an in-memory repository

Append the following implementation:

```python
class UserRepositoryOnMemory:
    def __init__(self):
        self._users: dict[int, User] = {}
        self._next_id = 1

    def fetch(self, user_id: int) -> User | None:
        return self._users.get(user_id)

    def put(self, data: User | UserDetail) -> User:
        if isinstance(data, UserDetail):
            user = User(id=self._next_id, detail=data)
            self._users[user.id] = user
            self._next_id += 1
            return user
        if isinstance(data, User):
            self._users[data.id] = data
            return data
        raise TypeError("Unsupported type for put method")
```

There is no `UserRepositoryProtocol` base class here. The method signatures satisfy the protocol structurally.

This implementation stores mutable objects directly. It is enough for the experiment, but it does not model database transactions or isolation.

## Assemble the application with dependency-injector

Install the packages in a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install dependency-injector pytest
```

Append the container and entry point to `main.py`:

```python
from dependency_injector import containers, providers


class Container(containers.DeclarativeContainer):
    user_repository = providers.Singleton(UserRepositoryOnMemory)
    user_service = providers.Factory(
        UserService,
        user_repository=user_repository,
    )


def main():
    container = Container()
    user_service = container.user_service()

    created_user = user_service.create_user(
        UserDetail(name="Alex", email="alex@example.com")
    )
    print(f"Created user: {created_user}")

    updated_user = user_service.update_user(
        created_user.id,
        UserDetail(name="Alex Smith", email="alex.smith@example.com"),
    )
    print(f"Updated user: {updated_user}")


if __name__ == "__main__":
    main()
```

`Singleton` reuses the repository within this container, so the in-memory data survives between service calls. `Factory` creates a new service when requested, passing in that repository.

The container explicitly supplies `user_repository`. It does not look up the implementation from the protocol annotation.

Run the application:

```bash
python main.py
```

Expected output:

```text
Created user: User(id=1, detail=UserDetail(name='Alex', email='alex@example.com'))
Updated user: User(id=1, detail=UserDetail(name='Alex Smith', email='alex.smith@example.com'))
```

## Test the service with a mock

Create `test_main.py`. For these unit tests, constructor injection is enough; we can instantiate the service directly.

```python
from unittest.mock import Mock

from main import User, UserDetail, UserRepositoryProtocol, UserService


def test_create_user():
    repository = Mock(spec=UserRepositoryProtocol)
    detail = UserDetail(name="New user", email="new@example.com")
    saved_user = User(id=1, detail=detail)
    repository.put.return_value = saved_user

    service = UserService(repository)
    actual = service.create_user(detail)

    assert actual == saved_user
    repository.put.assert_called_once_with(detail)


def test_update_user():
    repository = Mock(spec=UserRepositoryProtocol)
    existing_user = User(
        id=1,
        detail=UserDetail(name="Old name", email="old@example.com"),
    )
    repository.fetch.return_value = existing_user
    detail = UserDetail(name="New name", email="new@example.com")
    saved_user = User(id=1, detail=detail)
    repository.put.return_value = saved_user

    service = UserService(repository)
    actual = service.update_user(1, detail)

    assert actual == saved_user
    repository.fetch.assert_called_once_with(1)
    repository.put.assert_called_once_with(saved_user)


def test_update_user_not_found():
    repository = Mock(spec=UserRepositoryProtocol)
    repository.fetch.return_value = None

    service = UserService(repository)
    actual = service.update_user(
        99, UserDetail(name="Someone", email="someone@example.com")
    )

    assert actual is None
    repository.fetch.assert_called_once_with(99)
    repository.put.assert_not_called()
```

`Mock(spec=UserRepositoryProtocol)` restricts the mock's available attributes to the protocol's interface. It does not check argument types or provide runtime enforcement of the full protocol contract.

## Test with a handwritten repository fixture

Sometimes I prefer a small fixture that stores users and records calls. Create `test_fixture.py`:

```python
from main import User, UserDetail, UserService


class UserRepositoryFixture:
    def __init__(self):
        self._users: dict[int, User] = {}
        self._next_id = 1
        self.fetch_calls: list[int] = []
        self.put_calls: list[User | UserDetail] = []

    def set_user(self, user: User) -> None:
        self._users[user.id] = user
        self._next_id = max(self._next_id, user.id + 1)

    def fetch(self, user_id: int) -> User | None:
        self.fetch_calls.append(user_id)
        return self._users.get(user_id)

    def put(self, data: User | UserDetail) -> User:
        self.put_calls.append(data)
        if isinstance(data, UserDetail):
            user = User(id=self._next_id, detail=data)
            self._users[user.id] = user
            self._next_id += 1
            return user
        if isinstance(data, User):
            self._users[data.id] = data
            return data
        raise TypeError("Unsupported type for put method")


def test_create_user_with_fixture():
    repository = UserRepositoryFixture()
    detail = UserDetail(name="New user", email="new@example.com")

    actual = UserService(repository).create_user(detail)

    assert actual == User(id=1, detail=detail)
    assert repository.put_calls == [detail]


def test_update_user_with_fixture():
    repository = UserRepositoryFixture()
    repository.set_user(
        User(id=1, detail=UserDetail(name="Old name", email="old@example.com"))
    )
    detail = UserDetail(name="New name", email="new@example.com")

    actual = UserService(repository).update_user(1, detail)

    assert actual == User(id=1, detail=detail)
    assert repository.fetch_calls == [1]
    assert repository.put_calls == [User(id=1, detail=detail)]


def test_update_missing_user_with_fixture():
    repository = UserRepositoryFixture()

    actual = UserService(repository).update_user(
        99, UserDetail(name="Someone", email="someone@example.com")
    )

    assert actual is None
    assert repository.fetch_calls == [99]
    assert repository.put_calls == []
```

Run both test files:

```bash
python -m pytest -q test_main.py test_fixture.py
```

There are six tests: creation, update, and missing-user handling, each checked with a mock and a fixture.

The service accepts the fixture without any special registration. If I need to test application assembly through the container instead, `dependency-injector` also supports [overriding providers](https://python-dependency-injector.ets-labs.org/providers/overriding.html).

## Summary

`Protocol` gives the service a structural interface to depend on. Constructor injection lets us pass in an implementation, and `dependency-injector` centralizes how the application creates and connects those implementations.

I found this combination useful for keeping the service independent of its data source and testing it with small substitutes. For a small program, manually passing the repository is also enough; a container becomes useful when there are more objects to assemble.

## References

- [Python documentation: Protocol](https://docs.python.org/3/library/typing.html#typing.Protocol)
- [Dependency Injector: Dependency injection and inversion of control in Python](https://python-dependency-injector.ets-labs.org/introduction/di_in_python.html)
- [Dependency Injector: Provider overriding](https://python-dependency-injector.ets-labs.org/providers/overriding.html)
