---
title: "PythonのProtocolとdependency-injectorでDIする"
emoji: "🐍"
type: "tech"
topics: ["python", "protocol", "di", "dependencyinjector"]
published: true
---

# 概要

Python には他の静的型付け言語のような明確な `interface` キーワードがありませんが、それに代わる `Protocol` という概念を最近知りました。
そこで、個人的に好んで使っている「Service クラスに Repository を注入する」という DI（依存性注入）パターンを、この `Protocol` を使って Python でどう実現できるか試してみることにしました。
この記事では、`dependency-injector` も組み合わせ、その具体的な実装方法をサンプルコードと共に備忘録として残します。

今回使ったコードは以下に置いてあります。

https://gist.github.com/ara-ta3/e668cd1d90daefe52b95de36c7e29485

# Protocol でインタフェースを定義する

まずはインタフェースを `Protocol` を使って定義します。

## Protocol とは

Python の `Protocol` は、Go 言語の `interface` に非常によく似た概念です。
Go では、ある型が特定の `interface` で定義されたメソッドをすべて実装していれば、その型は明示的に `implements` と書かなくても、その `interface` を満たすと見なされます。
Python の `Protocol` もこれと同じ考え方に基づいています。クラスが `Protocol` で定義されたメソッドや属性を（同じシグネチャで）持っていれば、そのクラスは `Protocol` を明示的に継承していなくても、その `Protocol` 型として扱うことができます。  
このような仕組みは、いわゆる構造的部分型（structural subtyping）と呼ばれるようです。
これにより、具象クラスと、それを利用するコードとの間に疎結合な関係を築くことができ、柔軟でテストしやすい設計が可能になります。

## Repository のインタフェースを定義する

今回はデータアクセス層のインタフェースとして、`UserRepositoryProtocol` を定義します。`put` メソッドは、型に応じて新規作成と更新をハンドリングする責務を持ちます。

```python
from typing import Protocol, Optional, Union
from dataclasses import dataclass

@dataclass
class UserDetail:
    name: str
    email: str


@dataclass
class User:
    id: int
    detail: UserDetail

class UserRepositoryProtocol(Protocol):
    def fetch(self, user_id: int) -> Optional[User]:
        ...

    def put(self, data: Union[User, UserDetail]) -> User:
        ...
```

# 主要なコンポーネントの実装

次に、定義した `Protocol` を利用して、アプリケーションの主要な部品の `Service` と `Repository` を実装します。

## Service クラス

`UserService` は、`create_user` と `update_user` の責務を持ちます。Repository の `put` メソッドに適切な型を渡すことで、新規作成と更新を依頼します。

```python
class UserService:
    def __init__(self, user_repository: UserRepositoryProtocol):
        self._user_repository = user_repository

    def create_user(self, detail: UserDetail) -> User:
        return self._user_repository.put(detail)

    def update_user(self, user_id: int, detail: UserDetail) -> Optional[User]:
        user = self._user_repository.fetch(user_id)
        if not user:
            return None

        user.detail.name = detail.name
        user.detail.email = detail.email
        return self._user_repository.put(user)
```

## Repository クラス

`put` メソッドは、渡されたオブジェクトの型を `isinstance` で判定し、処理を分岐します。

```python
class UserRepositoryOnMemory:
    def __init__(self):
        self._users: dict[int, User] = {}
        self._next_id = 1

    def fetch(self, user_id: int) -> Optional[User]:
        return self._users.get(user_id)

    def put(self, data: Union[User, UserDetail]) -> User:
        if isinstance(data, UserDetail):
            new_user = User(id=self._next_id, detail=data)
            self._users[new_user.id] = new_user
            self._next_id += 1
            return new_user
        elif isinstance(data, User):
            self._users[data.id] = data
            return data
        else:
            raise TypeError("Unsupported type for put method")
```

# DI によるアプリケーションの組み立て

実装したコンポーネントを `dependency-injector` を使って結合し、アプリケーションとして実行できるようにします。

## DI コンテナの定義

`dependency-injector` を使って、どのインタフェース（`Protocol`）にどの具象クラスを注入するかを定義します。

`pip install dependency-injector` でインストールできます。

```python
from dependency_injector import containers, providers

class Container(containers.DeclarativeContainer):
    config = providers.Configuration()

    user_repository = providers.Singleton(
        UserRepositoryOnMemory
    )

    user_service = providers.Factory(
        UserService,
        user_repository=user_repository,
    )
```

## アプリケーションの実行

コンテナから `UserService` のインスタンスを取得して、ビジネスロジックを実行します。

```python
def main():
    container = Container()
    user_service = container.user_service()

    created_user = user_service.create_user(UserDetail(name="田中太郎", email="tanaka@example.com"))
    print(f"作成されたユーザー: {created_user}")

    updated_user = user_service.update_user(
        created_user.id, UserDetail(name="田中次郎", email="jiro@example.com")
    )
    print(f"更新されたユーザー: {updated_user}")
```

## 実行結果

`uv` を使って依存関係のインストールとスクリプトの実行をします。

https://github.com/astral-sh/uv

```bash
# 仮想環境の作成と有効化
uv venv
source .venv/bin/activate

# 依存パッケージのインストール
uv pip install pytest dependency_injector

# main.pyの実行
uv run python main.py
```

実行すると、ユーザー作成、更新が成功していることがわかります。

```text
作成されたユーザー: User(id=1, detail=UserDetail(name='田中太郎', email='tanaka@example.com'))
更新されたユーザー: User(id=1, detail=UserDetail(name='田中次郎', email='jiro@example.com'))
```

