---
title: "PythonのProtocolとdependency-injectorでDIする"
emoji: "🐍"
type: "tech"
topics: ["python", "protocol", "di", "dependencyinjector"]
published: false
---

# 概要

Pythonには他の静的型付け言語のような明確な `interface` キーワードがありませんが、それに代わる `Protocol` という概念を最近知りました。

そこで、個人的に好んで使っている「ServiceクラスにRepositoryを注入する」というDI（依存性注入）パターンを、この `Protocol` を使ってPythonでどう実現できるか試してみることにしました。

本記事では、`dependency-injector` も組み合わせ、その具体的な実装方法をサンプルコードと共に備忘録として残します。

# Protocolでインタフェースを定義する

まずは、アプリケーションの疎結合性を高めるためのインタフェースを `Protocol` を使って定義します。

## Protocolとは

Pythonの `Protocol` は、Go言語の `interface` に非常によく似た概念です。

Goでは、ある型が特定の `interface` で定義されたメソッドをすべて実装していれば、その型は明示的に `implements` と書かなくても、その `interface` を満たすと見なされます。

Pythonの `Protocol` もこれと同じ考え方に基づいています。クラスが `Protocol` で定義されたメソッドや属性を（同じシグネチャで）持っていれば、そのクラスは `Protocol` を明示的に継承していなくても、その `Protocol` 型として扱うことができます。このような仕組みは、いわゆる構造的部分型（structural subtyping）と呼ばれるようです。

これにより、具象クラスと、それを利用するコードとの間に疎結合な関係を築くことができ、柔軟でテストしやすい設計が可能になります。

## Repositoryのインタフェースを定義する

今回はデータアクセス層のインタフェースとして、`UserRepositoryProtocol` を定義します。`put` メソッドは、型に応じて新規作成と更新をハンドリングする責務を持ちます。

```python
from typing import Protocol, Optional, Union
from dataclasses import dataclass

@dataclass
class User:
    id: int
    name: str
    email: str

@dataclass
class UserDetail:
    name: str
    email: str

class UserRepositoryProtocol(Protocol):
    def fetch(self, user_id: int) -> Optional[User]:
        ...

    def put(self, data: Union[User, UserDetail]) -> User:
        ...
```

# 主要なコンポーネントの実装

次に、定義した `Protocol` を利用して、アプリケーションの主要な部品の `Service` と `Repository` を実装します。

## Serviceクラス

`UserService` は、`create_user` と `update_user` の責務を持ちます。Repositoryの `put` メソッドに適切な型を渡すことで、新規作成と更新を依頼します。

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

        user.name = detail.name
        user.email = detail.email
        return self._user_repository.put(user)
```

## Repositoryクラス

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
            new_user = User(id=self._next_id, name=data.name, email=data.email)
            self._users[new_user.id] = new_user
            self._next_id += 1
            return new_user
        elif isinstance(data, User):
            self._users[data.id] = data
            return data
        else:
            raise TypeError("Unsupported type for put method")
```

# DIによるアプリケーションの組み立て

実装したコンポーネントを `dependency-injector` を使って結合し、アプリケーションとして実行できるようにします。

## DIコンテナの定義

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

# テスト容易性の確認

`Protocol` を使うことで、テストが非常に書きやすくなります。`Service` のテストをする際に、本物の `Repository` の代わりにモックオブジェクトを注入できるためです。

## Protocolを使ったユニットテスト

`unittest.mock.Mock` を使って `UserRepositoryProtocol` の振る舞いを模倣し、`UserService` をテストします。

```python
import pytest
from unittest.mock import Mock

class TestUserService:
    def test_create_user(self):
        mock_repository = Mock(spec=UserRepositoryProtocol)
        detail = UserDetail(name="新規ユーザー", email="new@example.com")
        saved_user = User(id=1, name=detail.name, email=detail.email)
        mock_repository.put.return_value = saved_user

        user_service = UserService(mock_repository)
        result = user_service.create_user(detail)

        assert result == saved_user
        mock_repository.put.assert_called_once_with(detail)

    def test_update_user_success(self):
        mock_repository = Mock(spec=UserRepositoryProtocol)
        detail = UserDetail(name="新ユーザー", email="new@example.com")
        existing_user = User(id=1, name="旧ユーザー", email="old@example.com")
        mock_repository.fetch.return_value = existing_user

        updated_user = User(id=1, name=detail.name, email=detail.email)
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

# まとめ

Python の Protocol と `dependency-injector` を使った DI パターンを試してみました。

- **型安全性とテスタビリティの向上**: Protocolにより、インタフェースが明確になり、安全なモックが可能になる。
- **実装の切り替えが容易になる柔軟性**: `dependency-injector` を使うことで、設定ファイルなどに応じて使用する実装を簡単に切り替えられる。
- **コードの簡潔化**: 自作のDIコンテナと比べて、`dependency-injector` はより宣言的でコードがシンプルになる。

Protocol と DI ライブラリを組み合わせることで、Python でも堅牢で保守性の高いアプリケーションを効率的に構築できそうです。