アプリケーションの基本的な動作を確認したら、次にテストコードも書いてみましょう。

# Protocol とテスト

`Protocol` を使うことで、テストが非常に書きやすくなります。  
`Service` のテストをする際に、本物の `Repository` の代わりにモックオブジェクトを注入できるためです。

## pytest の mock を使ったユニットテスト

`unittest.mock.Mock` を使って `UserRepositoryProtocol` の振る舞いを模倣し、`UserService` をテストします。

```python
import pytest
from unittest.mock import Mock

class TestUserService:
    def test_create_user(self):
        mock_repository = Mock(spec=UserRepositoryProtocol)
        detail = UserDetail(name="新規ユーザー", email="new@example.com")
        saved_user = User(id=1, detail=detail)
        mock_repository.put.return_value = saved_user

        user_service = UserService(mock_repository)
        result = user_service.create_user(detail)

        assert result == saved_user
        mock_repository.put.assert_called_once_with(detail)

    def test_update_user_success(self):
        mock_repository = Mock(spec=UserRepositoryProtocol)
        detail = UserDetail(name="新ユーザー", email="new@example.com")
        existing_user = User(id=1, detail=UserDetail(name="旧ユーザー", email="old@example.com"))
        mock_repository.fetch.return_value = existing_user

        updated_user = User(id=1, detail=detail)
        mock_repository.put.return_value = updated_user

        user_service = UserService(mock_repository)
        result = user_service.update_user(1, detail)

        assert result == updated_user
        mock_repository.fetch.assert_called_once_with(1)
        mock_repository.put.assert_called_once_with(updated_user)

    def test_update_user_not_found(self):
        mock_repository = Mock(spec=UserRepositoryProtocol)
        mock_repository.fetch.return_value = None

        user_service = UserService(mock_repository)
        result = user_service.update_user(99, UserDetail(name="誰か", email="darekasan@example.com"))

        assert result is None
        mock_repository.fetch.assert_called_once_with(99)
        mock_repository.put.assert_not_called()
```

実際にテストを実行してみましょう。

```bash
uv run pytest main.py
======================================================== test session starts ========================================================
platform darwin -- Python 3.13.3, pytest-8.4.1, pluggy-1.6.0
rootdir: /path/to/pythonprotocol
collected 3 items

main.py ...                                                                                                                   [100%]

========================================================= 3 passed in 0.04s =========================================================
```

テストがすべてパスすることを確認できました。

## 自前実装を使ったユニットテスト

mock を使わずに、テスト用の `Repository` を自前で実装する方法もあります。

```python
class UserRepositoryFixture:
    def __init__(self):
        self._predefined_users: dict[int, User] = {}
        self._next_id = 1
        self._fetch_calls: list[int] = []
        self._put_calls: list[Union[User, UserDetail]] = []

    def set_user(self, user: User):
        self._predefined_users[user.id] = user

    def fetch(self, user_id: int) -> Optional[User]:
        self._fetch_calls.append(user_id)
        return self._predefined_users.get(user_id)

    def put(self, data: Union[User, UserDetail]) -> User:
        self._put_calls.append(data)
        if isinstance(data, UserDetail):
            new_user = User(id=self._next_id, detail=data)
            self._predefined_users[new_user.id] = new_user
            self._next_id += 1
            return new_user
        elif isinstance(data, User):
            self._predefined_users[data.id] = data
            return data
        else:
            raise TypeError("Unsupported type for put method")

    def get_fetch_calls(self) -> list[int]:
        return self._fetch_calls.copy()

    def get_put_calls(self) -> list[Union[User, UserDetail]]:
        return self._put_calls.copy()

class TestUserServiceWithFixture:
    def test_create_user(self):
        test_repository = UserRepositoryFixture()
        detail = UserDetail(name="新規ユーザー", email="new@example.com")

        user_service = UserService(test_repository)
        result = user_service.create_user(detail)

        assert result.id == 1
        assert result.detail == detail
        assert test_repository.get_put_calls() == [detail]

    def test_update_user_success(self):
        test_repository = UserRepositoryFixture()
        detail = UserDetail(name="新ユーザー", email="new@example.com")
        existing_user = User(id=1, detail=UserDetail(name="旧ユーザー", email="old@example.com"))
        test_repository.set_user(existing_user)

        user_service = UserService(test_repository)
        result = user_service.update_user(1, detail)

        assert result is not None
        assert result.id == 1
        assert result.detail.name == "新ユーザー"
        assert result.detail.email == "new@example.com"
        assert test_repository.get_fetch_calls() == [1]
        assert len(test_repository.get_put_calls()) == 1

    def test_update_user_not_found(self):
        test_repository = UserRepositoryFixture()

        user_service = UserService(test_repository)
        result = user_service.update_user(99, UserDetail(name="誰か", email="darekasan@example.com"))

        assert result is None
        assert test_repository.get_fetch_calls() == [99]
        assert test_repository.get_put_calls() == []
```

実際にテストを実行してみましょう。

```bash
uv run pytest main2.py
======================================================== test session starts ========================================================
platform darwin -- Python 3.13.3, pytest-8.4.1, pluggy-1.6.0
rootdir: /path/to/pythonprotocol
collected 3 items

main2.py ...                                                                                                                  [100%]

========================================================= 3 passed in 0.05s =========================================================
```

テストがすべてパスすることを確認できました。

# まとめと感想

Python の Protocol と `dependency-injector` を使った DI パターンを試してみました。
インタフェースが Python にはなくて悲しいと思っていましたが、それ相当のものがあったので、便利に感じました。
Python をまた使う際には色々と試してみたいと思います。
